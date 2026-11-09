"""Foxglove buttons that start and stop whole stacks, bags, camera, stream and power.

Run on the Pi, outside the ROS packages so it survives every stack it controls:

    python3 tools/robot_control.py        (robot-control.service does this at boot)

Every managed command runs in its own process group; stopping signals the whole group
(SIGINT first: it closes the MCAP file and zeroes PWM, then SIGTERM, then SIGKILL).
Entries that share a group are mutually exclusive. Never passes dry_run:=false and never
touches /cmd_vel or GPIO: motors stay the safety node's business (AGENTS.md rule 1).

Services (all std_srvs/Trigger unless noted), request {} in Foxglove's Call Service panel:
    /stack/base  /stack/mapping  /stack/localisation  /stack/navigation  /stack/stop
    /camera/start  /camera/stop  /stream/start  /stream/audio  /stream/stop
    /bag/start  /bag/stop      parameters bag_label, bag_topics (Parameters panel)
    /stream/start              parameters stream_size, stream_fps (default 640x480 at 15 fps)
    /control/status
    /pi/shutdown  /pi/reboot   (SetBool, refused unless data: true)
Creates /marker without publishing on it, so the recorder subscribes before the first
Foxglove "push start" message.
Status, 1 Hz (the cockpit layout's indicators read these; a missing source gives a safe value):
    /robot/status/stack         String   base|mapping|localisation|navigation|none (stacks started here)
    /robot/status/video         String   camera|stream|audio|off
    /robot/status/bag           String   bag directory name, or off
    /robot/status/bag_s         Float32  seconds recording, 0 when off
    /robot/status/throttled     UInt32   raw `vcgencmd get_throttled`, 0 if unavailable
    /robot/status/undervolt     Bool     bit 0: under-voltage now
    /robot/status/throttling    Bool     bit 2: throttled now
    /robot/status/cpu_temp_c    Float32  thermal_zone0 / 1000, -1 if unreadable
    /robot/status/load1         Float32  1-minute load average
    /robot/status/disk_free_gb  Float32  free space under ~/bags
"""
from datetime import datetime
import os
import re
import shlex
import shutil
import signal
import subprocess
import threading
import time

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String, UInt32
from std_srvs.srv import SetBool, Trigger

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = 'source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash; '
BRIDGE = ("ros2 run foxglove_bridge foxglove_bridge --ros-args -p "
          "'topic_whitelist:=[\"^(?!/image_raw$)(?!/image_raw/(zstd|theora|compressedDepth)).*\"]'")
LAUNCH = 'ros2 launch delivery_bot_bringup '
# name -> (command, group); one running entry per group
PROCS = {
    'base': (LAUNCH + 'base.launch.py bridge:=false', 'stack'),
    'mapping': (LAUNCH + 'mapping.launch.py bridge:=false', 'stack'),
    'localisation': (LAUNCH + 'navigation.launch.py bridge:=false nav:=false', 'stack'),
    'navigation': (LAUNCH + 'navigation.launch.py bridge:=false nav:=true', 'stack'),
    'camera': (LAUNCH + 'camera.launch.py', 'video0'),
    'stream': (f'python3 {HERE}/streams/audio_stream.py --video', 'video0'),
    'audio': (f'python3 {HERE}/streams/audio_stream.py', 'video0'),
    'bridge': (BRIDGE, 'bridge'),
}
def exe_re(names: str) -> str:
    """Match a process by its executable path, not any command line that mentions the name.

    An unanchored pattern also matches `ssh ... pgrep -f ekf_node` and kills the shell.
    """
    return rf'^(/usr/bin/python3 )?\S*/({names})( |$)'


STACK_NAMES = ('rplidar_composition|rf2o_laser_odometry_node|ekf_node|imu_node|'
               r'odom_covariance_relay|robot_state_publisher|\w*slam_toolbox_node|run_save')
STACK_STRAYS = exe_re(STACK_NAMES)
CAMERA_RE = exe_re('usb_cam_node_exe')
AUDIO_RE = r'^(/usr/bin/)?python3 \S*/audio_stream\.py'
# processes started by hand (or start_streams.sh) that hold what a group needs
FOREIGN = {'stack': STACK_STRAYS, 'video0': f'{CAMERA_RE}|{AUDIO_RE}'}
HELD_BY = {'camera': CAMERA_RE, 'stream': AUDIO_RE, 'audio': AUDIO_RE}
POWER = {'shutdown': 'poweroff', 'reboot': 'reboot'}
DEFAULT_TOPICS = ['/scan', '/odom_rf2o', '/odom_rf2o_cov', '/odometry/filtered',
                  '/imu/data', '/tf', '/tf_static', '/marker', '/pose']
MIN_FREE_GB = 1.0
STACK_WAIT_S = 25
STREAM_SIZE, STREAM_FPS = '640x480', 15     # 2026-11-02: the 1280x720 30 fps copy lagged on the Pi


def pids_matching(pattern: str, own_pgids: set) -> list:
    """Pids whose command line matches, minus ours and any in a runner-owned group."""
    out = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True).stdout
    pids = []
    for pid in map(int, out.split()):
        try:
            if pid != os.getpid() and os.getpgid(pid) not in own_pgids:
                pids.append(pid)
        except ProcessLookupError:
            pass
    return pids


def stream_args(size: str, fps: int) -> str:
    """` --size WxH --fps N` for audio_stream.py; both reach a shell, so reject anything else."""
    if not re.fullmatch(r'\d{3,4}x\d{3,4}', str(size)) or not 1 <= int(fps) <= 60:
        raise ValueError(f'stream_size must be WxH and stream_fps 1-60, got {size!r} {fps!r}')
    return f' --size {size} --fps {int(fps)}'


def bag_name(label: str, now: datetime) -> str:
    """~/bags/<YYYY-MM-DD_HHMMSS>[_<label>]; the label is cut down to word characters."""
    label = re.sub(r'\W+', '_', label).strip('_')
    return os.path.expanduser(f"~/bags/{now:%Y-%m-%d_%H%M%S}" + (f'_{label}' if label else ''))


def parse_throttled(text: str) -> int:
    """`throttled=0x50005` -> 0x50005; anything unparsable -> 0 (no flags)."""
    match = re.search(r'throttled=(0x[0-9a-fA-F]+)', text or '')
    return int(match.group(1), 16) if match else 0


def throttle_flags(raw: int) -> tuple:
    """(under-voltage now, throttled now) = bits 0 and 2 of get_throttled."""
    return bool(raw & 1), bool(raw & 4)


def _running(procs: dict, name: str) -> bool:
    return name in procs and procs[name][0].poll() is None


def stack_state(procs: dict) -> str:
    return next((n for n in ('base', 'mapping', 'localisation', 'navigation') if _running(procs, n)), 'none')


def video_state(procs: dict) -> str:
    return next((n for n in ('camera', 'stream', 'audio') if _running(procs, n)), 'off')


def read_throttled() -> int:
    try:
        out = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True, text=True,
                             timeout=1).stdout
    except (OSError, subprocess.SubprocessError):
        return 0
    return parse_throttled(out)


def read_cpu_temp_c() -> float:
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            return int(f.read()) / 1000
    except (OSError, ValueError):
        return -1.0


def bag_dir_free_gb() -> float:
    bags = os.path.expanduser('~/bags')     # same disk as ~ until the first bag
    try:
        return shutil.disk_usage(bags if os.path.isdir(bags) else os.path.expanduser('~')).free / 1e9
    except OSError:
        return -1.0


class RobotControl(Node):
    def __init__(self) -> None:
        super().__init__('robot_control')
        self.declare_parameter('bag_label', '')
        self.declare_parameter('bag_topics', DEFAULT_TOPICS)
        self.declare_parameter('stream_size', STREAM_SIZE)
        self.declare_parameter('stream_fps', STREAM_FPS)
        self.procs = {}          # name -> (Popen, start time)
        self.bag_path = None
        self.lock = threading.RLock()
        self.create_publisher(String, '/marker', 10)
        kinds = {'stack': String, 'video': String, 'bag': String, 'bag_s': Float32,
                 'throttled': UInt32, 'undervolt': Bool, 'throttling': Bool,
                 'cpu_temp_c': Float32, 'load1': Float32, 'disk_free_gb': Float32}
        self.status_pubs = {k: self.create_publisher(t, f'/robot/status/{k}', 1)
                            for k, t in kinds.items()}
        self.create_timer(1.0, self.publish_status)
        cb = ReentrantCallbackGroup()
        routes = {'/stack/base': lambda: self.stack('base'),
                  '/stack/mapping': lambda: self.stack('mapping'),
                  '/stack/localisation': lambda: self.stack('localisation'),
                  '/stack/navigation': lambda: self.stack('navigation'),
                  '/stack/stop': self.stack_stop,
                  '/camera/start': lambda: self.start('camera'),
                  '/camera/stop': lambda: self.stop('camera'),
                  '/stream/start': lambda: self.start('stream'),
                  '/stream/audio': lambda: self.start('audio'),
                  '/stream/stop': self.stop_stream,
                  '/bag/start': self.bag_start, '/bag/stop': self.bag_stop,
                  '/control/status': self.status}
        for name, fn in routes.items():
            self.create_service(Trigger, name, self.wrap(fn), callback_group=cb)
        for name, verb in POWER.items():
            self.create_service(SetBool, f'/pi/{name}', self.power(verb), callback_group=cb)
        with self.lock:
            if not pids_matching('[f]oxglove_bridge', set()):
                self.spawn('bridge')

    def publish_status(self) -> None:
        try:
            procs = dict(self.procs)    # no lock: start/stop hold it for seconds
            throttled = read_throttled()
            under, throttling = throttle_flags(throttled)
            bag = _running(procs, 'bag') and self.bag_path
            values = {'stack': stack_state(procs), 'video': video_state(procs),
                      'bag': os.path.basename(bag) if bag else 'off',
                      'bag_s': time.time() - procs['bag'][1] if bag else 0.0,
                      'throttled': throttled, 'undervolt': under,
                      'throttling': throttling, 'cpu_temp_c': read_cpu_temp_c(),
                      'load1': os.getloadavg()[0], 'disk_free_gb': bag_dir_free_gb()}
            for key, value in values.items():
                self.status_pubs[key].publish(self.status_pubs[key].msg_type(data=value))
        except Exception as err:    # a status glitch must never take the buttons down
            self.get_logger().warn(f'status publish failed: {err}', throttle_duration_sec=30)

    def wrap(self, fn):
        def handler(_req, res):
            with self.lock:
                res.success, res.message = fn()
            return res
        return handler

    # processes ---------------------------------------------------------------------
    def own_pgids(self) -> set:
        return {p.pid for p, _ in self.procs.values() if p.poll() is None}

    def command(self, name: str) -> str:
        cmd = PROCS[name][0]
        if name == 'stream':
            cmd += stream_args(self.get_parameter('stream_size').value,
                               self.get_parameter('stream_fps').value)
        return cmd

    def spawn(self, name: str) -> None:
        log = open(f'/tmp/{name}.log', 'ab')
        proc = subprocess.Popen(['bash', '-lc', SRC + self.command(name)], start_new_session=True,
                                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        self.procs[name] = (proc, time.time())

    def running(self, name: str) -> bool:
        return name in self.procs and self.procs[name][0].poll() is None

    def kill_group(self, pid: int) -> None:
        """SIGINT, 10 s, SIGTERM, 5 s, SIGKILL on the whole group of a process we started."""
        for sig, wait in ((signal.SIGINT, 10), (signal.SIGTERM, 5), (signal.SIGKILL, 2)):
            try:
                os.killpg(pid, sig)
            except ProcessLookupError:
                return
            end = time.time() + wait
            while time.time() < end:
                for proc, _ in self.procs.values():
                    proc.poll()     # reap the group leader so killpg(0) can fail
                try:
                    os.killpg(pid, 0)
                except (ProcessLookupError, PermissionError):   # EPERM: only zombies left (macOS)
                    return
                time.sleep(0.2)

    def kill_strays(self, pattern: str) -> list:
        """SIGINT then SIGKILL on matching processes this runner did not start."""
        pids = pids_matching(pattern, self.own_pgids())
        for sig in (signal.SIGINT, signal.SIGKILL):
            for pid in pids:
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            if sig == signal.SIGINT:
                time.sleep(3)
        return pids

    def start(self, name: str):
        try:
            self.command(name)
        except ValueError as err:
            return False, str(err)
        group = PROCS[name][1]
        if self.running(name):
            return True, f'{name} already running (pid {self.procs[name][0].pid})'
        for other, (_, g) in PROCS.items():
            if g == group and self.running(other):
                self.kill_group(self.procs[other][0].pid)
        killed = self.kill_strays(FOREIGN[group]) if group in FOREIGN else []
        self.spawn(name)
        time.sleep(4)
        ok = self.running(name)
        return ok, (f'{name} running, log /tmp/{name}.log' if ok else f'{name} exited, see /tmp/{name}.log') \
            + (f'; killed strays {killed}' if killed else '')

    def stop(self, name: str):
        if self.running(name):
            self.kill_group(self.procs[name][0].pid)
        if name in HELD_BY:     # also the copy start_streams.sh started by hand
            self.kill_strays(HELD_BY[name])
        return True, f'{name} stopped'

    def stop_stream(self):
        self.stop('audio')      # a managed audio-only stream is not a stray of 'stream'
        return self.stop('stream')

    def stack(self, name: str):
        _, cleared = self.stack_stop()
        self.spawn(name)
        start = time.time()
        while True:     # the launch takes 10 s or more on the Pi before its nodes exist
            counts = {p: len(pids_matching(exe_re(p), set()))
                      for p in ('rplidar_composition', 'ekf_node')}
            ok = self.running(name) and all(counts.values())
            if ok or time.time() - start > STACK_WAIT_S:
                break
            time.sleep(1)
        return ok, (f"{'pass' if ok else 'FAIL'} after {time.time() - start:.0f} s: {name} "
                    f'{counts}, log /tmp/{name}.log; {cleared}')

    def stack_stop(self):
        for name, (_, group) in PROCS.items():
            if group == 'stack':
                self.stop(name)
        killed = self.kill_strays(STACK_STRAYS)
        return True, f'stack stopped; killed strays {killed}'

    # bag ---------------------------------------------------------------------------
    def bag_start(self):
        if self.running('bag'):
            return False, f'already recording {self.bag_path}'
        free = shutil.disk_usage(os.path.expanduser('~')).free / 1e9
        if free < MIN_FREE_GB:
            return False, f'only {free:.2f} GB free, need {MIN_FREE_GB}'
        self.bag_path = bag_name(self.get_parameter('bag_label').value, datetime.now())
        os.makedirs(os.path.dirname(self.bag_path), exist_ok=True)
        topics = list(self.get_parameter('bag_topics').value)
        cmd = shlex.join(['ros2', 'bag', 'record', '-s', 'mcap', '-o', self.bag_path] + topics)
        mark = os.path.getsize('/tmp/bag.log') if os.path.exists('/tmp/bag.log') else 0
        log = open('/tmp/bag.log', 'ab')
        self.procs['bag'] = (subprocess.Popen(
            ['bash', '-lc', SRC + cmd], start_new_session=True, stdout=log,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL), time.time())
        end = time.time() + 20      # markers sent before "Recording..." would be lost
        while self.running('bag') and time.time() < end:
            with open('/tmp/bag.log', 'rb') as f:
                f.seek(mark)
                if b'Recording...' in f.read():
                    return True, self.bag_path
            time.sleep(0.5)
        return False, 'recorder not ready, see /tmp/bag.log'

    def bag_stop(self):
        if not self.running('bag'):
            return False, 'no bag recording'
        self.kill_group(self.procs['bag'][0].pid)
        info = subprocess.run(['bash', '-lc', SRC + f'ros2 bag info {shlex.quote(self.bag_path)}'],
                              capture_output=True, text=True).stdout
        keep = [' '.join(line.split()) for line in info.splitlines()
                if re.match(r'\s*(Duration|Messages):', line)]
        return True, f"{self.bag_path} {' '.join(keep)}"

    # status and power --------------------------------------------------------------
    def status(self):
        now = time.time()
        up = [f'{n} pid {p.pid} {int(now - t)}s' for n, (p, t) in self.procs.items() if p.poll() is None]
        strays = pids_matching(STACK_STRAYS, self.own_pgids())
        free = shutil.disk_usage(os.path.expanduser('~')).free / 1e9
        return True, (f"running: {', '.join(up) or 'nothing'}; bag: {self.bag_path or 'none'}; "
                      f"free {free:.1f} GB; stray stack pids: {strays or 'none'}")

    def power(self, verb: str):
        def handler(req, res):
            if not req.data:
                res.success, res.message = False, 'refused: send {data: true}'
                return res
            cmd = ['/usr/bin/systemctl', verb]
            check = subprocess.run(['sudo', '-n', '-l'] + cmd, capture_output=True, text=True)
            if check.returncode:
                res.success, res.message = False, (check.stderr or check.stdout).strip() or 'sudo -n refused'
                return res
            with self.lock:
                self.stop('bag')
                self.stack_stop()
                for name in PROCS:
                    if name != 'bridge':
                        self.stop(name)
                subprocess.Popen(['sh', '-c', 'sleep 2; sudo -n ' + ' '.join(cmd)],
                                 start_new_session=True)
            res.success, res.message = True, f'{verb} in 2 s'
            return res
        return handler


def main() -> None:
    rclpy.init()
    node = RobotControl()
    ex = MultiThreadedExecutor(num_threads=4)
    ex.add_node(node)
    try:
        ex.spin()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

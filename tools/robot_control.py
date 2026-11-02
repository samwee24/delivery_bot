"""Foxglove buttons that start and stop whole stacks, bags, camera, stream and power.

Run on the Pi, outside the ROS packages so it survives every stack it controls:

    python3 tools/robot_control.py        (robot-control.service does this at boot)

Every managed command runs in its own process group; stopping signals the whole group
(SIGINT first: it closes the MCAP file and zeroes PWM, then SIGTERM, then SIGKILL).
Entries that share a group are mutually exclusive. Never passes dry_run:=false and never
touches /cmd_vel or GPIO: motors stay the safety node's business (AGENTS.md rule 1).

Services (all std_srvs/Trigger unless noted), request {} in Foxglove's Call Service panel:
    /stack/base  /stack/mapping  /stack/localisation  /stack/stop
    /camera/start  /camera/stop  /stream/start  /stream/stop
    /bag/start  /bag/stop      parameters bag_label, bag_topics (Parameters panel)
    /control/status
    /pi/shutdown  /pi/reboot   (SetBool, refused unless data: true)
Publishes nothing on /marker; it only creates the topic so the recorder subscribes before
the first Foxglove "push start" message.
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
from std_msgs.msg import String
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
    'localisation': (LAUNCH + 'navigation.launch.py bridge:=false', 'stack'),
    'camera': (LAUNCH + 'camera.launch.py', 'video0'),
    'stream': (f'python3 {HERE}/streams/audio_stream.py --video', 'video0'),
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
HELD_BY = {'camera': CAMERA_RE, 'stream': AUDIO_RE}
POWER = {'shutdown': 'poweroff', 'reboot': 'reboot'}
DEFAULT_TOPICS = ['/scan', '/odom_rf2o', '/odom_rf2o_cov', '/odometry/filtered',
                  '/imu/data', '/tf', '/tf_static', '/marker', '/pose']
MIN_FREE_GB = 1.0
STACK_WAIT_S = 25


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


def bag_name(label: str, now: datetime) -> str:
    """~/bags/<YYYY-MM-DD_HHMMSS>[_<label>]; the label is cut down to word characters."""
    label = re.sub(r'\W+', '_', label).strip('_')
    return os.path.expanduser(f"~/bags/{now:%Y-%m-%d_%H%M%S}" + (f'_{label}' if label else ''))


class RobotControl(Node):
    def __init__(self) -> None:
        super().__init__('robot_control')
        self.declare_parameter('bag_label', '')
        self.declare_parameter('bag_topics', DEFAULT_TOPICS)
        self.procs = {}          # name -> (Popen, start time)
        self.bag_path = None
        self.lock = threading.RLock()
        self.create_publisher(String, '/marker', 10)
        cb = ReentrantCallbackGroup()
        routes = {'/stack/base': lambda: self.stack('base'),
                  '/stack/mapping': lambda: self.stack('mapping'),
                  '/stack/localisation': lambda: self.stack('localisation'),
                  '/stack/stop': self.stack_stop,
                  '/camera/start': lambda: self.start('camera'),
                  '/camera/stop': lambda: self.stop('camera'),
                  '/stream/start': lambda: self.start('stream'),
                  '/stream/stop': lambda: self.stop('stream'),
                  '/bag/start': self.bag_start, '/bag/stop': self.bag_stop,
                  '/control/status': self.status}
        for name, fn in routes.items():
            self.create_service(Trigger, name, self.wrap(fn), callback_group=cb)
        for name, verb in POWER.items():
            self.create_service(SetBool, f'/pi/{name}', self.power(verb), callback_group=cb)
        with self.lock:
            if not pids_matching('[f]oxglove_bridge', set()):
                self.spawn('bridge')

    def wrap(self, fn):
        def handler(_req, res):
            with self.lock:
                res.success, res.message = fn()
            return res
        return handler

    # processes ---------------------------------------------------------------------
    def own_pgids(self) -> set:
        return {p.pid for p, _ in self.procs.values() if p.poll() is None}

    def spawn(self, name: str) -> None:
        log = open(f'/tmp/{name}.log', 'ab')
        proc = subprocess.Popen(['bash', '-lc', SRC + PROCS[name][0]], start_new_session=True,
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

    def stack(self, name: str):
        self.stack_stop()
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
                    f'{counts}, log /tmp/{name}.log')

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
        log = open('/tmp/bag.log', 'ab')
        self.procs['bag'] = (subprocess.Popen(
            ['bash', '-lc', SRC + cmd], start_new_session=True, stdout=log,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL), time.time())
        time.sleep(2)
        if not self.running('bag'):
            return False, 'recorder exited, see /tmp/bag.log'
        return True, self.bag_path

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

"""Tests for the pure parts of tools/robot_control.py: the stray-process patterns, the
PROCS table (rule 1) and the bag name. rclpy is stubbed when absent so this runs on a Mac."""
from datetime import datetime
import os
import re
import subprocess
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    import rclpy  # noqa: F401
except ImportError:
    for name, attrs in {
        'rclpy': {},
        'rclpy.callback_groups': {'ReentrantCallbackGroup': object},
        'rclpy.executors': {'MultiThreadedExecutor': object},
        'rclpy.node': {'Node': object},
        'std_msgs': {},
        'std_msgs.msg': {'String': object},
        'std_srvs': {},
        'std_srvs.srv': {'SetBool': object, 'Trigger': object},
    }.items():
        module = types.ModuleType(name)
        module.__dict__.update(attrs)
        sys.modules[name] = module

import robot_control as rc  # noqa: E402

REAL = [
    '/opt/ros/jazzy/lib/rplidar_ros/rplidar_composition --ros-args -r __node:=rplidar',
    '/opt/ros/jazzy/lib/robot_localization/ekf_node --ros-args --params-file x.yaml',
    '/usr/bin/python3 /home/robot/ros2_ws/install/delivery_bot_drivers/lib/'
    'delivery_bot_drivers/imu_node --ros-args',
    '/opt/ros/jazzy/lib/slam_toolbox/async_slam_toolbox_node --ros-args',
    '/home/robot/ros2_ws/install/delivery_bot_slam/lib/delivery_bot_slam/run_save',
]
# command lines that merely mention a stack name; matching these killed the SSH shell
IMPOSTORS = [
    "ssh robot@100.83.14.99 'pgrep -f ekf_node'",
    "bash -c 'source setup.bash; pgrep -f rplidar_composition'",
    'pgrep -f imu_node',
    'vim /home/robot/ekf_node.yaml',
    'tail -f /tmp/mapping.log ekf_node',
]


def test_stack_strays_match_real_executables():
    for line in REAL:
        assert re.search(rc.STACK_STRAYS, line), line


def test_stack_strays_ignore_commands_that_only_mention_a_name():
    for line in IMPOSTORS:
        assert not re.search(rc.STACK_STRAYS, line), line


def test_camera_and_audio_patterns():
    assert re.search(rc.CAMERA_RE, '/opt/ros/jazzy/lib/usb_cam/usb_cam_node_exe --ros-args')
    assert not re.search(rc.CAMERA_RE, 'pgrep -f usb_cam_node_exe')
    assert re.search(rc.AUDIO_RE, 'python3 /home/robot/x/tools/streams/audio_stream.py --video')
    assert not re.search(rc.AUDIO_RE, 'vim tools/streams/audio_stream.py')


def test_no_command_can_turn_off_dry_run():
    for name, (command, _group) in rc.PROCS.items():
        assert 'dry_run' not in command, name
        assert 'motor' not in command, name


def test_stack_entries_leave_the_bridge_to_the_runner():
    for name in ('base', 'mapping', 'localisation'):
        command, group = rc.PROCS[name]
        assert 'bridge:=false' in command, name
        assert group == 'stack', name


def test_every_held_by_and_foreign_group_exists():
    groups = {group for _command, group in rc.PROCS.values()}
    assert set(rc.FOREIGN) <= groups
    assert set(rc.HELD_BY) <= set(rc.PROCS)


def test_bag_name_cleans_the_label():
    now = datetime(2026, 11, 2, 12, 24, 5)
    stem = os.path.expanduser('~/bags/2026-11-02_122405')
    assert rc.bag_name('', now) == stem
    assert rc.bag_name('push 1/ test!', now) == stem + '_push_1_test'
    assert rc.bag_name('///', now) == stem


def test_pids_matching_skips_own_group_and_finds_others():
    proc = subprocess.Popen(['sleep', '31337'], start_new_session=True)
    try:
        assert proc.pid in rc.pids_matching(r'^sleep 31337$', set())
        assert proc.pid not in rc.pids_matching(r'^sleep 31337$', {os.getpgid(proc.pid)})
    finally:
        proc.kill()
        proc.wait()


def test_stream_args_accepts_a_size_and_rate():
    assert rc.stream_args('640x480', 15) == ' --size 640x480 --fps 15'
    assert rc.stream_args('1280x720', 30.0) == ' --size 1280x720 --fps 30'


def test_stream_args_rejects_anything_a_shell_could_run():
    for size, fps in [('640x480; reboot', 15), ('$(id)', 15), ('640', 15), ('640x480', 0),
                      ('640x480', 61)]:
        try:
            rc.stream_args(size, fps)
        except ValueError:
            continue
        raise AssertionError((size, fps))


def test_stream_defaults_are_a_native_camera_mode():
    assert rc.stream_args(rc.STREAM_SIZE, rc.STREAM_FPS) == ' --size 640x480 --fps 15'


def test_audio_only_stream_shares_the_camera_group_and_has_no_video_flag():
    command, group = rc.PROCS['audio']
    assert group == rc.PROCS['stream'][1] == rc.PROCS['camera'][1]
    assert 'audio_stream.py' in command and '--video' not in command
    assert re.search(rc.AUDIO_RE, 'python3 /home/robot/x/tools/streams/audio_stream.py')
    assert rc.HELD_BY['audio'] == rc.AUDIO_RE

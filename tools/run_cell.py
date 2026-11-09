#!/usr/bin/env python3
"""Run sheet for the driven experiments: one experiment cell, one run.

Usage: python3 tools/run_cell.py <exp> <cell> <run> [--dry]

Starts the cell's launch command, waits until odometry is publishing (40 s max), records
a rosbag2 MCAP to ~/bags/<date>_<exp>_<cell>_run<N>, waits for Enter, stops the bag and
the launch with SIGINT and prints one docs/test_log.md row (Result/Numbers left TODO).
--dry prints the plan only. Never starts a motor node, never sets dry_run, refuses to
overwrite a bag. Drive with tools/timed_move.py in a second shell while this waits.

Cells: E2 <config>_<cond> (config rf2o_imu|rf2o_only|imu_only|none, cond empty|people);
E3 <loc>_<cond> (loc slam|amcl, cond empty|people|wrongstart); E4 stepin; E1 demo.
"""
import argparse
import datetime
import os
import shlex
import signal
import subprocess
import sys
import time

LAUNCH = ['ros2', 'launch', 'delivery_bot_bringup', 'navigation.launch.py', 'nav:=true']
TOPICS = ['/scan', '/imu/data', '/odom_rf2o', '/odometry/filtered', '/tf', '/tf_static',
          '/cmd_vel', '/cmd_vel_smoothed', '/amcl_pose', '/pose', '/marker']
E2_CONFIGS = ('rf2o_imu', 'rf2o_only', 'imu_only', 'none')
CONDS = ('empty', 'people')
LOCS = ('slam', 'amcl')
WAIT_S = 40.0


def _share() -> str:
    from ament_index_python.packages import get_package_share_directory
    return get_package_share_directory('delivery_bot_bringup')


def cell_plan(exp: str, cell: str, share: str | None = None) -> dict:
    """Launch command, bag topics and the topic to wait for. Raises on an unknown cell."""
    wait = '/odometry/filtered'
    if exp == 'E2':
        config, _, cond = cell.rpartition('_')
        if config not in E2_CONFIGS or cond not in CONDS:
            raise ValueError(f'E2 cell must be <{"|".join(E2_CONFIGS)}>_<{"|".join(CONDS)}>')
        if config == 'none':
            extra, wait = ['ekf:=false'], '/tf'
        else:
            extra = ['ekf_params_file:=' + os.path.join(
                share or _share(), 'config', 'ekf_variants', config + '.yaml')]
        extra = ['localizer:=slam'] + extra
    elif exp == 'E3':
        loc, _, cond = cell.partition('_')
        if loc not in LOCS or cond not in CONDS + ('wrongstart',):
            raise ValueError('E3 cell must be <slam|amcl>_<empty|people|wrongstart>')
        extra = [f'localizer:={loc}']
    elif exp == 'E4' and cell == 'stepin' or exp == 'E1' and cell == 'demo':
        extra = ['localizer:=slam']
    else:
        raise ValueError(f'unknown cell {exp} {cell}')
    return {'launch': LAUNCH + extra, 'topics': list(TOPICS), 'wait_topic': wait}


def bag_name(date: str, exp: str, cell: str, run: int) -> str:
    return f'{date}_{exp}_{cell}_run{run}'


def _out(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return 'n/a'


def _stop(proc: subprocess.Popen, name: str) -> None:
    os.killpg(proc.pid, signal.SIGINT)
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        print(f'{name} ignored SIGINT, terminating', file=sys.stderr)
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('exp')
    ap.add_argument('cell')
    ap.add_argument('run', type=int)
    ap.add_argument('--dry', action='store_true', help='print the plan, start nothing')
    args = ap.parse_args()
    plan = cell_plan(args.exp, args.cell)
    date = datetime.date.today().isoformat()
    bag = os.path.expanduser(f'~/bags/{bag_name(date, args.exp, args.cell, args.run)}')
    bag_cmd = ['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag] + plan['topics']
    launch_str = ' '.join(plan['launch'])
    print('launch:', launch_str)
    print('bag   :', ' '.join(bag_cmd))
    print('wait  :', plan['wait_topic'])
    if args.dry:
        return 0
    if os.path.exists(bag):
        print(f'refusing: {bag} exists', file=sys.stderr)
        return 1
    before = _out(['vcgencmd', 'get_throttled'])
    launch = subprocess.Popen(plan['launch'], start_new_session=True)
    bagp = None
    try:
        deadline = time.monotonic() + WAIT_S
        while time.monotonic() < deadline:
            if launch.poll() is not None:
                raise RuntimeError('launch exited early')
            if subprocess.run(['ros2', 'topic', 'echo', '--once', plan['wait_topic']],
                              capture_output=True, timeout=15).returncode == 0:
                break
        else:
            raise RuntimeError(f'{plan["wait_topic"]} not publishing after {WAIT_S:.0f} s')
        bagp = subprocess.Popen(bag_cmd, start_new_session=True)
        input('recording; drive, then press Enter to stop ')
    finally:
        if bagp:
            _stop(bagp, 'bag')
        if launch.poll() is None:
            _stop(launch, 'launch')
    after = _out(['vcgencmd', 'get_throttled'])
    commit = _out(['git', '-C', os.path.dirname(os.path.abspath(__file__)),
                   'rev-parse', '--short', 'HEAD'])
    print(f'| {date} | {commit} | 9 | {args.exp} {args.cell} run {args.run}, '
          f'`{launch_str}`, bag `{bag}` | TODO | TODO | '
          f'get_throttled before {before}, after {after} |')
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Per-bag motion summary for the driven runs: commanded vs odometry distance and heading.

Usage: python3 tools/analysis/bag_summary.py BAG [BAG ...]

Reads /cmd_vel (TwistStamped), /odom_rf2o and /odometry/filtered from rosbag2 MCAP bags
(receive timestamps). Prints one markdown row per bag: cmd_s (first to last non-zero
command), cmd_dist and cmd_angle (each non-zero command held until the next message, gap
capped at 0.5 s, the motor watchdog), then per odom topic along (m, on the start heading)
and dheading (deg, wrapped to +-180), then side (m). rf2o sideways drift is not a result:
on 2026-11-09 it said 16 cm right where the tape said 3 cm left, so it is printed as
"(unreliable, use tape)". read_bag() reads with rosbag2_py on the Pi and with rosbags on the
Mac (.venv); the maths in summarise() needs neither.
"""
import argparse
import math
import os

GAP_CAP_S = 0.5
ODOM_TOPICS = ('/odom_rf2o', '/odometry/filtered')


def _wrap(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


def summarise(cmd: list[tuple[float, float, float]],
              odom: dict[str, list[tuple[float, float, float, float]]]) -> dict:
    """cmd: (t, v, w) from /cmd_vel; odom: topic -> (t, x, y, yaw). Missing data gives None."""
    moving = [i for i, (_, v, w) in enumerate(cmd) if v or w]
    out: dict = {'cmd_s': None, 'cmd_dist': 0.0, 'cmd_angle': 0.0}
    if moving:
        out['cmd_s'] = cmd[moving[-1]][0] - cmd[moving[0]][0]
    for i in moving:
        t, v, w = cmd[i]
        dt = min(cmd[i + 1][0] - t, GAP_CAP_S) if i + 1 < len(cmd) else 0.0
        out['cmd_dist'] += v * dt
        out['cmd_angle'] += w * dt
    for topic, rows in odom.items():
        if len(rows) < 2:
            continue
        (_, x0, y0, yaw0), (_, x1, y1, yaw1) = rows[0], rows[-1]
        dx, dy = x1 - x0, y1 - y0
        out[topic] = {'along': dx * math.cos(yaw0) + dy * math.sin(yaw0),
                      'side': -dx * math.sin(yaw0) + dy * math.cos(yaw0),
                      'dheading_deg': math.degrees(_wrap(yaw1 - yaw0))}
    return out


def _yaw(q) -> float:
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def read_bag(path: str):
    try:
        import rosbag2_py
        from rclpy.serialization import deserialize_message
        from rosidl_runtime_py.utilities import get_message
    except ImportError:
        return _read_bag_rosbags(path)
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=path, storage_id='mcap'),
                rosbag2_py.ConverterOptions('cdr', 'cdr'))
    types = {t.name: get_message(t.type) for t in reader.get_all_topics_and_types()}
    cmd, odom = [], {t: [] for t in ODOM_TOPICS}
    while reader.has_next():
        topic, data, ts = reader.read_next()
        if topic == '/cmd_vel' and topic in types:
            m = deserialize_message(data, types[topic])
            cmd.append((ts * 1e-9, m.twist.linear.x, m.twist.angular.z))
        elif topic in odom and topic in types:
            m = deserialize_message(data, types[topic])
            q, p = m.pose.pose.orientation, m.pose.pose.position
            odom[topic].append((ts * 1e-9, p.x, p.y, _yaw(q)))
    return cmd, odom


def _read_bag_rosbags(path: str):
    from pathlib import Path

    from rosbags.highlevel import AnyReader
    cmd, odom = [], {t: [] for t in ODOM_TOPICS}
    with AnyReader([Path(path)]) as reader:
        conns = [c for c in reader.connections if c.topic == '/cmd_vel' or c.topic in odom]
        for conn, ts, raw in reader.messages(connections=conns):
            m = reader.deserialize(raw, conn.msgtype)
            if conn.topic == '/cmd_vel':
                cmd.append((ts * 1e-9, m.twist.linear.x, m.twist.angular.z))
            else:
                q, p = m.pose.pose.orientation, m.pose.pose.position
                odom[conn.topic].append((ts * 1e-9, p.x, p.y, _yaw(q)))
    return cmd, odom


def _f(v, spec='.3f') -> str:
    return 'n/a' if v is None else format(v, spec)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('bags', nargs='+', metavar='BAG')
    args = ap.parse_args()
    print('| bag | cmd_s | cmd_dist m | cmd_angle rad | '
          'rf2o along m | rf2o dheading deg | filtered along m | filtered dheading deg | '
          'rf2o side m |')
    print('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for bag in args.bags:
        s = summarise(*read_bag(bag))
        r, f = s.get('/odom_rf2o', {}), s.get('/odometry/filtered', {})
        print(f'| {os.path.basename(os.path.normpath(bag))} | {_f(s["cmd_s"], ".1f")} '
              f'| {_f(s["cmd_dist"])} | {_f(s["cmd_angle"])} '
              f'| {_f(r.get("along"))} | {_f(r.get("dheading_deg"), ".1f")} '
              f'| {_f(f.get("along"))} | {_f(f.get("dheading_deg"), ".1f")} '
              f'| {_f(r.get("side"))} (unreliable, use tape) |')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

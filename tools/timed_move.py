#!/usr/bin/env python3
"""Open-loop timed motion for the E2 experiments: 1 m straight or a 360 degree spin.

Usage: python3 tools/timed_move.py straight|spin [--speed V] [--no-stamped] [--topic T]

Publishes at 20 Hz, then a zero command, then exits. It publishes on the collision
monitor's INPUT topic (nav2_params.yaml `cmd_vel_in_topic`), never on /cmd_vel, so the
collision monitor still stops it for obstacles: it needs the Nav2 stack (nav:=true).
Open loop on purpose: E2 compares odometry configs, so the motion must not depend on
the estimator under test. Caps: |v| <= 0.15 m/s (AGENTS rule 1), |w| <= 1.0 rad/s.
"""
import argparse
import math
import time

RATE_HZ = 20.0
V_CAP = 0.15        # m/s, AGENTS.md rule 1
W_CAP = 1.0         # rad/s
STRAIGHT_V = 0.10   # m/s, brief default: 10.0 s for 1.00 m
SPIN_W = 0.5        # rad/s, brief default: 2*pi/0.5 s for 360 deg
TOPIC = 'cmd_vel_smoothed'   # collision_monitor cmd_vel_in_topic in nav2_params.yaml


def profile(kind: str, speed: float | None = None) -> list[tuple[float, float, float]]:
    """(t, v, w) commands; each is held until the next t, the last one is zero."""
    if kind == 'straight':
        speed = STRAIGHT_V if speed is None else speed
        if not 0 < abs(speed) <= V_CAP:
            raise ValueError(f'|v| must be in (0, {V_CAP}] m/s, got {speed}')
        duration, v, w = 1.0 / abs(speed), speed, 0.0
    elif kind == 'spin':
        speed = SPIN_W if speed is None else speed
        if not 0 < abs(speed) <= W_CAP:
            raise ValueError(f'|w| must be in (0, {W_CAP}] rad/s, got {speed}')
        duration, v, w = 2 * math.pi / abs(speed), 0.0, speed
    else:
        raise ValueError(f'unknown motion {kind!r}, use straight or spin')
    steps = math.ceil(duration * RATE_HZ)
    return [(i / RATE_HZ, v, w) for i in range(steps)] + [(duration, 0.0, 0.0)]


def travelled(cmds: list[tuple[float, float, float]]) -> tuple[float, float]:
    """(metres, radians) the commanded profile covers."""
    pairs = list(zip(cmds, cmds[1:]))
    return (sum(abs(c[1]) * (n[0] - c[0]) for c, n in pairs),
            sum(abs(c[2]) * (n[0] - c[0]) for c, n in pairs))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('kind', choices=['straight', 'spin'])
    ap.add_argument('--speed', type=float, help='m/s for straight, rad/s for spin')
    # Nav2 runs with enable_stamped_cmd_vel true (nav2_params.yaml, PR 32), so the
    # collision monitor input is TwistStamped; --no-stamped is for a plain-Twist stack.
    ap.add_argument('--stamped', action=argparse.BooleanOptionalAction, default=True,
                    help='publish TwistStamped (default; the collision monitor input)')
    ap.add_argument('--topic', default=TOPIC)
    args = ap.parse_args()
    cmds = profile(args.kind, args.speed)   # validates the caps before ROS starts

    import rclpy
    from geometry_msgs.msg import Twist, TwistStamped
    rclpy.init()
    node = rclpy.create_node('timed_move')
    pub = node.create_publisher(TwistStamped if args.stamped else Twist, args.topic, 10)

    def send(v: float, w: float) -> None:
        twist = Twist()
        twist.linear.x, twist.angular.z = v, w
        if args.stamped:
            msg = TwistStamped()
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.header.frame_id = 'base_footprint'
            msg.twist = twist
            twist = msg
        pub.publish(twist)

    metres, rad = travelled(cmds)
    print(f'{args.kind}: {cmds[-1][0]:.2f} s, {metres:.3f} m, {math.degrees(rad):.1f} deg '
          f'on /{args.topic}')
    t0 = time.monotonic()
    try:
        for t, v, w in cmds[:-1]:
            time.sleep(max(0.0, t0 + t - time.monotonic()))
            send(v, w)
        time.sleep(max(0.0, t0 + cmds[-1][0] - time.monotonic()))
    finally:
        for _ in range(5):   # also on Ctrl+C: stop
            send(0.0, 0.0)
            time.sleep(0.05)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

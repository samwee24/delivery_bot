#!/usr/bin/env python3
"""Bench power check for the drive motors: a fixed duty for a fixed time, no ROS.

Usage: python3 tools/motor_check.py run DUTY SECONDS | stair

Deliberate exception to AGENTS rule 1 ("motors only through motor_node"): this writes
GPIO directly. It is allowed because it is a power check that must not depend on the
software stack, and because it is fenced in: it refuses to run while any motor_node
process exists, caps duty at 0.35 and a run at 3.0 s, and zeroes PWM in a `finally`.
It replaces /tmp/duty_run.py, which on 2026-11-09 told a dead motor battery apart from
a software fault.

Settings (same as delivery_bot_drivers/config/drivers.yaml): PWM 100 Hz; BCM ENA 12,
IN1 5, IN2 6, ENB 13, IN3 26, IN4 16; forward = IN1 and IN3 on, IN2 and IN4 off. The duty
is rewritten every 50 ms, as motor_node does. A wall-clock timestamp is printed at each
duty change so a bag of /odom_rf2o can be lined up.

Expected on the floor (measured 2026-11-09):
  run 0.30 2   travels about 0.9 m (0.87-0.90 m).
  stair        kick 0.30 for 0.15 s, then duty 0.20, 0.16, 0.14, 0.12, 0.10 for 1.5 s
               each. Rolling speeds were 0.293, 0.213, 0.156, 0.094 and 0.004 m/s; 0.10
               stalls.
A silent run (wheels do not turn) means motor power, not code: check the battery first
(OI-9 in docs/CA3.md).
"""
import argparse
import subprocess
import sys
import time

PWM_HZ = 100
DUTY_MAX = 0.35
SECONDS_MAX = 3.0
REWRITE_S = 0.05
ENA, IN1, IN2, ENB, IN3, IN4 = 12, 5, 6, 13, 26, 16


def check_run(duty: float, seconds: float) -> None:
    if not 0 < duty <= DUTY_MAX:
        raise ValueError(f'duty must be in (0, {DUTY_MAX}], got {duty}')
    if not 0 < seconds <= SECONDS_MAX:
        raise ValueError(f'seconds must be in (0, {SECONDS_MAX}], got {seconds}')


def stair_schedule() -> list[tuple[float, float]]:
    """(duty, seconds): kick-start, then the rolling staircase down to the stall."""
    return [(0.30, 0.15), (0.20, 1.5), (0.16, 1.5), (0.14, 1.5), (0.12, 1.5), (0.10, 1.5)]


def motor_node_running() -> bool:
    try:
        return subprocess.run(['pgrep', '-f', 'motor_node'],
                              capture_output=True).returncode == 0
    except OSError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 epilog='Expected results: see the module docstring.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run', help=f'duty (0, {DUTY_MAX}] for seconds (0, {SECONDS_MAX}]')
    r.add_argument('duty', type=float)
    r.add_argument('seconds', type=float)
    sub.add_parser('stair', help='kick 0.30 then 0.20 .. 0.10, 1.5 s each')
    args = ap.parse_args()
    schedule = stair_schedule()
    try:
        if args.cmd == 'run':
            check_run(args.duty, args.seconds)
            schedule = [(args.duty, args.seconds)]
    except ValueError as e:
        ap.error(str(e))
    if motor_node_running():
        print('refusing: a motor_node process is running; stop the stack first',
              file=sys.stderr)
        return 1
    from gpiozero import DigitalOutputDevice, PWMOutputDevice
    from gpiozero.pins.lgpio import LGPIOFactory
    factory = LGPIOFactory()
    pwm = [PWMOutputDevice(p, frequency=PWM_HZ, pin_factory=factory) for p in (ENA, ENB)]
    pins = [DigitalOutputDevice(p, pin_factory=factory) for p in (IN1, IN2, IN3, IN4)]
    try:
        pins[0].on(), pins[2].on()      # IN1, IN3: forward
        pins[1].off(), pins[3].off()    # IN2, IN4
        for duty, seconds in schedule:
            print(f'{time.time():.3f} duty {duty:.2f} for {seconds} s', flush=True)
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                for p in pwm:
                    p.value = duty
                time.sleep(REWRITE_S)
    finally:
        for p in pwm:
            p.value = 0
        for p in pins:
            p.off()
        for d in pwm + pins:
            d.close()
        print(f'{time.time():.3f} stopped', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

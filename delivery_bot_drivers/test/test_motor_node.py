"""Checks motor_node: wheel/duty maths, lidar stop sector, dry run (no GPIO)."""

from math import inf, pi, radians
import sys
from types import SimpleNamespace

from delivery_bot_drivers.motor_node import blocked, duty_for, MotorNode, wheel_speeds
import pytest
import rclpy

DUTY = {'gain': 2.0, 'min_duty': 0.11, 'max_duty': 0.85, 'min_wheel_speed': 0.01}
# 360 beams, 1 degree apart, angle 0 at index 0
SCAN = {'angle_min': 0.0, 'angle_increment': radians(1), 'range_min': 0.15,
        'stop_dist': 0.20, 'half_angle': radians(35)}


def free_scan(**close):
    """360 free beams with {index: range} set."""
    ranges = [3.0] * 360
    for i, r in close.items():
        ranges[int(i)] = r
    return ranges


def check(ranges, v, forward_angle=0.0, **over):
    args = {**SCAN, **over}
    return blocked(ranges, args['angle_min'], args['angle_increment'],
                   args['range_min'], v, args['stop_dist'], args['half_angle'],
                   forward_angle)


def test_straight_gives_equal_wheel_speeds() -> None:
    assert wheel_speeds(0.1, 0.0, 0.156) == (0.1, 0.1)


def test_spin_gives_opposite_wheel_speeds() -> None:
    left, right = wheel_speeds(0.0, 1.0, 0.156)
    assert left == pytest.approx(-0.078)
    assert right == pytest.approx(0.078)


def test_duty_zero_below_min_wheel_speed() -> None:
    assert duty_for(0.005, **DUTY) == (0.0, 1)


def test_duty_is_min_duty_plus_gain_times_speed() -> None:
    duty, direction = duty_for(0.1, **DUTY)
    assert duty == pytest.approx(0.11 + 2.0 * 0.1)
    assert direction == 1


def test_duty_clamped_to_max_duty() -> None:
    assert duty_for(5.0, **DUTY) == (0.85, 1)


def test_negative_speed_is_direction_minus_one() -> None:
    duty, direction = duty_for(-0.1, **DUTY)
    assert duty == pytest.approx(0.31)
    assert direction == -1


def test_blocked_dead_ahead_when_driving_forward() -> None:
    assert check(free_scan(**{'0': 0.15}), v=0.1)


def test_not_blocked_by_obstacle_behind_when_driving_forward() -> None:
    assert not check(free_scan(**{'180': 0.15}), v=0.1)


def test_blocked_behind_when_reversing() -> None:
    assert check(free_scan(**{'180': 0.15}), v=-0.1)


def test_not_blocked_at_0_25_m() -> None:
    assert not check(free_scan(**{'0': 0.25}), v=0.1)


def test_no_echo_and_below_range_min_are_free() -> None:
    assert not check(free_scan(**{'0': inf, '1': 0.05, '359': float('nan')}), v=0.1)


def test_not_blocked_outside_half_angle() -> None:
    assert not check(free_scan(**{'60': 0.15}), v=0.1)


def test_not_blocked_when_v_is_zero() -> None:
    assert not check(free_scan(**{'0': 0.15}), v=0.0)


def test_respects_forward_angle() -> None:
    ranges = free_scan(**{'90': 0.15})
    assert not check(ranges, v=0.1)
    assert check(ranges, v=0.1, forward_angle=pi / 2)


@pytest.fixture
def dry_node(monkeypatch):
    """Build a MotorNode in dry run; gpiozero is made unimportable to prove it."""
    monkeypatch.setitem(sys.modules, 'gpiozero', None)
    rclpy.init()
    node = MotorNode()
    yield node
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def test_dry_run_is_default_and_records_duty_without_gpio(dry_node) -> None:
    assert dry_node.dry_run is True
    dry_node.set_wheel('l', 0.3, 1)
    assert dry_node.last['l'] == (0.3, 1)
    dry_node.stop()
    assert dry_node.last['l'][0] == 0.0
    dry_node.stop_all()


def test_stale_scan_stops_even_with_a_fresh_command(dry_node) -> None:
    dry_node.set_wheel('l', 0.3, 1)
    dry_node.v = 0.1
    dry_node.last_cmd_time = dry_node.get_clock().now()
    dry_node._control_step()  # no scan ever arrived
    assert dry_node.last['l'][0] == 0.0 and dry_node.last['r'][0] == 0.0


def test_lidar_stop_zeroes_linear_but_keeps_turning(dry_node) -> None:
    ranges = free_scan(**{'0': 0.15})
    dry_node.scan = SimpleNamespace(
        ranges=ranges, angle_min=0.0, angle_increment=radians(1), range_min=0.15)
    dry_node.scan_time = dry_node.get_clock().now()
    dry_node.v, dry_node.w = 0.1, 1.0
    dry_node.last_cmd_time = dry_node.get_clock().now()
    dry_node._control_step()
    # v zeroed: wheels turn opposite ways
    assert dry_node.last['l'][1] == -1 and dry_node.last['r'][1] == 1

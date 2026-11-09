"""Tests for the motion profile in tools/timed_move.py (pure maths, no ROS needed)."""
import importlib.util
import math
import os
import re

import pytest

_here = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location(
    'timed_move', os.path.join(_here, '..', 'timed_move.py'))
tm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tm)


def test_imports_without_rclpy():
    src = open(os.path.join(_here, '..', 'timed_move.py')).read()
    assert not re.search(r'^(import rclpy|from (rclpy|geometry_msgs))', src, re.M)


def test_straight_covers_one_metre():
    m, rad = tm.travelled(tm.profile('straight'))
    assert abs(m - 1.0) < 0.01 and rad == 0


def test_straight_other_speed_still_one_metre():
    assert abs(tm.travelled(tm.profile('straight', 0.05))[0] - 1.0) < 0.01


def test_spin_covers_full_turn():
    m, rad = tm.travelled(tm.profile('spin'))
    assert abs(rad - 2 * math.pi) < 0.01 and m == 0


def test_last_command_is_zero():
    for kind in ('straight', 'spin'):
        assert tm.profile(kind)[-1][1:] == (0.0, 0.0)


@pytest.mark.parametrize('kind,speed', [('straight', 0.16), ('straight', -0.2),
                                        ('straight', 0), ('spin', 1.1), ('spin', -1.5)])
def test_speeds_above_caps_raise(kind, speed):
    with pytest.raises(ValueError):
        tm.profile(kind, speed)


def test_unknown_motion_raises():
    with pytest.raises(ValueError):
        tm.profile('wiggle')


def test_topic_is_collision_monitor_input_not_cmd_vel():
    params = open(os.path.join(_here, '..', '..', 'delivery_bot_bringup', 'config',
                               'nav2_params.yaml')).read()
    assert re.search(r'cmd_vel_in_topic:\s*"%s"' % tm.TOPIC, params)
    assert tm.TOPIC != 'cmd_vel'


def test_defaults_to_stamped_like_the_collision_monitor_input():
    params = open(os.path.join(_here, '..', '..', 'delivery_bot_bringup', 'config',
                               'nav2_params.yaml')).read()
    cm = params.split('\ncollision_monitor:\n')[1].split('\n\n')[0]
    assert 'enable_stamped_cmd_vel: true' in cm
    src = open(os.path.join(_here, '..', 'timed_move.py')).read()
    assert 'BooleanOptionalAction, default=True' in src

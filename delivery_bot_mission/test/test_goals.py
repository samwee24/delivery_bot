"""Tests for the pure goals.yaml helpers."""

import math

import pytest

from delivery_bot_mission import goals


@pytest.mark.parametrize('yaw', [0.0, math.pi / 2, -math.pi / 2, math.pi - 1e-6])
def test_yaw_quaternion_round_trip(yaw):
    assert goals.yaw_from_quaternion(*goals.quaternion_from_yaw(yaw)) == pytest.approx(yaw)


def test_yaw_pi_is_the_same_heading_either_way():
    yaw = goals.yaw_from_quaternion(*goals.quaternion_from_yaw(math.pi))
    assert abs(yaw) == pytest.approx(math.pi)


def write(tmp_path, text):
    path = tmp_path / 'goals.yaml'
    path.write_text(text)
    return str(path)


def test_load_requires_home(tmp_path):
    with pytest.raises(ValueError, match='home'):
        goals.load_goals(write(tmp_path, 'seat_1: {x: 1, y: 2, yaw: 0}\n'))


def test_load_rejects_goal_without_xy(tmp_path):
    with pytest.raises(ValueError, match='seat_1'):
        goals.load_goals(write(tmp_path, 'home: {x: 0, y: 0}\nseat_1: {x: 1}\n'))


def test_pick_goals_unknown_name_is_a_clear_error():
    with pytest.raises(ValueError, match='nope'):
        goals.pick_goals({'home': {}}, ['nope'])


def test_pose_fields_converts_yaw_and_defaults_it():
    x, y, qx, qy, qz, qw = goals.pose_fields({'x': 1.5, 'y': -2.0, 'yaw': math.pi / 2})
    assert (x, y, qx, qy) == (1.5, -2.0, 0.0, 0.0)
    assert (qz, qw) == pytest.approx((math.sin(math.pi / 4), math.cos(math.pi / 4)))
    assert goals.pose_fields({'x': 0, 'y': 0})[5] == 1.0


def test_save_keeps_existing_entries_and_comments(tmp_path):
    path = write(tmp_path, '# header\nhome:\n  x: 0.0\n  y: 0.0\n  yaw: 0.0\n')
    goals.save_goal(path, 'seat_1', 1.23456, -0.5, 1.57079)
    assert open(path).read().startswith('# header\n')
    saved = goals.load_goals(path)
    assert saved['home'] == {'x': 0.0, 'y': 0.0, 'yaw': 0.0}
    assert saved['seat_1'] == {'x': 1.235, 'y': -0.5, 'yaw': 1.571}


def test_save_refuses_existing_name_without_overwrite(tmp_path):
    path = write(tmp_path, 'home: {x: 0, y: 0, yaw: 0}\n')
    with pytest.raises(ValueError, match='overwrite'):
        goals.save_goal(path, 'home', 9, 9, 0)
    assert goals.load_goals(path)['home']['x'] == 0
    goals.save_goal(path, 'home', 9, 9, 0, overwrite=True)
    assert goals.load_goals(path)['home']['x'] == 9

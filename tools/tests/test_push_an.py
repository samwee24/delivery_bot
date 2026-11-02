"""Tests for window() in tools/analysis/push_an.py (pure maths, no ROS needed)."""
import importlib.util
import math
import os

_spec = importlib.util.spec_from_file_location(
    'push_an', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'push_an.py'))
push_an = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(push_an)


def test_straight_move():
    P = [(0, 0, 0, 0), (1, 0.3, 0, 0), (2, 0.6, 0, 0), (3, 0.9, 0, 0)]
    dist, dyaw, n = push_an.window(P, 1, 3)
    assert abs(dist - 0.6) < 1e-9 and dyaw == 0 and n == 3


def test_distance_ignores_heading():
    h = math.pi / 2
    P = [(0, 1, 1, h), (1, 1, 1.5, h)]
    dist, dyaw, n = push_an.window(P, 0, 1)
    assert abs(dist - 0.5) < 1e-9 and abs(dyaw) < 1e-9 and n == 2


def test_yaw_wraps():
    P = [(0, 0, 0, math.radians(179)), (1, 0, 0, math.radians(-179))]
    assert abs(push_an.window(P, 0, 1)[1] - 2) < 1e-9

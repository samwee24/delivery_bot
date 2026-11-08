"""Tests for unwrap() and integrate() in tools/analysis/turn_an.py (pure maths, no ROS needed)."""
import importlib.util
import math
import os

_spec = importlib.util.spec_from_file_location(
    'turn_an', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'turn_an.py'))
turn_an = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(turn_an)


def test_unwrap_across_pi():
    # 170 -> -170 -> -150 deg is +20 then +20, not -340
    Y = [(0, math.radians(170)), (1, math.radians(-170)), (2, math.radians(-150))]
    u = turn_an.unwrap(Y)
    assert [t for t, _ in u] == [0, 1, 2]
    assert [round(math.degrees(a), 9) for _, a in u] == [0, 20, 40]


def test_unwrap_full_turn_counts_past_360():
    Y = [(k, math.atan2(math.sin(math.radians(30 * k)), math.cos(math.radians(30 * k)))) for k in range(14)]
    assert abs(math.degrees(turn_an.unwrap(Y)[-1][1]) - 390) < 1e-9


def test_unwrap_empty_and_single():
    assert turn_an.unwrap([]) == []
    assert turn_an.unwrap([(5, 1.0)]) == [(5, 0)]


def test_integrate_uses_gap_before_each_sample():
    # first sample has no gap; 2 * 0.5 + 4 * 0.25
    assert abs(turn_an.integrate([(0, 100), (0.5, 2), (0.75, 4)]) - 2) < 1e-12


def test_integrate_too_short():
    assert turn_an.integrate([]) == 0 and turn_an.integrate([(0, 1)]) == 0

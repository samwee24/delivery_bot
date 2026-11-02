"""Tests for rest(), moving() and slope() in tools/analysis/var_an.py (pure maths, no ROS needed)."""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    'var_an', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'var_an.py'))
var_an = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(var_an)

# rf2o at 100, 101, 102, 103 s: (t, vx, wz); gyro every 0.5 s
O = [(100, 0.0, 0.0), (101, 0.1, 0.5), (102, 0.2, 1.0), (103, 0.0, 0.0)]
G = [(100.0, 0.4), (100.5, 0.6), (101.0, 1.0), (101.5, 1.0), (102.0, 0.0), (102.5, 0.0)]


def test_rest_is_open_interval():
    R, g = var_an.rest(O, G, 100, 0, 2)
    assert R == [(101, 0.1, 0.5)]
    assert g == [0.6, 1.0, 1.0]


def test_moving_means_gyro_over_each_interval():
    res, rf, gg = var_an.moving(O, G, 100, 1, 2)
    # i=1: gyro over [100, 101) mean 0.5; i=2: over [101, 102) mean 1.0
    assert rf == [0.5, 1.0] and gg == [0.5, 1.0] and res == [0.0, 0.0]


def test_moving_skips_interval_without_gyro():
    res, rf, gg = var_an.moving(O, G[:2], 100, 0, 3)
    assert rf == [0.5] and gg == [0.5]


def test_moving_empty_window():
    assert var_an.moving(O, G, 100, 50, 60) == ([], [], [])


def test_slope_least_squares_through_origin():
    # sum(rf*gg) / sum(gg^2) = (2*1 + 4*2) / (1 + 4)
    assert var_an.slope([2, 4], [1, 2]) == 2


def test_var_is_population_variance():
    assert var_an.var([1, 3]) == 1

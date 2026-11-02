"""Tests for pgm() and track() in tools/analysis/sweep_an.py (pure maths, no ROS needed)."""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    'sweep_an', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'sweep_an.py'))
sweep_an = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep_an)


def test_pgm_counts_cells():
    # pixel 10 is a newline byte: the data part must not be split on it
    w, h, c = sweep_an.pgm(b'P5\n3 2\n255\n' + bytes([254, 0, 205, 254, 10, 254]))
    assert (w, h) == (3, 2)
    assert c[254] == 3 and c[0] == 1 and c[205] == 1 and c[10] == 1


def test_track_square_loop():
    L = [[0, 0, 0], [1, 1, 0], [2, 1, 1], [3, 0, 1], [4, 0, 0.1]]
    path, closure = sweep_an.track(L)
    assert abs(path - 3.9) < 1e-9 and abs(closure - 0.1) < 1e-9


def test_track_single_pose():
    assert sweep_an.track([[0, 2.0, 3.0, 0, 0, 0, 0, 1]]) == (0, 0.0)

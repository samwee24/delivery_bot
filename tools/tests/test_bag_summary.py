"""Tests for summarise() in tools/analysis/bag_summary.py (pure maths, no ROS needed)."""
import importlib.util
import math
import os

import pytest

_spec = importlib.util.spec_from_file_location(
    'bag_summary', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'bag_summary.py'))
bsum = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bsum)

R = '/odom_rf2o'


def test_one_metre_straight_at_20_hz():
    n = 134   # 6.7 s at 20 Hz, 0.15 m/s
    cmd = [(i * 0.05, 0.15, 0.0) for i in range(n)] + [(n * 0.05, 0.0, 0.0)]
    odom = {R: [(i * 0.05, 0.15 * i * 0.05, 0.0, 0.0) for i in range(n + 1)]}
    s = bsum.summarise(cmd, odom)
    assert s['cmd_dist'] == pytest.approx(1.0, abs=0.01)
    assert s[R]['along'] == pytest.approx(1.0, abs=0.01)
    assert s[R]['side'] == pytest.approx(0.0, abs=1e-9)
    assert s['cmd_s'] == pytest.approx(n * 0.05 - 0.05)


def test_full_spin_wraps_to_zero_heading_change():
    w, n = 0.5, 251   # 2*pi/0.5 = 12.57 s at 20 Hz
    cmd = [(i * 0.05, 0.0, w) for i in range(n)] + [(n * 0.05, 0.0, 0.0)]
    odom = {R: [(i * 0.05, 0.0, 0.0, math.atan2(math.sin(w * i * 0.05), math.cos(w * i * 0.05)))
                for i in range(n + 1)]}
    s = bsum.summarise(cmd, odom)
    assert s['cmd_angle'] == pytest.approx(2 * math.pi, abs=0.05)
    assert abs(s[R]['dheading_deg']) < 3.0


def test_a_two_second_gap_counts_only_the_watchdog_time():
    s = bsum.summarise([(0.0, 0.1, 0.0), (2.0, 0.0, 0.0)], {})
    assert s['cmd_dist'] == pytest.approx(0.05)


def test_displacement_is_projected_on_the_start_heading():
    odom = {R: [(0.0, 1.0, 1.0, math.pi / 2), (1.0, 1.0, 2.0, math.pi / 2)]}
    s = bsum.summarise([], odom)
    assert s[R]['along'] == pytest.approx(1.0)
    assert s[R]['side'] == pytest.approx(0.0, abs=1e-9)
    assert s['cmd_s'] is None

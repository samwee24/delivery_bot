"""Test for clip() in tools/analysis/scan_minrange.py (needs rclpy and sensor_msgs, so skipped without ROS)."""
import importlib.util
import os

import pytest

pytest.importorskip('sensor_msgs')
from sensor_msgs.msg import LaserScan  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    'scan_minrange', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'scan_minrange.py'))
sm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sm)


def test_clip_drops_only_ranges_below_minr():
    m = LaserScan()
    m.ranges = [0.3, 0.59, 0.6, 2.0, float('inf')]
    out = sm.clip(m).ranges
    assert list(out[:2]) == [float('inf')] * 2
    assert list(out[2:4]) == pytest.approx([0.6, 2.0])

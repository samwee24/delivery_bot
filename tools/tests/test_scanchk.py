"""Tests for med() in tools/analysis/scanchk.py (pure maths, no ROS needed)."""
import importlib.util
import math
import os
from types import SimpleNamespace

_spec = importlib.util.spec_from_file_location(
    'scanchk', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'scanchk.py'))
scanchk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scanchk)


def _scan(ranges):
    # beams every 2 deg from -180: none sits on the +-3 deg edge, so float rounding cannot move one in or out
    return (0, SimpleNamespace(ranges=ranges, angle_min=math.radians(-180), angle_increment=math.radians(2)))


def test_median_within_3_deg():
    # 0 deg is index 90; -2, 0, +2 deg are inside, -4 and +4 are not
    r = [9.0] * 180
    r[88:93] = [0.5, 1.0, 2.0, 4.0, 0.7]
    assert scanchk.med([_scan(r)], 0) == 2.0


def test_drops_inf_and_short_ranges():
    r = [9.0] * 180
    r[89:92] = [float('inf'), 0.05, 1.5]
    assert scanchk.med([_scan(r)], 0) == 1.5


def test_pools_beams_over_scans():
    a, b = [9.0] * 180, [9.0] * 180
    a[44:47] = [1.0, 1.0, 1.0]   # -90 deg is index 45
    b[44:47] = [3.0, 3.0, 3.0]
    assert scanchk.med([_scan(a), _scan(b)], -90) == 2.0


def test_180_wraps_to_minus_180():
    # inside 3 deg of 180: -180, -178 (start of scan) and 178 (end); 176 and -176 are outside
    r = [9.0] * 180
    r[0], r[1], r[179] = 1.0, 2.0, 3.0
    r[2], r[178] = 0.5, 0.5
    assert scanchk.med([_scan(r)], 180) == 2.0


def test_no_beams_is_none():
    assert scanchk.med([], 90) is None
    assert scanchk.med([_scan([float('inf')] * 180)], 90) is None

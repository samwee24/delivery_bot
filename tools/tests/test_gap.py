"""Tests for compose(), origin(), pgm() and ray() in tools/analysis/gap.py (pure maths, no ROS needed)."""
import importlib.util
import math
import os
from types import SimpleNamespace

_spec = importlib.util.spec_from_file_location(
    'gap', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'gap.py'))
gap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gap)


def test_yaw_from_quaternion():
    h = math.radians(120)
    q = SimpleNamespace(x=0.0, y=0.0, z=math.sin(h / 2), w=math.cos(h / 2))
    assert abs(gap.yaw(q) - h) < 1e-12


def test_compose_rotates_odom_pose():
    # map->odom: (1, 2) turned 90 deg; odom pose (1, 0) facing 0 lands at (1, 3) facing 90
    x, y, th = gap.compose((1, 2, math.pi / 2), (1, 0, 0))
    assert abs(x - 1) < 1e-12 and abs(y - 3) < 1e-12 and abs(th - math.pi / 2) < 1e-12
    # odom (0, 1): 1 m to the odom left is 1 m along map -x
    x, y, th = gap.compose((1, 2, math.pi / 2), (0, 1, 0.5))
    assert abs(x - 0) < 1e-12 and abs(y - 2) < 1e-12 and abs(th - (math.pi / 2 + 0.5)) < 1e-12


def test_origin_from_yaml():
    assert gap.origin('image: m.pgm\norigin: [-1.5, 2.25, 0.0]\n') == [-1.5, 2.25]


def _box():
    # 10 x 4 cells of 0.05 m, origin (0, 0); one wall column at i = 8, rows stored top first
    w, h = 10, 4
    px = bytearray([254]) * (w * h)
    for j in range(h):
        px[(h - 1 - j) * w + 8] = 0
    return bytes(px), w, h


def test_ray_hits_wall():
    px, w, h = _box()
    # from x = 0.13 the first 0.025 m step inside cell 8 (x >= 0.40) is d = 0.275 (x = 0.405)
    assert abs(gap.ray(px, w, h, 0, 0, 0.13, 0.1, 0) - 0.275) < 1e-9


def test_ray_row_order_is_flipped():
    # wall only in map row j = 0 (bottom, stored last): a ray along y = 0.025 hits it, y = 0.175 does not
    w, h = 10, 4
    px = bytearray([254]) * (w * h)
    px[(h - 1) * w + 8] = 0
    assert gap.ray(bytes(px), w, h, 0, 0, 0.125, 0.025, 0) is not None
    assert gap.ray(bytes(px), w, h, 0, 0, 0.125, 0.175, 0) is None


def test_ray_leaves_map():
    px, w, h = _box()
    assert gap.ray(px, w, h, 0, 0, 0.125, 0.1, math.pi) is None


def test_pgm_header():
    w, h, px = gap.pgm(b'P5\n2 1\n255\n' + bytes([0, 254]))
    assert (w, h, px) == (2, 1, bytes([0, 254]))

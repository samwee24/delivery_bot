"""Tests for the pure parts of tools/motor_check.py (no GPIO needed)."""
import importlib.util
import os

import pytest

_spec = importlib.util.spec_from_file_location(
    'motor_check', os.path.join(os.path.dirname(__file__), '..', 'motor_check.py'))
mc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mc)


@pytest.mark.parametrize('duty,seconds', [(0.35, 2.0), (0.30, 3.0), (0.01, 0.1)])
def test_check_run_accepts_in_bounds(duty, seconds):
    mc.check_run(duty, seconds)


@pytest.mark.parametrize('duty,seconds', [(0.36, 2.0), (0.0, 2.0), (-0.1, 2.0),
                                          (0.30, 3.1), (0.30, 0.0)])
def test_check_run_rejects_out_of_bounds(duty, seconds):
    with pytest.raises(ValueError):
        mc.check_run(duty, seconds)


def test_stair_starts_with_the_kick_and_ends_at_the_stall_duty():
    s = mc.stair_schedule()
    assert s[0] == (0.30, 0.15)
    assert s[-1][0] == 0.10
    assert all(d <= mc.DUTY_MAX for d, _ in s)

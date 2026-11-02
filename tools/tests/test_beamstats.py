"""Tests for scan_stats() and summarise() in tools/analysis/beamstats.py (pure maths, no ROS needed)."""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    'beamstats', os.path.join(os.path.dirname(__file__), '..', 'analysis', 'beamstats.py'))
bs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bs)

inf, nan = float('inf'), float('nan')


def test_bad_fraction_counts_inf_nan_zero():
    bad, _, _ = bs.scan_stats([1.0, inf, nan, 0.0, 2.0])
    assert bad == 3 / 5


def test_duplicates_only_between_adjacent_finite():
    # pairs: (1,1) dup, (1,2) no, (2,2) dup, (2,3) no -> 2/4; the inf gap breaks adjacency
    _, dup, _ = bs.scan_stats([1.0, 1.0, 2.0, 2.0, 3.0, inf, 3.0])
    assert dup == 2 / 4


def test_longest_run_of_bad_beams():
    _, _, run = bs.scan_stats([1.0, inf, nan, 0.0, 1.0, inf, 1.0])
    assert run == 3


def test_run_at_end_counts():
    assert bs.scan_stats([1.0, inf, inf])[2] == 2


def test_summarise_medians_and_counts():
    s = bs.summarise([[1.0, inf], [1.0, 1.0, 1.0], [1.0, 2.0]])
    assert (s['beams_min'], s['beams_max'], s['scans']) == (2, 3, 3)
    assert s['bad_med'] == 0 and s['dup_med'] == 0 and s['run_max'] == 1

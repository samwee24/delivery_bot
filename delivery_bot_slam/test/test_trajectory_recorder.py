"""Pure-logic checks for the recorder's append rule and quaternion handling."""

import math
from types import SimpleNamespace

from delivery_bot_slam.trajectory_recorder import accept, normalise, TrajectoryRecorder


def pose(x=0.0, y=0.0, yaw=0.0):
    return (0.0, x, y, 0.0, 0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2))


def test_append_rule() -> None:
    assert accept(pose(), None, 0.02, 2.0)           # first pose always kept
    assert not accept(pose(0.019), pose(), 0.02, 2.0)
    assert accept(pose(0.021), pose(), 0.02, 2.0)
    assert not accept(pose(yaw=math.radians(1.9)), pose(), 0.02, 2.0)
    assert accept(pose(yaw=math.radians(2.1)), pose(), 0.02, 2.0)
    # yaw wraps across +-pi: 179 -> -179 is 2 degrees, not 358
    assert accept(pose(yaw=math.radians(-179)), pose(yaw=math.radians(177)), 0.02, 2.0)


def test_normalise() -> None:
    assert normalise((0, 0, 0, 0)) is None
    assert abs(sum(c * c for c in normalise((0, 0, 3, 4))) - 1.0) < 1e-12


def test_yaw_wrap_is_a_small_rotation() -> None:
    # +179 -> -179 deg is 2 degrees of rotation, not 358, so 5 degrees rejects it
    assert not accept(pose(yaw=math.radians(-179)), pose(yaw=math.radians(179)), 0.02, 5.0)
    assert accept(pose(yaw=math.radians(-174)), pose(yaw=math.radians(179)), 0.02, 5.0)


def recorder(tum_dir=None):
    node = TrajectoryRecorder.__new__(TrajectoryRecorder)   # skip TF and publishers
    node._tum_dir = str(tum_dir) if tum_dir else ''
    node._written = False
    node._slam = [(1.5, 0.0, 0.0, 0.0, *normalise((0, 0, 3, 4))),
                  (2.25, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 1.0)]
    node._odom = [(1.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)]
    node.get_logger = lambda: SimpleNamespace(info=lambda text: None)
    return node


def test_tum_files_have_eight_numbers_per_line(tmp_path) -> None:
    node = recorder(tmp_path / 'out')
    node._write_tum_files()
    files = {p.name.split('_')[0]: p for p in (tmp_path / 'out').glob('*.tum')}
    assert set(files) == {'slam', 'odom'}
    rows = [line.split(' ') for line in files['slam'].read_text().splitlines()]
    assert len(rows) == 2
    for row in rows:
        values = [float(v) for v in row]
        assert len(values) == 8
        assert math.isclose(math.sqrt(sum(q * q for q in values[4:])), 1.0)
    assert [float(r[0]) for r in rows] == [1.5, 2.25]   # seconds
    assert len(files['odom'].read_text().splitlines()) == 1


def test_empty_tum_dir_writes_nothing(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)   # a stray relative write would land here
    node = recorder()
    node._write_tum_files()
    assert list(tmp_path.iterdir()) == []

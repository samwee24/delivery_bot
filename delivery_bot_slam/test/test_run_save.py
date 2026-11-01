"""copy_configs puts every YAML from the source dirs into the run's config folder."""

from delivery_bot_slam.run_save import copy_configs


def test_copy_configs(tmp_path) -> None:
    a, b = tmp_path / 'a', tmp_path / 'b'
    a.mkdir()
    b.mkdir()
    (a / 'ekf.yaml').write_text('x: 1')
    (a / 'notes.txt').write_text('skip')
    (b / 'drivers.yaml').write_text('y: 2')
    dest = tmp_path / 'run_config'
    assert copy_configs([str(a), str(b)], str(dest)) == ['ekf.yaml', 'drivers.yaml']
    assert sorted(p.name for p in dest.iterdir()) == ['drivers.yaml', 'ekf.yaml']

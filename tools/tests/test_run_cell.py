"""Tests for cell_plan() and bag_name() in tools/run_cell.py (pure, no ROS needed)."""
import importlib.util
import os

import pytest

_spec = importlib.util.spec_from_file_location(
    'run_cell', os.path.join(os.path.dirname(__file__), '..', 'run_cell.py'))
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

BASE = ['ros2', 'launch', 'delivery_bot_bringup', 'navigation.launch.py', 'nav:=true']
OFF = ['bridge:=false']
S = '/share'


def plan(exp, cell):
    return rc.cell_plan(exp, cell, share=S)


@pytest.mark.parametrize('config', ['rf2o_imu', 'rf2o_only', 'imu_only'])
@pytest.mark.parametrize('cond', ['empty', 'people'])
def test_e2_variants_pass_the_installed_ekf_file(config, cond):
    p = plan('E2', f'{config}_{cond}')
    assert p['launch'] == BASE + ['localizer:=slam',
                                  f'ekf_params_file:={S}/config/ekf_variants/{config}.yaml'] + OFF
    assert p['wait_topic'] == '/odometry/filtered'


@pytest.mark.parametrize('cond', ['empty', 'people'])
def test_e2_none_turns_the_ekf_off(cond):
    p = plan('E2', f'none_{cond}')
    assert p['launch'] == BASE + ['localizer:=slam', 'ekf:=false'] + OFF
    assert p['wait_topic'] == '/tf'


@pytest.mark.parametrize('loc', ['slam', 'amcl'])
@pytest.mark.parametrize('cond', ['empty', 'people', 'wrongstart'])
def test_e3_cells(loc, cond):
    assert plan('E3', f'{loc}_{cond}')['launch'] == BASE + [f'localizer:={loc}'] + OFF


@pytest.mark.parametrize('exp,cell', [('E4', 'stepin'), ('E1', 'demo')])
def test_e4_and_e1(exp, cell):
    assert plan(exp, cell)['launch'] == BASE + ['localizer:=slam'] + OFF


@pytest.mark.parametrize('exp,cell', [('E9', 'demo'), ('E2', 'bogus_empty'),
                                      ('E2', 'none_crowd'), ('E2', 'none'),
                                      ('E3', 'icp_empty'), ('E3', 'slam_crowd'),
                                      ('E4', 'demo'), ('E1', 'stepin')])
def test_unknown_exp_or_cell_raises(exp, cell):
    with pytest.raises(ValueError):
        plan(exp, cell)


def test_bag_name():
    assert rc.bag_name('2026-11-09', 'E2', 'none_people', 3) == '2026-11-09_E2_none_people_run3'


def test_no_plan_sets_dry_run_and_bags_the_required_topics():
    cells = [('E2', f'{c}_{k}') for c in rc.E2_CONFIGS for k in rc.CONDS]
    cells += [('E3', f'{loc}_{k}') for loc in rc.LOCS for k in ('empty', 'people', 'wrongstart')]
    cells += [('E4', 'stepin'), ('E1', 'demo')]
    for exp, cell in cells:
        p = plan(exp, cell)
        assert 'dry_run' not in ' '.join(p['launch'])
        assert {'/scan', '/imu/data', '/odometry/filtered', '/tf', '/cmd_vel'} <= set(p['topics'])


def test_bridge_true_omits_the_bridge_off_argument():
    p = rc.cell_plan('E3', 'slam_empty', share=S, bridge=True)
    assert p['launch'] == BASE + ['localizer:=slam']


def test_extras_are_returned_in_order():
    assert rc.check_extras(['localizer:=amcl', 'x:=1']) == ['localizer:=amcl', 'x:=1']


@pytest.mark.parametrize('bad', ['foo', 'a:=b; rm', 'a:=', ':=b', '1a:=b', 'a b:=c'])
def test_malformed_extra_is_rejected(bad):
    with pytest.raises(ValueError):
        rc.check_extras(['localizer:=amcl', bad])

"""Every launch file must at least load; slam_replay must wire the TF and EKF rules."""

import importlib.util
from pathlib import Path
import re

from ament_index_python.packages import get_package_share_directory
import launch
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import LifecycleNode, Node
import pytest

LAUNCH_DIRS = [Path(get_package_share_directory(p)) / 'launch'
               for p in ('delivery_bot_bringup', 'delivery_bot_slam')]
LAUNCH_FILES = sorted(f for d in LAUNCH_DIRS for f in d.glob('*.launch.py'))
EXPLORE = LAUNCH_DIRS[1] / 'explore.launch.py'
REPLAY = LAUNCH_DIRS[1] / 'slam_replay.launch.py'


def generate(path: Path) -> launch.LaunchDescription:
    spec = importlib.util.spec_from_file_location(path.stem.replace('.', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_launch_description()


def walk(entities):
    for entity in entities:
        yield entity
        sub = getattr(entity, 'get_sub_entities', None)
        if sub is not None:
            yield from walk(sub())


def nodes(description):
    return [e for e in walk(description.entities) if isinstance(e, Node)]


def test_launch_files_were_found() -> None:
    assert {f.name for f in LAUNCH_FILES} >= {'slam_replay.launch.py', 'mapping.launch.py'}


@pytest.mark.parametrize('path', LAUNCH_FILES, ids=lambda p: p.name)
def test_launch_file_loads(path) -> None:
    assert isinstance(generate(path), launch.LaunchDescription)


def test_replay_has_one_ekf_and_the_relay() -> None:
    found = nodes(generate(REPLAY))
    assert sum(n.node_package == 'robot_localization' for n in found) == 1
    assert sum(n.node_executable == 'odom_covariance_relay' for n in found) == 1
    assert any(n.node_package == 'rf2o_laser_odometry' for n in found)


def test_replay_slam_toolbox_is_a_lifecycle_node() -> None:
    slam = [n for n in nodes(generate(REPLAY)) if n.node_package == 'slam_toolbox']
    assert len(slam) == 1
    assert isinstance(slam[0], LifecycleNode)


def test_replay_rf2o_does_not_publish_tf() -> None:
    # The launch_ros Node keeps its parameters in private attributes, so this reads
    # the source: the first publish_tf after the rf2o executable is rf2o's own.
    m = re.search(r"executable='rf2o_laser_odometry_node'.*?'publish_tf':\s*(\w+)",
                  REPLAY.read_text(), re.S)
    assert m and m.group(1) == 'False'


def test_base_owns_odom_tf_once_and_rf2o_does_not() -> None:
    found = nodes(generate(LAUNCH_DIRS[0] / 'base.launch.py'))
    assert sum(n.node_package == 'robot_localization' for n in found) == 1
    assert {'robot_state_publisher', 'imu_node', 'odom_covariance_relay',
            'foxglove_bridge'} <= {n.node_executable for n in found}


def declared(name: str) -> dict:
    """Launch arguments a bringup file declares, name -> default text."""
    path = LAUNCH_DIRS[0] / name
    return {e.name: ''.join(t.text for t in e.default_value)
            for e in generate(path).entities if isinstance(e, DeclareLaunchArgument)}


def test_base_declares_dry_run_true_by_default() -> None:
    # AGENTS rule 1: live motors are a deliberate act, never a launch default.
    assert declared('base.launch.py')['dry_run'] == 'true'


@pytest.mark.parametrize('name', ['base.launch.py', 'mapping.launch.py', 'navigation.launch.py'])
def test_stack_launch_files_declare_bridge_true_by_default(name) -> None:
    # robot_control.py passes bridge:=false when it already runs the one bridge on 8765.
    assert declared(name)['bridge'] == 'true'


def test_bridge_argument_gates_the_foxglove_node() -> None:
    found = nodes(generate(LAUNCH_DIRS[0] / 'base.launch.py'))
    bridge = next(n for n in found if n.node_executable == 'foxglove_bridge')
    assert isinstance(bridge.condition, IfCondition)


NAV = LAUNCH_DIRS[0] / 'navigation.launch.py'


def test_navigation_nav_argument_defaults_true() -> None:
    assert declared('navigation.launch.py')['nav'] == 'true'


def test_navigation_nav2_include_is_gated_by_nav_and_starts_on_slam_active() -> None:
    # The event handler hides its entities from walk(), so this reads the source.
    m = re.search(r"goal_state='active',\s*entities=\[IncludeLaunchDescription\("
                  r'(.*?)\)\]\)\)', NAV.read_text(), re.S)
    assert m, 'Nav2 include must sit in the slam-active OnStateTransition'
    body = m.group(1)
    assert "'navigation_launch.py'" in body
    assert "IfCondition(LaunchConfiguration('nav'))" in body


def test_navigation_nav2_uses_our_params_without_composition() -> None:
    text = NAV.read_text()
    assert "'nav2_params.yaml'" in text
    assert "'use_composition': 'False'" in text
    assert "'autostart': 'true'" in text


def test_navigation_never_uses_bringup_launch() -> None:
    # bringup_launch.py would add its own Nav2 and map server on top of ours.
    assert "bringup_launch.py'" not in NAV.read_text()


def test_navigation_localizer_defaults_to_slam() -> None:
    assert declared('navigation.launch.py')['localizer'] == 'slam'


def test_navigation_declares_and_forwards_ekf_arguments() -> None:
    d = declared('navigation.launch.py')
    assert d['ekf'] == 'true'
    assert d['ekf_params_file'].endswith('config/ekf.yaml')
    text = NAV.read_text()
    assert "'ekf': LaunchConfiguration('ekf')" in text
    assert "'ekf_params_file': LaunchConfiguration(" in text


def test_navigation_amcl_branch_is_gated_on_localizer() -> None:
    found = {n.node_executable: n for n in nodes(generate(NAV))}
    for exe in ('map_server', 'amcl', 'lifecycle_manager'):
        assert isinstance(found[exe].condition, IfCondition), exe
    slam = found['localization_slam_toolbox_node']
    assert isinstance(slam, LifecycleNode) and isinstance(slam.condition, IfCondition)
    text = NAV.read_text()
    assert "name='lifecycle_manager_localization'" in text
    assert "'node_names': ['map_server', 'amcl']" in text
    assert "' == 'slam'" in text and "' == 'amcl'" in text
    assert text.count("'navigation_launch.py'") == 2   # one per localiser


def test_base_ekf_arguments_and_defaults() -> None:
    d = declared('base.launch.py')
    assert d['ekf'] == 'true'
    assert d['ekf_params_file'].endswith('config/ekf.yaml')


def test_base_ekf_node_is_gated_by_ekf() -> None:
    found = nodes(generate(LAUNCH_DIRS[0] / 'base.launch.py'))
    ekf = next(n for n in found if n.node_package == 'robot_localization')
    assert isinstance(ekf.condition, IfCondition)


def test_base_identity_tf_replaces_the_ekf_when_ekf_false() -> None:
    found = nodes(generate(LAUNCH_DIRS[0] / 'base.launch.py'))
    tf = [n for n in found if n.node_executable == 'static_transform_publisher']
    assert len(tf) == 1 and isinstance(tf[0].condition, UnlessCondition)
    text = (LAUNCH_DIRS[0] / 'base.launch.py').read_text()
    assert "'--frame-id', 'odom', '--child-frame-id', 'base_footprint'" in text


def test_explore_dry_run_defaults_true() -> None:
    # explore_lite drives the moment it starts; live motors stay a deliberate act.
    args = {e.name: ''.join(t.text for t in e.default_value)
            for e in generate(EXPLORE).entities if isinstance(e, DeclareLaunchArgument)}
    assert args['dry_run'] == 'true'
    assert args['bridge'] == 'true'


def test_explore_slam_is_a_mapping_lifecycle_node() -> None:
    slam = [n for n in nodes(generate(EXPLORE)) if n.node_package == 'slam_toolbox']
    assert len(slam) == 1
    assert isinstance(slam[0], LifecycleNode)
    assert slam[0].node_executable == 'async_slam_toolbox_node'


def test_explore_nav2_and_explorer_start_on_slam_active() -> None:
    # The event handler hides its entities from walk(), so this reads the source.
    text = EXPLORE.read_text()
    m = re.search(r"goal_state='active',\s*entities=\[(.*?)\]\)\)", text, re.S)
    assert m, 'Nav2 and explore must sit in the slam-active OnStateTransition'
    body = m.group(1)
    assert "'navigation_launch.py'" in body
    assert "package='explore_lite'" in body
    assert "'use_composition': 'False'" in body
    assert "bringup_launch.py'" not in text  # no AMCL / map_server: slam owns /map


NAV2_PARAMS = (Path(get_package_share_directory('delivery_bot_bringup'))
               / 'config' / 'nav2_params.yaml')


@pytest.mark.parametrize('path', [NAV, EXPLORE], ids=lambda p: p.name)
def test_launch_applies_bond_timeout_from_nav2_params(path) -> None:
    # nav2_bringup does not pass params_file to its lifecycle manager, so the value
    # is read from YAML and applied with SetParameter. Reads the source (see above).
    text = path.read_text()
    assert "SetParameter(name='bond_timeout'" in text
    assert 'nav2_params.yaml' in text


def test_bond_timeout_in_yaml_is_a_float_above_the_jazzy_default() -> None:
    import yaml
    value = yaml.safe_load(NAV2_PARAMS.read_text())[
        'lifecycle_manager_navigation']['ros__parameters']['bond_timeout']
    assert isinstance(value, float)
    assert value > 4.0

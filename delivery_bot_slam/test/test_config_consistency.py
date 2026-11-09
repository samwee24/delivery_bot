"""Cross-file checks: configs, URDF and safety limits that must agree or stay capped."""

import ast
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import pytest
import xacro
import yaml

MAX_SPEED = 0.15       # AGENTS.md rule 1: v_max, do not raise casually
MAX_DUTY = 0.85
MAX_WATCHDOG_S = 0.5


def share(package: str) -> Path:
    return Path(get_package_share_directory(package))


def params(package: str, name: str, node: str) -> dict:
    return yaml.safe_load((share(package) / 'config' / name).read_text())[node]['ros__parameters']


def find_all(tree, key):
    """Every value stored under ``key`` anywhere in a nested dict."""
    if isinstance(tree, dict):
        for k, v in tree.items():
            if k == key:
                yield v
            yield from find_all(v, key)


XACRO = share('delivery_bot_description') / 'urdf' / 'delivery_bot.urdf.xacro'


def xacro_property(name: str) -> float:
    m = re.search(rf'<xacro:property\s+name="{name}"\s+value="([^"]+)"', XACRO.read_text())
    assert m, f'xacro property {name} not found in {XACRO}'
    return float(m.group(1))


@pytest.fixture(scope='module')
def urdf():
    return ET.fromstring(xacro.process_file(str(XACRO)).toxml())


@pytest.fixture(scope='module')
def nav2():
    path = share('delivery_bot_bringup') / 'config' / 'nav2_params.yaml'
    return yaml.safe_load(path.read_text())


def test_ekf_reads_the_relay_output() -> None:
    ekf = params('delivery_bot_bringup', 'ekf.yaml', 'ekf_filter_node')
    relay = params('delivery_bot_slam', 'odom_covariance.yaml', 'odom_covariance_relay')
    assert ekf['odom0'] == relay['output_topic']
    assert ekf['odom0'] != '/odom_rf2o'   # raw rf2o has a zero twist covariance


def test_ekf_frames_and_tf_ownership() -> None:
    ekf = params('delivery_bot_bringup', 'ekf.yaml', 'ekf_filter_node')
    assert ekf['imu0'] == '/imu/data'
    assert ekf['base_link_frame'] == 'base_footprint'
    assert ekf['publish_tf'] is True   # the EKF is the only odom -> base_footprint publisher


def test_wheel_base_matches_urdf() -> None:
    motor = params('delivery_bot_drivers', 'drivers.yaml', 'motor_node')
    assert motor['wheel_base'] == xacro_property('wheel_base')


def test_costmap_radius_matches_urdf(nav2, urdf) -> None:
    local = nav2['local_costmap']['local_costmap']['ros__parameters']['robot_radius']
    glob = nav2['global_costmap']['global_costmap']['ros__parameters']['robot_radius']
    assert local == glob == xacro_property('robot_radius')
    # the expanded URDF must actually use the property
    cylinder = urdf.find("./link[@name='base_link']/visual/geometry/cylinder")
    assert float(cylinder.get('radius')) == xacro_property('robot_radius')


def test_collision_monitor_zones(nav2) -> None:
    cm = nav2['collision_monitor']['ros__parameters']
    assert {'stop', 'slowdown', 'approach'} <= set(cm['polygons'])
    stop_reach = max(x for x, _ in ast.literal_eval(cm['stop']['points']))
    slow_reach = max(x for x, _ in ast.literal_eval(cm['slowdown']['points']))
    assert stop_reach == 0.20          # E4 baseline, not re-tuned
    assert slow_reach > stop_reach
    assert 0 < cm['slowdown']['slowdown_ratio'] < 1
    local = nav2['local_costmap']['local_costmap']['ros__parameters']['robot_radius']
    assert cm['approach']['radius'] == local
    assert cm['approach']['time_before_collision'] > 0
    assert all(cm[name]['enabled'] is True for name in cm['polygons'])
    # Jazzy's string parser rejects fewer than 4 vertices (`vvf.size() <= 3`).
    for name in ('stop', 'slowdown'):
        assert len(ast.literal_eval(cm[name]['points'])) >= 4


def test_nav2_speed_cap(nav2) -> None:
    desired = list(find_all(nav2, 'desired_linear_vel'))
    limits = list(find_all(nav2, 'max_velocity'))
    assert desired and limits, 'speed keys not found, the test is looking in the wrong place'
    assert all(v <= MAX_SPEED for v in desired)
    assert all(v[0] <= MAX_SPEED for v in limits)   # [linear x, linear y, angular]


def test_slam_mapping_and_localization_agree() -> None:
    mapping = params('delivery_bot_bringup', 'slam_mapping.yaml', 'slam_toolbox')
    localization = params('delivery_bot_bringup', 'slam_localization.yaml', 'slam_toolbox')
    for key in ('base_frame', 'odom_frame', 'map_frame', 'resolution',
                'min_laser_range', 'max_laser_range', 'ceres_loss_function'):
        assert mapping[key] == localization[key], key


def test_slam_modes() -> None:
    mapping = params('delivery_bot_bringup', 'slam_mapping.yaml', 'slam_toolbox')
    localization = params('delivery_bot_bringup', 'slam_localization.yaml', 'slam_toolbox')
    assert mapping['mode'] == 'mapping'
    assert localization['mode'] == 'localization'
    assert 'map_file_name' not in localization   # supplied by the launch argument


def test_configured_frames_exist_in_urdf(urdf) -> None:
    links = {link.get('name') for link in urdf.iter('link')}
    lidar_launch = (share('delivery_bot_bringup') / 'launch' / 'lidar.launch.py').read_text()
    lidar_frame = re.search(
        r"DeclareLaunchArgument\('frame_id',\s*default_value='([^']+)'", lidar_launch).group(1)
    imu = params('delivery_bot_drivers', 'drivers.yaml', 'imu_node')
    ekf = params('delivery_bot_bringup', 'ekf.yaml', 'ekf_filter_node')
    slam = params('delivery_bot_bringup', 'slam_mapping.yaml', 'slam_toolbox')
    explore = params('delivery_bot_slam', 'explore.yaml', 'explore_node')
    configured = {
        ekf['base_link_frame'], slam['base_frame'], explore['robot_base_frame'],
        imu.get('frame_id', 'imu_link'),   # imu_node's declared default
        lidar_frame,
    }
    assert configured == {'base_footprint', 'imu_link', 'laser'}
    assert configured <= links


def test_explore_base_frame() -> None:
    explore = params('delivery_bot_slam', 'explore.yaml', 'explore_node')
    assert explore['robot_base_frame'] == 'base_footprint'


def test_motor_safety_limits_do_not_grow() -> None:
    motor = params('delivery_bot_drivers', 'drivers.yaml', 'motor_node')
    assert motor['max_duty'] <= MAX_DUTY
    assert motor['watchdog_s'] <= MAX_WATCHDOG_S
    assert isinstance(motor['dry_run'], bool)   # launch overrides it to true


STAMPED_NODES = ['controller_server', 'velocity_smoother', 'collision_monitor', 'behavior_server']


def test_nav2_nodes_that_set_stamped_cmd_vel_set_it_true(nav2) -> None:
    # motor_node subscribes /cmd_vel as TwistStamped only
    for node, block in nav2.items():
        value = block.get('ros__parameters', {}).get('enable_stamped_cmd_vel', True)
        assert value is True, f'{node}: enable_stamped_cmd_vel must be true'


@pytest.mark.parametrize('node', STAMPED_NODES)
def test_nav2_cmd_vel_chain_is_stamped(nav2, node) -> None:
    assert nav2[node]['ros__parameters']['enable_stamped_cmd_vel'] is True

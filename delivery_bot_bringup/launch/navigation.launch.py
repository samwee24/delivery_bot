"""Navigation mode: base stack + slam_toolbox localization + Nav2.

Nav2's navigation_launch.py is used (not bringup_launch.py): bringup_launch
would start AMCL and map_server, and slam_toolbox localization already supplies
both the map and map -> odom.

The map argument is the serialised graph produced by mapping.launch.py, without
an extension (slam_toolbox appends .posegraph/.data). It must reach the node as the
`map_file_name` parameter: do not include slam_toolbox's own localization_launch.py,
which only forwards `slam_params_file` and would silently drop the map.

The start pose is not a launch argument. It is set over /initialpose from Foxglove
(the 3D panel's "Publish pose estimate"), which slam_toolbox listens for in
localization mode and uses to anchor map -> odom.

Expected: include base.launch.py, then slam_toolbox localization mode with
config/slam_localization.yaml, then nav2_bringup/navigation_launch.py with
config/nav2_params.yaml, passing the map argument through.

slam_toolbox is a lifecycle node (`unconfigured` until told otherwise), so it must be
a launch_ros.actions.LifecycleNode driven by ChangeState(TRANSITION_CONFIGURE) and,
on reaching `inactive`, ChangeState(TRANSITION_ACTIVATE). A plain Node starts, looks
healthy, and publishes no /map, no map -> odom and no error. Pass
`use_lifecycle_manager: false` and forward `use_sim_time` to the slam_toolbox node.
Background: docs/slam.md §3.1.

Nav2 starts only once slam_toolbox is `active`, so its costmaps find /map and
map -> odom. `nav:=false` gives the localisation-only stack (build path 6.2).
Nav2 runs without composition (no container to load into) and autostarts.

Arguments added for the live experiments (docs/report_plan.md): `ekf` and
`ekf_params_file` go to base.launch.py (E2 odometry configs); `localizer` is `slam`
(default, as above) or `amcl` (E3): then slam_toolbox is not started, and nav2_map_server
(`map_yaml`, the occupancy grid), nav2_amcl (config/amcl.yaml) and a localisation
lifecycle manager are. Nav2 starts 5 s after that lifecycle manager, which has no
state transition event to wait on. The default behaviour is unchanged.

Build path: task 6.2 in docs/slam_build_path.md
"""

import os

import launch
import lifecycle_msgs.msg
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent,
                            IncludeLaunchDescription, RegisterEventHandler,
                            TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import LifecycleNode, Node, SetParameter
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState


def generate_launch_description() -> LaunchDescription:
    bringup = get_package_share_directory('delivery_bot_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time')
    localizer = LaunchConfiguration('localizer')
    is_slam = IfCondition(PythonExpression(["'", localizer, "' == 'slam'"]))
    is_amcl = IfCondition(PythonExpression(["'", localizer, "' == 'amcl'"]))
    nav2_params = os.path.join(bringup, 'config', 'nav2_params.yaml')
    with open(nav2_params) as f:
        bond_timeout = yaml.safe_load(f)['lifecycle_manager_navigation'][
            'ros__parameters']['bond_timeout']
    nav2_args = {
        'params_file': nav2_params,
        'use_sim_time': use_sim_time,
        'autostart': 'true',
        'use_composition': 'False'}

    slam = LifecycleNode(
        package='slam_toolbox', executable='localization_slam_toolbox_node',
        name='slam_toolbox', namespace='', output='screen', condition=is_slam,
        parameters=[
            os.path.join(bringup, 'config', 'slam_localization.yaml'),
            {'use_lifecycle_manager': False, 'use_sim_time': use_sim_time,
             'map_file_name': LaunchConfiguration('map'),
             # = home in goals.yaml, the taped mark. Moved 2026-11-10 from the map
             # origin (0.21 m clearance) to 0.67 m clearance; map_start_at_dock is
             # rejected in localisation mode. Yaw 2.635 = 151 deg, parallel to the walls either side
             'map_start_pose': [-1.3, -0.3, 2.635]}])
    configure = EmitEvent(event=ChangeState(
        lifecycle_node_matcher=launch.events.matches_action(slam),
        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE),
        condition=is_slam)
    activate = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=slam, start_state='configuring',
        goal_state='inactive',
        entities=[EmitEvent(event=ChangeState(
            lifecycle_node_matcher=launch.events.matches_action(slam),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE))]))
    nav2 = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=slam, goal_state='active',
        entities=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch', 'navigation_launch.py')),
            launch_arguments=nav2_args.items(),
            condition=launch.conditions.IfCondition(LaunchConfiguration('nav')))]))
    amcl_stack = [
        Node(package='nav2_map_server', executable='map_server', name='map_server',
             output='screen', condition=is_amcl,
             parameters=[{'yaml_filename': LaunchConfiguration('map_yaml'),
                          'use_sim_time': use_sim_time}]),
        Node(package='nav2_amcl', executable='amcl', name='amcl', output='screen',
             condition=is_amcl,
             parameters=[os.path.join(bringup, 'config', 'amcl.yaml'),
                         {'use_sim_time': use_sim_time}]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_localization', output='screen', condition=is_amcl,
             parameters=[{'autostart': True, 'node_names': ['map_server', 'amcl'],
                          'use_sim_time': use_sim_time}]),
        TimerAction(period=5.0, actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch', 'navigation_launch.py')),
            launch_arguments=nav2_args.items(),
            condition=IfCondition(PythonExpression(
                ["'", LaunchConfiguration('nav'), "' == 'true' and '", localizer,
                 "' == 'amcl'"])))]),
    ]

    return LaunchDescription([
        # navigation_launch.py does not pass params_file to its lifecycle manager
        SetParameter(name='bond_timeout', value=float(bond_timeout)),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('nav', default_value='true'),
        DeclareLaunchArgument('bridge', default_value='true'),
        DeclareLaunchArgument('dry_run', default_value='true'),   # motors; base.launch.py
        DeclareLaunchArgument('include_base', default_value='true'),
        DeclareLaunchArgument('localizer', default_value='slam'),   # slam | amcl
        DeclareLaunchArgument('ekf', default_value='true'),
        DeclareLaunchArgument('ekf_params_file', default_value=os.path.join(
            bringup, 'config', 'ekf.yaml')),
        DeclareLaunchArgument('map_yaml', default_value=os.path.expanduser(
            '~/maps/2026-10-31_room2.yaml')),
        DeclareLaunchArgument('map', default_value=os.path.expanduser(
            '~/maps/2026-10-31_room2_graph')),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(bringup, 'launch', 'base.launch.py')),
            launch_arguments={'use_sim_time': use_sim_time,
                              'bridge': LaunchConfiguration('bridge'),
                              'dry_run': LaunchConfiguration('dry_run'),
                              'ekf': LaunchConfiguration('ekf'),
                              'ekf_params_file': LaunchConfiguration(
                                  'ekf_params_file')}.items(),
            condition=launch.conditions.IfCondition(
                LaunchConfiguration('include_base'))),
        slam, activate, nav2, *amcl_stack,
        # configure is not retried if sent before the lifecycle services exist
        TimerAction(period=5.0, actions=[configure]),
    ])

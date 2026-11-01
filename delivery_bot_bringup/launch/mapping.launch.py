"""Mapping mode: base stack + slam_toolbox online async mapping.

Saving the map (run while this launch is up):

    # occupancy grid + yaml, straight into the repo (symlink-install makes the
    # installed share directory the source directory):
    ros2 run nav2_map_server map_saver_cli -f \
      ~/ros2_ws/src/delivery_bot/delivery_bot_bringup/maps/room

    # serialised graph, required by navigation.launch.py (localization mode):
    ros2 service call /slam_toolbox/serialize_map \
      slam_toolbox/srv/SerializePoseGraph \
      "{filename: '$HOME/ros2_ws/src/delivery_bot/delivery_bot_bringup/maps/room'}"

slam_toolbox's serialize_map writes room.posegraph and room.data next to the
given filename.

Expected: include base.launch.py, then slam_toolbox's async node with
config/slam_mapping.yaml (online_async; the map frame is published by slam_toolbox).
That node must be a launch_ros.actions.LifecycleNode, not a plain Node: start it with
ChangeState(TRANSITION_CONFIGURE) and, on reaching `inactive`,
ChangeState(TRANSITION_ACTIVATE). slam_toolbox 2.8.5 stays `unconfigured` otherwise —
a plain Node starts, looks healthy, and produces no /map, no map -> odom and no error
to explain why. Pass `use_lifecycle_manager: false` (the launch file drives the
transitions itself) and forward `use_sim_time` to the same node. Background:
docs/slam.md §3.1.

Build path: task 5.3 in docs/slam_build_path.md
"""

import os

import launch
import lifecycle_msgs.msg
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent,
                            IncludeLaunchDescription, RegisterEventHandler,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState


def generate_launch_description() -> LaunchDescription:
    bringup = get_package_share_directory('delivery_bot_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time')

    slam = LifecycleNode(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        output='screen',
        parameters=[
            os.path.join(bringup, 'config', 'slam_mapping.yaml'),
            {'use_lifecycle_manager': False, 'use_sim_time': use_sim_time},
        ],
    )
    configure = EmitEvent(event=ChangeState(
        lifecycle_node_matcher=launch.events.matches_action(slam),
        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE))
    activate = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=slam,
        start_state='configuring', goal_state='inactive',
        entities=[EmitEvent(event=ChangeState(
            lifecycle_node_matcher=launch.events.matches_action(slam),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE))]))

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        # false lets a bag replay supply its own tf and sensors (build path 5.3).
        DeclareLaunchArgument('include_base', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(bringup, 'launch', 'base.launch.py')),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
            condition=IfCondition(LaunchConfiguration('include_base'))),
        slam,
        activate,
        # /run/save: map + pose graph + configs under one dated name
        Node(package='delivery_bot_slam', executable='run_save', output='screen'),
        # configure fails (and is never retried) if sent before the node's lifecycle
        # services exist; with include_base:=false slam is the only process, so wait.
        TimerAction(period=5.0, actions=[configure]),
    ])

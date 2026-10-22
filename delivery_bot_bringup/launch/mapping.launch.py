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
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    bringup = get_package_share_directory("delivery_bot_bringup")
    params_file = LaunchConfiguration("params_file")
    dry_run = LaunchConfiguration("dry_run")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=os.path.join(bringup, "config", "slam_mapping.yaml"),
            ),
            DeclareLaunchArgument(
                "dry_run",
                default_value="true",
                description="false only when the robot is on the floor and watched",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup, "launch", "base.launch.py")
                ),
                launch_arguments={"dry_run": dry_run}.items(),
            ),
            Node(
                package="slam_toolbox",
                executable="async_slam_toolbox_node",
                name="slam_toolbox",
                output="screen",
                parameters=[params_file],
            ),
        ]
    )

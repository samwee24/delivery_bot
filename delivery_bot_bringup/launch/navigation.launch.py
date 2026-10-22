"""Navigation mode: base stack + slam_toolbox localization + Nav2.

Nav2's navigation_launch.py is used (not bringup_launch.py): bringup_launch
would start AMCL and map_server, and slam_toolbox localization already supplies
both the map and map -> odom.

The map argument is the serialised graph produced by mapping.launch.py, without
an extension (slam_toolbox appends .posegraph/.data).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    bringup = get_package_share_directory("delivery_bot_bringup")
    nav2_bringup = get_package_share_directory("nav2_bringup")

    slam_params = LaunchConfiguration("slam_params_file")
    nav2_params = LaunchConfiguration("params_file")
    map_file = LaunchConfiguration("map")
    dry_run = LaunchConfiguration("dry_run")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "slam_params_file",
                default_value=os.path.join(
                    bringup, "config", "slam_localization.yaml"
                ),
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=os.path.join(bringup, "config", "nav2_params.yaml"),
            ),
            DeclareLaunchArgument(
                "map",
                default_value=os.path.join(bringup, "maps", "room"),
                description="serialised slam_toolbox map, without extension",
            ),
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup, "launch", "base.launch.py")
                ),
                launch_arguments={
                    "dry_run": dry_run,
                    "use_sim_time": use_sim_time,
                }.items(),
            ),
            # Localization mode: map frozen, pose tracked against it. The start
            # pose is the map origin until someone sets it with the Foxglove
            # "Publish pose" panel or save_goal/initial pose on the robot.
            Node(
                package="slam_toolbox",
                executable="localization_slam_toolbox_node",
                name="slam_toolbox",
                output="screen",
                parameters=[
                    slam_params,
                    {"map_file_name": map_file, "map_start_pose": [0.0, 0.0, 0.0]},
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav2_bringup, "launch", "navigation_launch.py")
                ),
                launch_arguments={
                    "params_file": nav2_params,
                    "use_sim_time": use_sim_time,
                }.items(),
            ),
        ]
    )

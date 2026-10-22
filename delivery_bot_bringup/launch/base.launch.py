"""Base stack that both mapping and navigation build on.

Order of ownership for tf matters:
  odom -> base_footprint is published by the EKF only (rf2o has publish_tf
  false), because two publishers of one transform make the map spin.

Motors default to dry_run: the launch argument exists so live testing is a
deliberate act, never a default.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    description = get_package_share_directory("delivery_bot_description")
    drivers = get_package_share_directory("delivery_bot_drivers")
    bringup = get_package_share_directory("delivery_bot_bringup")

    urdf_path = os.path.join(description, "urdf", "delivery_bot.urdf.xacro")
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", urdf_path]), value_type=str
    )

    dry_run = LaunchConfiguration("dry_run")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "dry_run",
                default_value="true",
                description="true = compute and log duties without touching GPIO",
            ),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": ParameterValue(
                            use_sim_time, value_type=bool
                        ),
                    }
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup, "launch", "lidar.launch.py")
                )
            ),
            Node(
                package="delivery_bot_drivers",
                executable="imu_node",
                output="screen",
                parameters=[
                    os.path.join(drivers, "config", "drivers.yaml"),
                    {"use_sim_time": ParameterValue(use_sim_time, value_type=bool)},
                ],
            ),
            Node(
                package="delivery_bot_drivers",
                executable="motor_node",
                output="screen",
                parameters=[
                    os.path.join(drivers, "config", "drivers.yaml"),
                    {
                        "dry_run": ParameterValue(dry_run, value_type=bool),
                        "use_sim_time": ParameterValue(
                            use_sim_time, value_type=bool
                        ),
                    },
                ],
            ),
            # rf2o turns scans into a velocity estimate. publish_tf must stay
            # false: the EKF owns odom -> base_footprint.
            Node(
                package="rf2o_laser_odometry",
                executable="rf2o_laser_odometry_node",
                name="rf2o_laser_odometry",
                output="screen",
                parameters=[
                    {
                        "laser_scan_topic": "/scan",
                        "odom_topic": "/odom_rf2o",
                        "publish_tf": False,
                        "base_frame_id": "base_footprint",
                        "odom_frame_id": "odom",
                        "init_pose_from_topic": "",
                        "freq": 10.0,
                    }
                ],
            ),
            Node(
                package="robot_localization",
                executable="ekf_node",
                name="ekf_filter_node",
                output="screen",
                parameters=[
                    os.path.join(bringup, "config", "ekf.yaml"),
                    {"use_sim_time": ParameterValue(use_sim_time, value_type=bool)},
                ],
            ),
            Node(
                package="foxglove_bridge",
                executable="foxglove_bridge",
                name="foxglove_bridge",
                output="screen",
                parameters=[{"port": 8765, "address": "0.0.0.0"}],
            ),
        ]
    )

"""Base stack that both mapping and navigation build on.

Order of ownership for tf matters:
  odom -> base_footprint is published by the EKF only (rf2o has publish_tf
  false), because two publishers of one transform make the map spin.

Motors are live: motor_node is always started and drives the wheels from
/cmd_vel. dry_run (default false) is still passed to it, but motor_node has no
dry run and ignores it. The motor battery switch is the kill switch.

What this file is expected to start (see docs/07_ros_stack.md):

  robot_state_publisher          URDF from delivery_bot_description, xacro
  rplidar_node                   /scan, on /dev/rplidar at 115200
  rf2o_laser_odometry            /scan -> /odom_rf2o, publish_tf false
  imu_node                       /imu/data, from delivery_bot_drivers
  odom_covariance_relay          /odom_rf2o ->
                                 /odom_rf2o_cov (delivery_bot_slam)
  ekf_filter_node                robot_localization, config/ekf.yaml
  motor_node                     /cmd_vel -> L298N GPIO, config/drivers.yaml,
                                 20 Hz control, 0.5 s watchdog; always live
  foxglove_bridge                port 8765

Launch arguments: dry_run (default false, ignored by motor_node), motor
(default true, not used by any action yet), bridge (true), use_sim_time
(false), serial_port (/dev/rplidar), rf2o_delay (2.0 s).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    bringup = get_package_share_directory('delivery_bot_bringup')
    drivers = get_package_share_directory('delivery_bot_drivers')
    slam_pkg = get_package_share_directory('delivery_bot_slam')
    urdf = os.path.join(
                    get_package_share_directory('delivery_bot_description'),
                    'urdf', 'delivery_bot.urdf.xacro')
    sim = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        # motors are ok, no dry run
        DeclareLaunchArgument('dry_run', default_value='false'),
        # false when robot_control.py already runs the one bridge (port 8765)
        DeclareLaunchArgument('bridge', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('serial_port', default_value='/dev/rplidar'),
        # rf2o reads base_footprint -> laser once, on the first scan, so the
        # static tree must be up first (build path 3.4).
        DeclareLaunchArgument('rf2o_delay', default_value='2.0'),
        DeclareLaunchArgument('motor', default_value='true'),
        Node(package='robot_state_publisher',
             executable='robot_state_publisher',
             parameters=[{'use_sim_time': sim, 'robot_description':
                          ParameterValue(
                             Command(['xacro ', urdf]), value_type=str)}]),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(bringup, 'launch', 'lidar.launch.py')),
            launch_arguments={'serial_port':
                              LaunchConfiguration('serial_port')}.items()),
        TimerAction(
            period=LaunchConfiguration('rf2o_delay'),
            actions=[Node(
                package='rf2o_laser_odometry',
                executable='rf2o_laser_odometry_node',
                name='rf2o_laser_odometry', output='screen',
                parameters=[{
                    'laser_scan_topic': '/scan', 'odom_topic': '/odom_rf2o',
                    'publish_tf': False,  # the EKF owns odom -> base_footprint
                    'base_frame_id': 'base_footprint', 'odom_frame_id': 'odom',
                    'init_pose_from_topic': '', 'freq': 20.0,
                    'use_sim_time': sim}])]),
        Node(package='delivery_bot_slam', executable='odom_covariance_relay',
             name='odom_covariance_relay', output='screen',
             parameters=[os.path.join(slam_pkg, 'config',
                                      'odom_covariance.yaml'),
                         {'use_sim_time': sim}]),
        Node(package='delivery_bot_drivers', executable='imu_node',
             name='imu_node', output='screen',
             parameters=[os.path.join(drivers, 'config', 'drivers.yaml'),
                         {'use_sim_time': sim}]),
        Node(package='delivery_bot_drivers', executable='motor_node',
             name='motor_node', output='screen',
             parameters=[os.path.join(drivers, 'config', 'drivers.yaml'),
                         {'dry_run': ParameterValue(
                             LaunchConfiguration('dry_run'),
                             value_type=bool),
                         'use_sim_time': sim}]),
        Node(package='robot_localization', executable='ekf_node',
             name='ekf_filter_node', output='screen',
             parameters=[os.path.join(bringup, 'config', 'ekf.yaml'),
                         {'use_sim_time': sim}]),
        Node(package='foxglove_bridge', executable='foxglove_bridge',
             parameters=[{'use_sim_time': sim}],
             condition=IfCondition(LaunchConfiguration('bridge')))
    ])

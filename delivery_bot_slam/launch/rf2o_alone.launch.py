"""
Build path 3.2 / 3.4 experiment: lidar + URDF + rf2o, no EKF.

NOT the real stack. rf2o runs here with ``publish_tf: true`` because nothing else
publishes odom -> base_footprint; in the real stack the EKF owns that transform
and rf2o runs with ``publish_tf: false``.

rf2o is started ``rf2o_delay`` seconds after robot_state_publisher: it reads
base_footprint -> laser once, on the first scan, so the static tree must already
be up (build path 3.4). ``rf2o_delay:=0`` reproduces the race.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    urdf = os.path.join(get_package_share_directory('delivery_bot_description'),
                        'urdf', 'delivery_bot.urdf.xacro')
    lidar = os.path.join(get_package_share_directory('delivery_bot_bringup'),
                         'launch', 'lidar.launch.py')
    return LaunchDescription([
        DeclareLaunchArgument('rf2o_delay', default_value='2.0'),
        DeclareLaunchArgument('serial_port', default_value='/dev/rplidar'),
        DeclareLaunchArgument('angle_compensate', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lidar),
            launch_arguments={
                'serial_port': LaunchConfiguration('serial_port'),
                'angle_compensate': LaunchConfiguration('angle_compensate')}.items()),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': ParameterValue(
                 Command(['xacro ', urdf]), value_type=str)}]),
        TimerAction(
            period=LaunchConfiguration('rf2o_delay'),
            actions=[Node(
                package='rf2o_laser_odometry', executable='rf2o_laser_odometry_node',
                name='rf2o_laser_odometry', output='screen',
                parameters=[{
                    'laser_scan_topic': '/scan',
                    'odom_topic': '/odom_rf2o',
                    'publish_tf': True,
                    'base_frame_id': 'base_footprint',
                    'odom_frame_id': 'odom',
                    'init_pose_from_topic': '',
                    'freq': 20.0}])]),
    ])

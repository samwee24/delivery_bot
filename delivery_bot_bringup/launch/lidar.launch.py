"""RPLidar A1M8 driver.

In Jazzy the apt package provides the ``rplidar_composition`` executable (the
node is a component, but it runs fine standalone). Its parameters were checked
on the robot with strings(1): serial_port, serial_baudrate, frame_id, inverted,
angle_compensate, scan_mode, channel_type, topic_name.

Expected arguments: serial_port (default /dev/rplidar), serial_baudrate
(115200), frame_id (laser).

The udev rule that creates /dev/rplidar is in docs/pi_setup.md; if the symlink
is missing, /dev/ttyUSB0 works until it is fixed.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument('serial_port', default_value='/dev/rplidar'),
        DeclareLaunchArgument('serial_baudrate', default_value='115200'),
        DeclareLaunchArgument('frame_id', default_value='laser'),
        # false restores the driver's varying beam count (about 1045); only for the rf2o scale test
        DeclareLaunchArgument('angle_compensate', default_value='true'),
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='screen',
            parameters=[{
                'serial_port': LaunchConfiguration('serial_port'),
                # LaunchConfiguration is a string; the node wants an int.
                'serial_baudrate': ParameterValue(
                    LaunchConfiguration('serial_baudrate'), value_type=int),
                'frame_id': LaunchConfiguration('frame_id'),
                # Fixed beam count per scan: slam_toolbox drops every scan whose
                # count differs from the first one (seen 2026-10-31: 1032-1046 vs 931).
                'angle_compensate': ParameterValue(
                    LaunchConfiguration('angle_compensate'), value_type=bool),
            }],
        ),
    ])

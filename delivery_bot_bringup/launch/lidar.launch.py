"""RPLidar A1M8 driver.

In Jazzy the apt package provides the ``rplidar_composition`` executable (the
node is a component, but it runs fine standalone). Its parameters were checked
on the robot with strings(1): serial_port, serial_baudrate, frame_id, inverted,
angle_compensate, scan_mode, channel_type, topic_name.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    serial_port = LaunchConfiguration("serial_port")
    serial_baudrate = LaunchConfiguration("serial_baudrate")
    frame_id = LaunchConfiguration("frame_id")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "serial_port",
                default_value="/dev/rplidar",
                description="udev alias is preferred over /dev/ttyUSB0",
            ),
            DeclareLaunchArgument("serial_baudrate", default_value="115200"),
            DeclareLaunchArgument("frame_id", default_value="laser"),
            Node(
                package="rplidar_ros",
                executable="rplidar_composition",
                name="rplidar_node",
                output="screen",
                parameters=[
                    {
                        "channel_type": "serial",
                        "serial_port": serial_port,
                        "serial_baudrate": ParameterValue(
                            serial_baudrate, value_type=int
                        ),
                        "frame_id": frame_id,
                        "inverted": False,
                        "angle_compensate": True,
                        "scan_mode": "Standard",
                        "topic_name": "scan",
                    }
                ],
            ),
        ]
    )

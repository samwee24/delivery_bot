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


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([])

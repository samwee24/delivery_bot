"""USB camera (UGREEN camera 2K) via usb_cam.

Publishes /image_raw and, through image_transport, /image_raw/compressed. The
Foxglove bridge shows the compressed topic in an Image panel. Parameters are in
config/camera.yaml.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config = os.path.join(
        get_package_share_directory('delivery_bot_bringup'), 'config', 'camera.yaml')
    return LaunchDescription([
        Node(package='usb_cam', executable='usb_cam_node_exe', name='camera',
             output='screen', parameters=[config]),
    ])

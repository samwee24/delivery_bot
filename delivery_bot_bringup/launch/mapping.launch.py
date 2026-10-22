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

Expected: include base.launch.py, then slam_toolbox/slam_toolbox.py with
config/slam_mapping.yaml (online_async, map frame published by slam_toolbox).
"""

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([])

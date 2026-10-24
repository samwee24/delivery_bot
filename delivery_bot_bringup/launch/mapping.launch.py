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

Expected: include base.launch.py, then slam_toolbox's async node with
config/slam_mapping.yaml (online_async; the map frame is published by slam_toolbox).
That node must be a launch_ros.actions.LifecycleNode, not a plain Node: start it with
ChangeState(TRANSITION_CONFIGURE) and, on reaching `inactive`,
ChangeState(TRANSITION_ACTIVATE). slam_toolbox 2.8.5 stays `unconfigured` otherwise —
a plain Node starts, looks healthy, and produces no /map, no map -> odom and no error
to explain why. Pass `use_lifecycle_manager: false` (the launch file drives the
transitions itself) and forward `use_sim_time` to the same node. Background:
docs/slam.md §3.1.

Build path: task 5.3 in docs/slam_build_path.md
"""

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([])

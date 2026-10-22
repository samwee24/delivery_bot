"""Navigation mode: base stack + slam_toolbox localization + Nav2.

Nav2's navigation_launch.py is used (not bringup_launch.py): bringup_launch
would start AMCL and map_server, and slam_toolbox localization already supplies
both the map and map -> odom.

The map argument is the serialised graph produced by mapping.launch.py, without
an extension (slam_toolbox appends .posegraph/.data).

Expected: include base.launch.py, then slam_toolbox localization mode with
config/slam_localization.yaml, then nav2_bringup/navigation_launch.py with
config/nav2_params.yaml, passing the map argument through.
"""

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([])

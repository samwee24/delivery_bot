"""Navigation mode: base stack + slam_toolbox localization + Nav2.

Nav2's navigation_launch.py is used (not bringup_launch.py): bringup_launch
would start AMCL and map_server, and slam_toolbox localization already supplies
both the map and map -> odom.

The map argument is the serialised graph produced by mapping.launch.py, without
an extension (slam_toolbox appends .posegraph/.data). It must reach the node as the
`map_file_name` parameter: do not include slam_toolbox's own localization_launch.py,
which only forwards `slam_params_file` and would silently drop the map.

The start pose is not a launch argument. It is set over /initialpose from Foxglove
(the 3D panel's "Publish pose estimate"), which slam_toolbox listens for in
localization mode and uses to anchor map -> odom.

Expected: include base.launch.py, then slam_toolbox localization mode with
config/slam_localization.yaml, then nav2_bringup/navigation_launch.py with
config/nav2_params.yaml, passing the map argument through.

slam_toolbox is a lifecycle node (`unconfigured` until told otherwise), so it must be
a launch_ros.actions.LifecycleNode driven by ChangeState(TRANSITION_CONFIGURE) and,
on reaching `inactive`, ChangeState(TRANSITION_ACTIVATE). A plain Node starts, looks
healthy, and publishes no /map, no map -> odom and no error. Pass
`use_lifecycle_manager: false` and forward `use_sim_time` to the slam_toolbox node.
Background: docs/slam.md §3.1.
"""

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([])

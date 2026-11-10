"""
Autonomous mapping: base stack, slam_toolbox, Nav2, explore_lite.

STOP AND READ: explore_lite starts driving as soon as it launches.

There is no start-paused option. Its first timer tick picks a frontier and
sends a goal through Nav2, and the robot moves. Launch it deliberately: robot
on the floor, wheels clear, someone watching, physical motor switch within
reach. Nothing in this file pauses it for you.

Pause without killing the node:

    ros2 topic pub --once /explore/resume std_msgs/msg/Bool "{data: false}"

The same message with ``true`` resumes. The Foxglove publish panel does the
same job. explore_lite reads ``/explore/resume`` on every tick, so one message
is enough.

Prerequisite: a reliable Nav2. explore_lite plans nothing and controls
nothing; it only asks Nav2 for goals and watches a costmap. If Nav2 cannot
reach a goal, exploration stalls at "goal failed" and the robot stops -- that
is a Nav2 fault, not an exploration one. Get Nav2 right first (that section of
the project belongs to the navigation work, not this file).

What this file starts
---------------------
1. ``delivery_bot_bringup/launch/base.launch.py``, forwarding ``use_sim_time``
   and ``dry_run``. ``dry_run`` stays true by default: live motors remain a
   deliberate act.
2. slam_toolbox as a ``LifecycleNode``, not a plain ``Node``:
       package     slam_toolbox
       executable  async_slam_toolbox_node
       name        slam_toolbox
       parameters  delivery_bot_bringup/config/slam_mapping.yaml, with
                   ``map_update_interval: 2.0`` (the file says 5.0; frontiers
                   need a fresher /map than a mapping demo does) and
                   ``use_lifecycle_manager: false`` (this file drives the
                   transitions itself; an external manager would fight it)
       then  ChangeState(TRANSITION_CONFIGURE)
       then  RegisterEventHandler(
                 OnStateTransition(goal_state='inactive')
                 -> ChangeState(TRANSITION_ACTIVATE))

   Why the LifecycleNode: in slam_toolbox 2.8.5 (the version on the Pi) a
   plain ``Node`` leaves the underlying lifecycle node unconfigured. It starts,
   logs nothing alarming, and simply never publishes ``/map`` or
   ``map -> odom``. Wrapping it and driving configure -> activate by hand is
   the fix; the ``inactive`` event is the only reliable trigger for activation,
   because configure is asynchronous.
3. ``nav2_bringup/launch/navigation_launch.py`` with the existing unchanged
   ``delivery_bot_bringup/config/nav2_params.yaml``, forwarding
   ``use_sim_time``. Not ``bringup_launch.py``: slam_toolbox supplies the map
   and ``map -> odom``, so AMCL and map_server must stay out.
4. explore_lite's ``explore`` node with ``delivery_bot_slam/config/explore.yaml``.
   That config reads ``/global_costmap/costmap`` rather than ``/map`` so
   frontiers stop hugging walls, and sets ``return_to_init: true`` so the robot
   drives home and the return-to-start error can be measured.

Launch arguments
    ``use_sim_time``  default false, forwarded to base, slam_toolbox, Nav2 and
                      explore_lite
    ``dry_run``       default true, forwarded to base.launch.py
    ``bridge``        default true; robot_control.py passes false when it runs
                      the one bridge on 8765

Acceptance test
    ``ros2 lifecycle get /slam_toolbox`` reports ``active``;
    ``ros2 topic echo /map --once`` returns a grid;
    ``ros2 run tf2_ros tf2_echo map base_footprint`` resolves;
    ``ros2 topic echo /explore/frontiers --once`` shows markers once the
    costmap has grown. With the robot on the floor the wheels start turning
    within a few seconds -- which is exactly why the warning is first.

Build path: task 8.3 in docs/slam_build_path.md
"""

import os

from ament_index_python.packages import get_package_share_directory
import launch
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent,
                            IncludeLaunchDescription, RegisterEventHandler,
                            TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node, SetParameter
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
import lifecycle_msgs.msg
import yaml


def generate_launch_description() -> LaunchDescription:
    bringup = get_package_share_directory('delivery_bot_bringup')
    slam_pkg = get_package_share_directory('delivery_bot_slam')
    use_sim_time = LaunchConfiguration('use_sim_time')
    nav2_params = os.path.join(bringup, 'config', 'nav2_params.yaml')
    with open(nav2_params) as f:
        bond_timeout = yaml.safe_load(f)['lifecycle_manager_navigation'][
            'ros__parameters']['bond_timeout']

    slam = LifecycleNode(
        package='slam_toolbox', executable='async_slam_toolbox_node',
        name='slam_toolbox', namespace='', output='screen',
        parameters=[
            os.path.join(bringup, 'config', 'slam_mapping.yaml'),
            {'map_update_interval': 2.0,  # frontiers need a fresher /map
             'use_lifecycle_manager': False, 'use_sim_time': use_sim_time}])
    configure = EmitEvent(event=ChangeState(
        lifecycle_node_matcher=launch.events.matches_action(slam),
        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE))
    activate = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=slam, start_state='configuring',
        goal_state='inactive',
        entities=[EmitEvent(event=ChangeState(
            lifecycle_node_matcher=launch.events.matches_action(slam),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE))]))
    # Nav2 and the explorer wait for slam_toolbox `active`: before that there is
    # no /map and no map -> odom for the costmaps to start from.
    nav2_and_explore = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=slam, goal_state='active',
        entities=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(
                    get_package_share_directory('nav2_bringup'),
                    'launch', 'navigation_launch.py')),
                launch_arguments={
                    'params_file': nav2_params,
                    'use_sim_time': use_sim_time,
                    'autostart': 'true',
                    'use_composition': 'False'}.items()),
            Node(package='explore_lite', executable='explore', name='explore_node',
                 output='screen',
                 parameters=[os.path.join(slam_pkg, 'config', 'explore.yaml'),
                             {'use_sim_time': use_sim_time}])]))

    return LaunchDescription([
        # navigation_launch.py does not pass params_file to its lifecycle manager
        SetParameter(name='bond_timeout', value=float(bond_timeout)),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('dry_run', default_value='true'),
        DeclareLaunchArgument('bridge', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(bringup, 'launch', 'base.launch.py')),
            launch_arguments={'use_sim_time': use_sim_time,
                              'dry_run': LaunchConfiguration('dry_run'),
                              'bridge': LaunchConfiguration('bridge')}.items()),
        slam, activate, nav2_and_explore,
        # /run/save: map + pose graph + configs under one dated name
        Node(package='delivery_bot_slam', executable='run_save', output='screen'),
        # configure is not retried if sent before the lifecycle services exist
        TimerAction(period=5.0, actions=[configure]),
    ])

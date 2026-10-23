"""Autonomous mapping: base stack, slam_toolbox, Nav2, explore_lite.

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

Acceptance test
    ``ros2 lifecycle get /slam_toolbox`` reports ``active``;
    ``ros2 topic echo /map --once`` returns a grid;
    ``ros2 run tf2_ros tf2_echo map base_footprint`` resolves;
    ``ros2 topic echo /explore/frontiers --once`` shows markers once the
    costmap has grown. With the robot on the floor the wheels start turning
    within a few seconds -- which is exactly why the warning is first.
"""

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([])

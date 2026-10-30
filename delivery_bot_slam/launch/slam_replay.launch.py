"""Offline SLAM replay from a recorded bag: estimation and mapping only.

No hardware. No lidar driver, no IMU driver, no motor node: every sensor
message comes out of the bag, so a mapping experiment can be re-run on the Mac
without the robot.

What this file starts
---------------------
    rf2o_laser_odometry     /scan -> /odom_rf2o, ``publish_tf: false``,
                            ``odom_topic: /odom_rf2o``
    odom_covariance_relay   /odom_rf2o -> /odom_rf2o_cov
    ekf_filter_node         robot_localization with ``ekf_params_file``
    slam_toolbox            ``LifecycleNode``, executable
                            ``async_slam_toolbox_node``, name ``slam_toolbox``,
                            configured with ChangeState(TRANSITION_CONFIGURE)
                            and activated on OnStateTransition(
                            goal_state='inactive') -- a plain ``Node`` stays
                            unconfigured in 2.8.5 and never publishes /map
    trajectory_recorder     /slam/path and /odom/path, optional TUM output
    foxglove_bridge         so the replay can be watched from the Mac
    (trajectory_recorder is added in build path 7.1)

No ``robot_state_publisher`` by default (``use_rsp:=false``; set it true only for a bag with no ``/tf_static``). The static tree comes from ``/tf_static`` in the
bag, which is the geometry that was current when the bag was recorded. A live
``robot_state_publisher`` would be a second publisher of
``base_footprint -> base_link``, ``base_link -> laser`` and
``base_link -> imu_link``; if the URDF changed after the recording, the two
disagree and the replay silently uses whichever arrived last. Record a new bag
after changing the URDF rather than mixing the two.

Every node gets ``use_sim_time: true``. Nothing here reads the wall clock, so
the replayed stamps drive TF, the EKF and slam_toolbox exactly as they did
live.

The replay rule
---------------
Play only the sensor and static-transform topics:

    ros2 bag play ~/bags/room --topics /scan /imu/data /tf_static

(``~/bags/room`` is an MCAP bag directory written by ``ros2 bag record -s mcap
-o room``; the repo records MCAP, not sqlite3.)

Never replay ``/tf``. The live EKF and slam_toolbox in this launch republish
``odom -> base_footprint`` and ``map -> odom`` themselves. A bag that also
carries ``/tf`` gives each of those transforms two publishers, and the map
visibly jumps at every playback hiccup -- it looks exactly like a broken
sensor, which is why the rule is here and not in a note. ``/tf_static`` is
safe and necessary (lidar and IMU mounts): no driver is running to publish it.

A full replay, start to finish:

    ros2 launch delivery_bot_slam slam_replay.launch.py slam_mode:=mapping
    # second terminal, once the launch is up:
    ros2 bag play ~/bags/room --topics /scan /imu/data /tf_static

Launch arguments
    ``slam_mode``        ``mapping`` (default) or ``localization``. Selects
                         slam_toolbox's ``mode`` parameter; ``localization``
                         requires ``map``.
    ``ekf_params_file``  default
                         ``delivery_bot_bringup/config/ekf.yaml``, so an
                         experiment can swap in a variant config without
                         editing the bringup package.
    ``map``              serialised pose graph for ``localization`` mode,
                         without an extension (slam_toolbox appends
                         ``.posegraph`` and ``.data``). Empty in mapping mode.
    ``use_sim_time``     default ``true``; this launch is for replay.
    ``tum_output_dir``   empty = no files. A directory writes the recorder's
                         ``slam_*.tum`` and ``odom_*.tum`` on shutdown, for
                         ``evo``.

A bag recorded without ``/tf_static`` cannot be replayed here: there is no
``robot_state_publisher`` by design, so the static tree has to come from the
bag. Record again rather than adding one back.

Note on the EKF input: ``ekf_params_file`` must point ``odom0`` at
``/odom_rf2o_cov``, the relay's output, not at ``/odom_rf2o``. The bringup
``ekf.yaml`` already does; a variant config that still names ``/odom_rf2o``
silently reproduces the zero-covariance problem this package exists to fix.

Acceptance test
    During playback ``ros2 topic hz /odom_rf2o_cov`` matches the bag's rf2o
    rate, ``ros2 topic echo /odometry/filtered --once`` shows a moving pose
    whose stamp is the bag's, not today's, and ``ros2 lifecycle get
    /slam_toolbox`` reports ``active``. After the bag ends, ``ros2 topic echo
    /map --once`` shows the room. Playing the same bag twice produces the same
    map; if it does not, something is publishing /tf twice.

Build path: task 5.5 in docs/slam_build_path.md
"""

import os

import launch
import lifecycle_msgs.msg
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    bringup = get_package_share_directory('delivery_bot_bringup')
    description = get_package_share_directory('delivery_bot_description')
    slam_pkg = get_package_share_directory('delivery_bot_slam')
    sim = LaunchConfiguration('use_sim_time')
    mode = LaunchConfiguration('slam_mode')

    # mapping and localisation have separate configs; pick by slam_mode
    slam_params = PythonExpression([
        "'", os.path.join(bringup, 'config', 'slam_mapping.yaml'),
        "' if '", mode, "' == 'mapping' else '",
        os.path.join(bringup, 'config', 'slam_localization.yaml'), "'"])

    slam = LifecycleNode(
        package='slam_toolbox', executable='async_slam_toolbox_node',
        name='slam_toolbox', namespace='', output='screen',
        parameters=[slam_params, {
            'use_lifecycle_manager': False, 'use_sim_time': sim,
            'mode': mode,
            'map_file_name': LaunchConfiguration('map')}])
    configure = EmitEvent(event=ChangeState(
        lifecycle_node_matcher=launch.events.matches_action(slam),
        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE))
    activate = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=slam, start_state='configuring',
        goal_state='inactive',
        entities=[EmitEvent(event=ChangeState(
            lifecycle_node_matcher=launch.events.matches_action(slam),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE))]))

    return LaunchDescription([
        DeclareLaunchArgument('slam_mode', default_value='mapping'),
        DeclareLaunchArgument('ekf_params_file', default_value=os.path.join(
            bringup, 'config', 'ekf.yaml')),
        DeclareLaunchArgument('map', default_value=''),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        # The static tree normally comes from /tf_static in the bag. A bag
        # recorded without it needs this on; never both (two publishers).
        DeclareLaunchArgument('use_rsp', default_value='false'),
        DeclareLaunchArgument('foxglove', default_value='true'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             condition=IfCondition(LaunchConfiguration('use_rsp')),
             parameters=[{'use_sim_time': sim, 'robot_description': ParameterValue(
                 Command(['xacro ', os.path.join(
                     description, 'urdf', 'delivery_bot.urdf.xacro')]),
                 value_type=str)}]),
        Node(package='rf2o_laser_odometry', executable='rf2o_laser_odometry_node',
             name='rf2o_laser_odometry', output='screen',
             parameters=[{
                 'laser_scan_topic': '/scan', 'odom_topic': '/odom_rf2o',
                 'publish_tf': False,  # the EKF owns odom -> base_footprint
                 'base_frame_id': 'base_footprint', 'odom_frame_id': 'odom',
                 'init_pose_from_topic': '', 'freq': 20.0,
                 'use_sim_time': sim}]),
        Node(package='delivery_bot_slam', executable='odom_covariance_relay',
             name='odom_covariance_relay', output='screen',
             parameters=[os.path.join(slam_pkg, 'config', 'odom_covariance.yaml'),
                         {'use_sim_time': sim}]),
        Node(package='robot_localization', executable='ekf_node',
             name='ekf_filter_node', output='screen',
             parameters=[LaunchConfiguration('ekf_params_file'),
                         {'use_sim_time': sim}]),
        slam, activate, configure,
        Node(package='foxglove_bridge', executable='foxglove_bridge',
             condition=IfCondition(LaunchConfiguration('foxglove')),
             parameters=[{'use_sim_time': sim}]),
        # trajectory_recorder joins here in build path 7.1.
    ])

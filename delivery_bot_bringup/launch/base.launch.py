"""Base stack that both mapping and navigation build on.

Order of ownership for tf matters:
  odom -> base_footprint is published by the EKF only (rf2o has publish_tf
  false), because two publishers of one transform make the map spin.

Motors default to dry_run: the launch argument exists so live testing is a
deliberate act, never a default.

What this file is expected to start (see docs/07_ros_stack.md):

  robot_state_publisher          URDF from delivery_bot_description, xacro
  rplidar_node                   /scan, on /dev/rplidar at 115200
  rf2o_laser_odometry            /scan -> /odom_rf2o, publish_tf false
  imu_node                       /imu/data, from delivery_bot_drivers
  ekf_filter_node                robot_localization, config/ekf.yaml
  motor_node                     /cmd_vel -> GPIO, dry_run override here
  foxglove_bridge                port 8765

Launch arguments to declare: dry_run (default true), use_sim_time (false).
"""

from launch import LaunchDescription


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([])

"""Records two trajectories for SLAM evaluation, as Path topics and TUM files.

``/slam/path`` is built from TF ``map -> base_footprint``: it is what SLAM
believes the robot did, including loop closures, so it can be compared with
the map it produced. ``/odom/path`` is built from the EKF's
``/odometry/filtered``: it is dead reckoning, so the gap between the two is
the correction SLAM applied. Both are ``nav_msgs/msg/Path`` in their own frame
(``map`` and the odometry message's ``header.frame_id``, normally ``odom``).

Contract
--------
Subscribe
    TF ``map -> base_footprint`` via ``tf2_ros.Buffer`` +
    ``tf2_ros.TransformListener``, sampled on a ``sample_rate_hz`` (20 Hz)
    timer with a latest-available lookup (``rclpy.time.Time()``).
    ``/odometry/filtered``, ``nav_msgs/msg/Odometry``, queue depth 10.

Publish
    ``/slam/path`` (``nav_msgs/msg/Path``, frame ``map``) and
    ``/odom/path`` (frame ``odom``), each message carrying the full pose list
    so far and a fresh ``header.stamp`` from the node clock, at
    ``publish_rate_hz`` (1 Hz). A small room produces a few hundred poses, so
    republishing the list is cheap; republishing at the sampling rate is not.

Append rule
    A pose is appended only when the robot has moved at least 2 cm in the
    plane (``min_translation_m`` = ``0.02``) OR rotated at least 2 degrees
    (``min_rotation_deg`` = ``2.0``, ``0.0349`` rad) since the last appended
    pose. The sampling timer exists so the check runs often; the filter is what
    stops a 30 Hz EKF from producing 30 poses per second. The first candidate
    pose is always appended. Translation is measured against the last appended
    pose, not the last sampled one.

    Yaw comes from the quaternion with the standard
    ``atan2(2(wz + xy), 1 - 2(y^2 + z^2))`` formula; z is ignored because the
    robot is planar.

TUM output
    ``tum_output_dir`` (default ``""``, disabled). When it is a non-empty
    path, on shutdown write ``slam_<yyyymmdd-HHMMSS>.tum`` and
    ``odom_<yyyymmdd-HHMMSS>.tum`` into it (creating the directory if
    needed), one row per recorded pose; both files share the one timestamp so
    a run can be identified by its files:

        timestamp x y z qx qy qz qw

    space separated, timestamps in seconds (``sec + nanosec * 1e-9``, nine
    decimal places) taken from the TF lookup or the odometry
    ``header.stamp``. Position and quaternion are in the trajectory's own
    frame. Files are written once per process; a second shutdown must not
    overwrite them.

Parameters
    ``tum_output_dir``    default ``""`` = write nothing.
    ``map_frame``         default ``map``.
    ``base_frame``        default ``base_footprint``.
    ``odom_topic``        default ``/odometry/filtered``.
    ``min_translation_m`` default ``0.02``; append threshold in metres.
    ``min_rotation_deg``  default ``2.0``; append threshold in degrees.
    ``sample_rate_hz``    default ``20.0`` ``# TUNE``; TF sampling rate.
    ``publish_rate_hz``   default ``1.0`` ``# TUNE``; ``Path`` republish rate.

    Configured on the command line; there is no YAML for this node, because
    every value is a property of how the trajectory is consumed rather than of
    the robot.

    Example:

        ros2 run delivery_bot_slam trajectory_recorder --ros-args \
          -p tum_output_dir:=$HOME/ros2_ws/evidence/slam_2026-10-23

Edge cases
    * TF ``map -> base_footprint`` not published yet (SLAM still starting or
      in ``unconfigured``): skip this tick silently at ``debug`` level, never
      crash, never queue a pose for later. Nothing is appended until the
      transform exists, so a slow slam_toolbox start simply delays the path.
    * ``/odometry/filtered`` absent: ``/odom/path`` stays empty and
      ``/slam/path`` is unaffected.
    * Empty trajectory at shutdown: write no file, log ``info`` that there was
      nothing to write and why. Do not create a zero-byte file.
    * Quaternions: normalise before storing/publishing/writing. TF and the EKF
      give near-unit quaternions, but a drifting EKF can hand over one that is
      not, and ``evo``/TUM readers reject or silently mis-scale those. A
      quaternion whose norm is below 1e-9 means a broken message: skip the
      pose and log ``warn``.
    * ``use_sim_time``: every stamp comes from the message or the TF lookup,
      never ``time.time()``, so a bag replay produces TUM timestamps on the
      bag's timeline and ``evo_traj`` lines up with a recorded bag.
    * Shutdown through Ctrl+C goes through ``main``'s ``try/finally``: destroy
      the node after writing the files, so a ``KeyboardInterrupt`` inside
      ``rclpy.spin`` still saves them.

Acceptance test
    ``ros2 topic hz /slam/path`` reports about 1 Hz while stationary and
    drops to a few Hz while driving 0.1 m/s (2 cm every 0.2 s).
    Drive a 1 m square with ``tum_output_dir`` set, Ctrl+C, then
    ``wc -l`` on both files shows roughly 50 rows each and
    ``evo_traj tum <dir>/slam_*.tum --ref <dir>/odom_*.tum --plot``
    opens with both starting at the origin and the odometry drifting away from
    the SLAM path. Replaying the same bag twice gives identical timestamps.
"""

from __future__ import annotations

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node


class TrajectoryRecorder(Node):
    """Publishes map and odom trajectories, optionally writing TUM files."""

    def __init__(self) -> None:
        raise NotImplementedError

    def _on_tf_timer(self) -> None:
        raise NotImplementedError

    def _on_odom(self, msg: Odometry) -> None:
        raise NotImplementedError

    def _accept(self, pose, last_pose) -> bool:
        raise NotImplementedError

    def _publish_path(self, topic: str, frame_id: str, poses: list) -> None:
        raise NotImplementedError

    def _write_tum_files(self) -> None:
        raise NotImplementedError


def main(args=None) -> None:
    raise NotImplementedError

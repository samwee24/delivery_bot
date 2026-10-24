"""Relay that gives rf2o's odometry a twist covariance the EKF can trust.

Why this exists
---------------
The pinned rf2o (deps.repos, commit b38c68e) fills ``pose`` and ``twist`` but
never writes ``twist.covariance``, so all 36 entries stay zero.
robot_localization (Jazzy) replaces every zero measurement variance with 1e-9,
so rf2o's yaw rate arrives at the filter looking almost perfect. The MPU6050's
yaw rate carries a variance of 4e-4 -- five and a half orders of magnitude
larger -- so the EKF effectively ignores the gyro and follows scan-matching
noise instead. This node rewrites the twist covariance to measured values and
republishes the message otherwise unchanged.

Contract
--------
Subscribe
    ``input_topic`` (default ``/odom_rf2o``), ``nav_msgs/msg/Odometry``,
    reliable, queue depth 10.

Publish
    ``output_topic`` (default ``/odom_rf2o_cov``), the same
    ``nav_msgs/msg/Odometry`` with only ``twist.covariance`` replaced.

Carried over untouched
    ``header.stamp`` (including ``sec``/``nanosec``), ``header.frame_id``,
    ``child_frame_id``, the whole of ``pose`` (position, orientation and
    ``pose.covariance``) and ``twist.twist``.

Rewritten
    ``twist.covariance`` is a row-major 6x6 matrix, 36 entries:

        index 0   (row 0, col 0) = ``vx_variance``      [m^2/s^2]
        index 35  (row 5, col 5) = ``vyaw_variance``    [rad^2/s^2]
        every other diagonal     = ``unused_variance``  default 1e3
        every off-diagonal       = 0.0

    ``vy`` (index 7) and ``vz`` (index 14) stay at ``unused_variance``, not at
    a measured value: rf2o reports them as zero with no basis for a variance,
    and ``two_d_mode: true`` in ``delivery_bot_bringup/config/ekf.yaml``
    ignores them anyway. 1e3 means "unknown, do not fuse".

Parameters (see config/odom_covariance.yaml)
    ``input_topic``      default ``/odom_rf2o``
    ``output_topic``     default ``/odom_rf2o_cov``
    ``vx_variance``      CALIBRATE; the config ships a 1e-3 placeholder
    ``vyaw_variance``    CALIBRATE; the config ships a 4e-3 placeholder
    ``unused_variance``  default 1e3

Edge cases
    * If the incoming ``twist.covariance`` is entirely zero, log one ``warn``
      naming the input topic and saying the covariance is being replaced --
      once, on the first such message, not once per message. rf2o always sends
      zeros, so this fires at start-up and then stays silent.
    * If it is already non-zero, log one ``info`` and still overwrite: the
      configured values are the single source of truth, which keeps an
      upstream rf2o fix from silently changing the fusion.
    * ``use_sim_time``: this node never reads the clock. It copies
      ``header.stamp``, so replaying a bag reproduces the recorded times. It
      still takes the launch file's ``use_sim_time`` like every other node, so
      TF lookups elsewhere in the graph agree.
    * The EKF must be pointed at ``output_topic`` (``odom0`` in
      ``delivery_bot_bringup/config/ekf.yaml``). Publishing on a new topic while
      the EKF still reads ``/odom_rf2o`` leaves the zero covariance in place
      and this node inert.

Acceptance test
    With the node running, ``ros2 topic echo /odom_rf2o_cov --field
    twist.covariance`` shows ``vx_variance`` at index 0, ``vyaw_variance`` at
    index 35 and 1e3 on the other diagonals, while ``ros2 topic echo
    /odom_rf2o --field twist.covariance`` still shows zeros.
    robot_localization's diagnostics stop warning about zero covariance for
    odom0, and ``ros2 topic hz /odom_rf2o_cov`` matches the rf2o input rate.

Build path: task 4.3 in docs/slam_build_path.md
"""

from __future__ import annotations

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node


class OdomCovarianceRelay(Node):
    """Rewrites rf2o's twist covariance and republishes under a new topic."""

    def __init__(self) -> None:
        raise NotImplementedError

    def _build_covariance(self) -> list[float]:
        raise NotImplementedError

    def _on_odom(self, msg: Odometry) -> None:
        raise NotImplementedError


def main(args=None) -> None:
    raise NotImplementedError

"""
Records two trajectories for SLAM evaluation, as Path topics and TUM files.

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

Node parameters
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

    For example:

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

Build path: task 7.1 in docs/slam_build_path.md
"""

from __future__ import annotations

from datetime import datetime
import math
import os

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener

# A pose is (t_sec, x, y, z, qx, qy, qz, qw) with a unit quaternion.


def _yaw(p) -> float:
    qx, qy, qz, qw = p[4:8]
    return math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))


def normalise(q):
    """Return the unit quaternion, or None if the norm says the message is broken."""
    n = math.sqrt(sum(c * c for c in q))
    return None if n < 1e-9 else tuple(c / n for c in q)


def accept(pose, last_pose, min_translation_m: float, min_rotation_deg: float) -> bool:
    """First pose always; then 2 cm in the plane OR 2 degrees since the last kept."""
    if last_pose is None:
        return True
    if math.hypot(pose[1] - last_pose[1], pose[2] - last_pose[2]) >= min_translation_m:
        return True
    dyaw = math.atan2(math.sin(_yaw(pose) - _yaw(last_pose)),
                      math.cos(_yaw(pose) - _yaw(last_pose)))
    return abs(math.degrees(dyaw)) >= min_rotation_deg


class TrajectoryRecorder(Node):
    """Publishes map and odom trajectories, optionally writing TUM files."""

    def __init__(self) -> None:
        super().__init__('trajectory_recorder')
        self.declare_parameter('tum_output_dir', '')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('odom_topic', '/odometry/filtered')
        self.declare_parameter('min_translation_m', 0.02)
        self.declare_parameter('min_rotation_deg', 2.0)
        self.declare_parameter('sample_rate_hz', 20.0)  # TUNE
        self.declare_parameter('publish_rate_hz', 1.0)  # TUNE
        g = lambda n: self.get_parameter(n).value  # noqa: E731
        self._map = g('map_frame')
        self._base = g('base_frame')
        self._dt = float(g('min_translation_m'))
        self._dr = float(g('min_rotation_deg'))
        self._tum_dir = g('tum_output_dir')
        self._slam: list = []
        self._odom: list = []
        self._odom_frame = 'odom'
        self._written = False
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._slam_pub = self.create_publisher(Path, '/slam/path', 10)
        self._odom_pub = self.create_publisher(Path, '/odom/path', 10)
        self.create_subscription(Odometry, g('odom_topic'), self._on_odom, 10)
        self.create_timer(1.0 / float(g('sample_rate_hz')), self._on_tf_timer)
        self.create_timer(1.0 / float(g('publish_rate_hz')), self._publish_all)

    def _add(self, store: list, pose) -> None:
        if self._accept(pose, store[-1] if store else None):
            store.append(pose)

    def _on_tf_timer(self) -> None:
        try:
            t = self._tf_buffer.lookup_transform(self._map, self._base, Time())
        except TransformException:
            self.get_logger().debug(f'{self._map} -> {self._base} not available yet')
            return
        tr, r = t.transform.translation, t.transform.rotation
        q = normalise((r.x, r.y, r.z, r.w))
        if q is None:
            self.get_logger().warn('zero-norm quaternion in TF, pose skipped')
            return
        st = t.header.stamp
        self._add(self._slam, (st.sec + st.nanosec * 1e-9, tr.x, tr.y, tr.z, *q))

    def _on_odom(self, msg: Odometry) -> None:
        o = msg.pose.pose.orientation
        q = normalise((o.x, o.y, o.z, o.w))
        if q is None:
            self.get_logger().warn('zero-norm quaternion in odometry, pose skipped')
            return
        self._odom_frame = msg.header.frame_id or 'odom'
        p, st = msg.pose.pose.position, msg.header.stamp
        self._add(self._odom, (st.sec + st.nanosec * 1e-9, p.x, p.y, p.z, *q))

    def _accept(self, pose, last_pose) -> bool:
        return accept(pose, last_pose, self._dt, self._dr)

    def _publish_all(self) -> None:
        self._publish_path('/slam/path', self._map, self._slam)
        self._publish_path('/odom/path', self._odom_frame, self._odom)

    def _publish_path(self, topic: str, frame_id: str, poses: list) -> None:
        path = Path()
        path.header.frame_id = frame_id
        path.header.stamp = self.get_clock().now().to_msg()
        for t, x, y, z, qx, qy, qz, qw in poses:
            ps = PoseStamped()
            ps.header.frame_id = frame_id
            ps.header.stamp = Time(seconds=t).to_msg()
            ps.pose.position.x, ps.pose.position.y, ps.pose.position.z = x, y, z
            (ps.pose.orientation.x, ps.pose.orientation.y,
             ps.pose.orientation.z, ps.pose.orientation.w) = qx, qy, qz, qw
            path.poses.append(ps)
        (self._slam_pub if topic == '/slam/path' else self._odom_pub).publish(path)

    def _write_tum_files(self) -> None:
        if not self._tum_dir or self._written:
            return
        self._written = True
        if not self._slam and not self._odom:
            self.get_logger().info('no poses recorded (no TF map -> base and no odometry); '
                                   'no TUM files written')
            return
        os.makedirs(self._tum_dir, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        for name, poses in (('slam', self._slam), ('odom', self._odom)):
            if not poses:
                continue
            with open(os.path.join(self._tum_dir, f'{name}_{stamp}.tum'), 'w') as f:
                for t, *rest in poses:
                    f.write(f'{t:.9f} ' + ' '.join(f'{v:.9g}' for v in rest) + '\n')
        self.get_logger().info(f'wrote TUM files to {self._tum_dir}')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TrajectoryRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._write_tum_files()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

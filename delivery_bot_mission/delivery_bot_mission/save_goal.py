"""
Save the robot's current map pose under a name in goals.yaml.

Run it while the robot is where you want the goal, and the map is already up
(localization or mapping mode both publish map -> base_footprint):

    ros2 run delivery_bot_mission save_goal --ros-args \
      -p goals_file:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml \
      -- seat_1

Add ``-p overwrite:=true`` to replace an existing name. The default goals_file
points at the source tree on purpose, so the change can be committed.
"""

from __future__ import annotations

import os
import sys

from delivery_bot_mission.goals import save_goal, yaw_from_quaternion
import rclpy
from rclpy.node import Node
from rclpy.utilities import remove_ros_args
from tf2_ros import Buffer, TransformListener

DEFAULT_FILE = os.path.expanduser(
    '~/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml')


class SaveGoal(Node):
    """Looks up map -> base_footprint, then appends one named goal to the YAML."""

    def __init__(self, name: str) -> None:
        super().__init__('save_goal')
        self.name = name
        self.goals_file = self.declare_parameter('goals_file', DEFAULT_FILE).value
        self.overwrite = self.declare_parameter('overwrite', False).value
        self.tf_buffer = Buffer()
        self.listener = TransformListener(self.tf_buffer, self)

    def run(self) -> int:
        """Return 0 on success, 1 if the pose is unavailable or the name is taken."""
        end = self.get_clock().now().nanoseconds + 10 * 10**9
        tf = None
        while rclpy.ok() and tf is None and self.get_clock().now().nanoseconds < end:
            rclpy.spin_once(self, timeout_sec=0.2)
            if self.tf_buffer.can_transform('map', 'base_footprint', rclpy.time.Time()):
                tf = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        if tf is None:
            self.get_logger().error('no map -> base_footprint within 10 s; is a stack running?')
            return 1
        t, q = tf.transform.translation, tf.transform.rotation
        yaw = yaw_from_quaternion(q.x, q.y, q.z, q.w)
        try:
            save_goal(self.goals_file, self.name, t.x, t.y, yaw, self.overwrite)
        except ValueError as err:
            self.get_logger().error(str(err))
            return 1
        self.get_logger().info(
            f'saved {self.name}: x {t.x:.3f} y {t.y:.3f} yaw {yaw:.3f} -> {self.goals_file}')
        return 0


def main(args=None) -> None:
    """Entry point: ``save_goal <name>``."""
    rclpy.init(args=args)
    names = remove_ros_args(sys.argv)[1:]
    if len(names) != 1:
        print('usage: save_goal [--ros-args ...] -- <name>', file=sys.stderr)
        rclpy.shutdown()
        sys.exit(2)
    node = SaveGoal(names[0])
    code = node.run()
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(code)

"""Save the robot's current map pose under a name in goals.yaml.

Run it while the robot is where you want the goal, and the map is already up
(localization or mapping mode both publish map -> base_footprint):

    ros2 run delivery_bot_mission save_goal --ros-args \
      -p goals_file:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml \
      seat_1

The default goals_file points at the source tree on purpose, so the change can
be committed. Writing YAML here does not preserve comments or ordering from the
existing file beyond the top-level dict order.
"""

from __future__ import annotations

import math
import os
import sys

import rclpy
import yaml
from geometry_msgs.msg import TransformStamped  # noqa: F401  (documents intent)
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener

DEFAULT_GOALS_FILE = os.path.expanduser(
    "~/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml"
)


def yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


class SaveGoal(Node):
    def __init__(self, name: str) -> None:
        super().__init__("save_goal")
        self.name = name
        self.goals_file = self.declare_parameter(
            "goals_file", DEFAULT_GOALS_FILE
        ).value
        self.source_frame = self.declare_parameter("map_frame", "map").value
        self.target_frame = self.declare_parameter(
            "base_frame", "base_footprint"
        ).value

        self._buffer = Buffer()
        self._listener = TransformListener(self._buffer, self)

    def run(self) -> int:
        try:
            transform = self._buffer.lookup_transform(
                self.source_frame,
                self.target_frame,
                rclpy.time.Time(),  # latest
                timeout=Duration(seconds=2.0),
            )
        except Exception as exc:
            self.get_logger().error(
                "no transform %s -> %s: %s\n"
                "Is the base stack running?"
                % (self.source_frame, self.target_frame, exc)
            )
            return 2

        translation = transform.transform.translation
        rotation = transform.transform.rotation
        pose = {
            "x": round(float(translation.x), 3),
            "y": round(float(translation.y), 3),
            "yaw": round(
                yaw_from_quaternion(rotation.x, rotation.y, rotation.z, rotation.w),
                3,
            ),
        }

        goals: dict = {}
        if os.path.exists(self.goals_file):
            with open(self.goals_file, "r", encoding="utf-8") as handle:
                goals = yaml.safe_load(handle) or {}
        else:
            self.get_logger().warning("creating %s" % self.goals_file)
        goals[self.name] = pose
        os.makedirs(os.path.dirname(self.goals_file) or ".", exist_ok=True)
        with open(self.goals_file, "w", encoding="utf-8") as handle:
            yaml.safe_dump(goals, handle, sort_keys=False, default_flow_style=False)

        self.get_logger().info(
            "saved %s = [%.3f, %.3f, %.3f] to %s"
            % (self.name, pose["x"], pose["y"], pose["yaw"], self.goals_file)
        )
        return 0


def main(args=None) -> None:
    # Strip ROS arguments so our positional name survives them.
    argv = rclpy.utilities.remove_ros_args(sys.argv)[1:]
    names = [a for a in argv if not a.startswith("-")]
    if len(names) != 1:
        print("usage: save_goal <name> [--ros-args -p goals_file:=...]")
        raise SystemExit(1)

    rclpy.init(args=args)
    node = SaveGoal(names[0])
    try:
        code = node.run()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    raise SystemExit(code)


if __name__ == "__main__":
    main()

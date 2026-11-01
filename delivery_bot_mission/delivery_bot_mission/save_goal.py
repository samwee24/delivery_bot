"""
Save the robot's current map pose under a name in goals.yaml.

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

from rclpy.node import Node


def yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    raise NotImplementedError


class SaveGoal(Node):
    """Looks up map -> base_footprint, then appends one named goal to the YAML."""

    def __init__(self, name: str) -> None:
        raise NotImplementedError

    def run(self) -> int:
        raise NotImplementedError


def main(args=None) -> None:
    raise NotImplementedError

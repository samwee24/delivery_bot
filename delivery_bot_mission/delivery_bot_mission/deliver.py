"""
Delivery mission: named goals, then home.

Usage:

    ros2 run delivery_bot_mission deliver --ros-args \
      -p goals_file:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml \
      -- seat_1 seat_2

Each goal is visited in order with a ``wait_s`` pause, then the robot returns
home. Ctrl+C cancels the current task through the Nav2 action interface and
leaves the motor watchdog to stop the wheels.

Goal names live in config/goals.yaml; the map frame is the reference for every
coordinate in it.
"""

from __future__ import annotations


def _goal_to_pose(navigator, goal: dict):
    """Turn {x, y, yaw} from goals.yaml into a PoseStamped in the map frame."""
    raise NotImplementedError


def main(args=None) -> None:
    raise NotImplementedError

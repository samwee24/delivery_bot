"""Delivery mission: named goals, then home.

Usage:

    ros2 run delivery_bot_mission deliver --ros-args \
      -p goals_file:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml \
      -- seat_1 seat_2

Each goal is visited in order with a ``wait_s`` pause, then the robot returns
home. Ctrl+C cancels the current task through the Nav2 action interface and
leaves the motor watchdog to stop the wheels.
"""

from __future__ import annotations

import math
import os
import sys
import time

import rclpy
import yaml
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

DEFAULT_GOALS_FILE = os.path.expanduser(
    "~/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml"
)
HOME_NAME = "home"


def _goal_to_pose(navigator: BasicNavigator, goal: dict) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(goal["x"])
    pose.pose.position.y = float(goal["y"])
    yaw = float(goal.get("yaw", 0.0))
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def main(args=None) -> None:
    argv = rclpy.utilities.remove_ros_args(sys.argv)[1:]
    requested = [a for a in argv if not a.startswith("-")]

    rclpy.init(args=args)
    navigator = BasicNavigator()
    navigator.declare_parameter("wait_s", 10.0)
    goals_file = navigator.declare_parameter("goals_file", DEFAULT_GOALS_FILE).value
    wait_s = float(navigator.get_parameter("wait_s").value)

    if not os.path.exists(goals_file):
        navigator.get_logger().error("goals file not found: %s" % goals_file)
        raise SystemExit(1)
    with open(goals_file, "r", encoding="utf-8") as handle:
        goals = yaml.safe_load(handle) or {}

    available = sorted(goals)
    missing = [name for name in requested if name not in goals]
    if missing:
        navigator.get_logger().error(
            "unknown goal(s): %s\navailable: %s"
            % (", ".join(missing), ", ".join(available))
        )
        raise SystemExit(1)

    legs = list(requested)
    if not legs or legs[-1] != HOME_NAME:
        legs.append(HOME_NAME)

    navigator.get_logger().info("waiting for Nav2 + slam_toolbox localization ...")
    navigator.waitUntilNav2Active(localizer="slam_toolbox")

    try:
        for leg in legs:
            pose = _goal_to_pose(navigator, goals[leg])
            navigator.get_logger().info(
                "leg -> %s [%.2f, %.2f, %.2f]"
                % (leg, pose.pose.position.x, pose.pose.position.y, goals[leg].get("yaw", 0.0))
            )
            navigator.goToPose(pose)

            while not navigator.isTaskComplete():
                feedback = navigator.getFeedback()
                if feedback is not None:
                    navigator.get_logger().info(
                        "  %s: %.2f m remaining" % (leg, feedback.distance_remaining),
                        throttle_duration_sec=2.0,
                    )
                time.sleep(0.1)

            result = navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                navigator.get_logger().info("leg %s: succeeded" % leg)
            else:
                name = {
                    TaskResult.CANCELED: "canceled",
                    TaskResult.FAILED: "failed",
                }.get(result, str(result))
                navigator.get_logger().error("leg %s: %s — stopping mission" % (leg, name))
                break

            if leg != legs[-1]:
                time.sleep(wait_s)
    except KeyboardInterrupt:
        navigator.get_logger().warning("interrupted — cancelling current task")
        navigator.cancelTask()
    finally:
        navigator.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

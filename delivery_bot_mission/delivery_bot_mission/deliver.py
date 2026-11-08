"""
Delivery mission: named goals, then home.

Usage:

    ros2 run delivery_bot_mission deliver --ros-args \
      -p goals_file:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml \
      -- seat_1 seat_2

Each goal is visited in order with a ``wait_s`` pause (a per-goal ``wait_s`` in
goals.yaml wins over the parameter, default 5.0), then the robot returns home.
Ctrl+C cancels the current task through the Nav2 action interface and leaves
the motor watchdog to stop the wheels.

Goal names live in config/goals.yaml; the map frame is the reference for every
coordinate in it.
"""

from __future__ import annotations

import os
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.utilities import remove_ros_args

from delivery_bot_mission.goals import load_goals, pick_goals, pose_fields

DEFAULT_FILE = os.path.expanduser(
    '~/ros2_ws/src/delivery_bot/delivery_bot_mission/config/goals.yaml')


def _goal_to_pose(navigator, goal: dict):
    """Turn {x, y, yaw} from goals.yaml into a PoseStamped in the map frame."""
    x, y, qx, qy, qz, qw = pose_fields(goal)
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x, pose.pose.position.y = x, y
    pose.pose.orientation.x, pose.pose.orientation.y = qx, qy
    pose.pose.orientation.z, pose.pose.orientation.w = qz, qw
    return pose


def _go(navigator, name: str, goal: dict) -> bool:
    """Send one goal and block until it finishes; True if it succeeded."""
    navigator.goToPose(_goal_to_pose(navigator, goal))
    while not navigator.isTaskComplete():
        time.sleep(0.2)
    result = navigator.getResult()
    navigator.get_logger().info(f'{name}: {result.name}')
    return result == TaskResult.SUCCEEDED


def main(args=None) -> None:
    """Entry point: ``deliver <name> ...``; visits each, then home."""
    rclpy.init(args=args)
    names = remove_ros_args(sys.argv)[1:]
    navigator = BasicNavigator('deliver')
    navigator.declare_parameter('goals_file', DEFAULT_FILE)
    navigator.declare_parameter('wait_s', 5.0)
    status = 1
    try:
        goals = load_goals(navigator.get_parameter('goals_file').value)
        route = pick_goals(goals, names) + ['home']
        default_wait = navigator.get_parameter('wait_s').value
        # no AMCL here: slam_toolbox is the localizer
        navigator.waitUntilNav2Active(localizer='slam_toolbox')
        status = 0
        for name in route:
            if not _go(navigator, name, goals[name]):
                status = 1
                break
            if name != 'home':
                time.sleep(float(goals[name].get('wait_s', default_wait)))
    except ValueError as err:
        navigator.get_logger().error(str(err))
    except KeyboardInterrupt:
        navigator.cancelTask()
    finally:
        navigator.destroy_node()
        rclpy.shutdown()
    sys.exit(status)

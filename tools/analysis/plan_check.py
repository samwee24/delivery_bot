"""Ask the Nav2 planner for paths from home; print pose count and length."""
import json
import math
import sys

import rclpy
from nav2_msgs.action import ComputePathToPose
from rclpy.action import ActionClient
from rclpy.node import Node

GOALS = [(1.0, 0.0), (0.0, 1.0), (1.0, 1.0), (-1.0, 0.0), (2.0, -1.0), (-9.0, -3.0), (0.0, 20.0)]

paths = {}
rclpy.init()
node = Node('plan_check')
client = ActionClient(node, ComputePathToPose, 'compute_path_to_pose')
if not client.wait_for_server(timeout_sec=30):
    print('no compute_path_to_pose server'); sys.exit(1)
for gx, gy in GOALS:
    goal = ComputePathToPose.Goal()
    goal.use_start = False          # start = robot pose from tf map->base_footprint
    goal.goal.header.frame_id = 'map'
    goal.goal.pose.position.x, goal.goal.pose.position.y = gx, gy
    goal.goal.pose.orientation.w = 1.0
    fut = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, fut, timeout_sec=10)
    handle = fut.result()
    if handle is None or not handle.accepted:
        print(f'goal ({gx}, {gy}): rejected'); continue
    res_fut = handle.get_result_async()
    rclpy.spin_until_future_complete(node, res_fut, timeout_sec=20)
    res = res_fut.result()
    if res is None:
        print(f'goal ({gx}, {gy}): timeout'); continue
    poses = res.result.path.poses
    length = sum(math.dist((a.pose.position.x, a.pose.position.y), (b.pose.position.x, b.pose.position.y))
                 for a, b in zip(poses, poses[1:]))
    paths[f'{gx},{gy}'] = [(p.pose.position.x, p.pose.position.y) for p in poses]
    ms = res.result.planning_time.sec * 1e3 + res.result.planning_time.nanosec / 1e6
    print(f'goal ({gx}, {gy}): status {res.status} error_code {res.result.error_code} '
          f'poses {len(poses)} length {length:.2f} m planning {ms:.0f} ms')
json.dump(paths, open('/tmp/paths.json', 'w'))
node.destroy_node(); rclpy.shutdown()

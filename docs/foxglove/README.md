# Foxglove — the SLAM layout

What to look at while mapping, while localising, and while deciding whether the
estimation stack is behaving. The layout itself is not written by hand here: build it
once in Foxglove Studio, then export it and commit the file as
`docs/foxglove/slam_layout.json` so every machine opens the same panels. Ad-hoc panels
drift; a committed layout is the thing the phase-5 and phase-6 "done when" conditions
refer to.

For why any of it behaves the way it does — lifecycle, covariance, `laser_yaw` — see
[`../slam.md`](../slam.md).

## How to connect

The bridge runs inside `base.launch.py`, so it is up in every mode. Open a Foxglove
connection to `ws://<pi-ip>:8765`; the LAN and Tailscale addresses, and the stale
bridge on port 8765, are in the main [Foxglove section](../../README.md#foxglove).

## 3D panel

Fixed frame `map`. Every display below is a TF child of it; if the fixed frame is
`odom` or `base_link` the pose graph and the map will not line up.

| Topic | What to look for |
| --- | --- |
| `/map` | Walls straight, furniture recognisable. A doubled wall that closes up after a loop closure is normal; one that stays doubled is drift |
| `/scan` | The scan laid over the walls. A wrong `laser_yaw` shows as a rotated scan against the map, not as a misplaced robot |
| TF | `map → odom → base_footprint → base_link → laser`. The robot model must move with the scan; either alone means the tree is broken |
| `/robot_description` | The robot model itself, from `robot_state_publisher`; use it to confirm the sensor frames sit where the URDF says |
| `/slam_toolbox/graph_visualization` | The pose graph: nodes along the driven path and the loop-closure edges between them. An empty graph with a live map means `slam_toolbox` is not configured |
| `/slam/path` | The trajectory as `slam_toolbox` believes it, after scan matching and loop closure |
| `/odom/path` | The EKF's trajectory. It should sit on `/slam/path`; the gap between them is odometry drift that the mapper is correcting |
| `/explore/frontiers` | Frontier markers for autonomous mapping. They thin out as the room is covered and disappear at the end |
| `/global_costmap/costmap` | Nav2's inflated costmap, to see what the planner treats as blocked. **Display only — never drive from it**: it is a planning artefact, not a map |

## Plot panel

Yaw rate, three traces on one plot, same time axis:

| Series | Topic field |
| --- | --- |
| rf2o | `/odom_rf2o.twist.twist.angular.z` |
| gyro | `/imu/data.angular_velocity.z` |
| fused | `/odometry/filtered.twist.twist.angular.z` |

This is the direct check that the covariance fix works. The fused trace should sit
**between** the two inputs — pulled towards the gyro when rf2o's scan matching is poor,
towards rf2o when the gyro drifts. A fused trace lying exactly on the rf2o line means
the relay is not running and the EKF still believes rf2o's zero covariance.

## Controls

| Control | Topic or service | Use |
| --- | --- | --- |
| 3D panel → "Publish pose estimate" | `/initialpose` | Set the start pose in localisation mode; `slam_toolbox` listens and re-anchors `map → odom` |
| Call service | `/slam_toolbox/serialize_map` | Write the `.posegraph` and `.data` files that navigation mode loads |
| Call service | `/slam_toolbox/save_map` | Write the occupancy grid and its `.yaml`; equivalent to `map_saver_cli` |
| Call service | `/slam_toolbox/pause_new_measurements` | Stop adding nodes, typically before saving at the end of a run |
| Call service | `/slam_toolbox/reset` | Clear the graph and the map and start a fresh mapping run |
| Publish | `/explore/resume` (`std_msgs/Bool`) | Start or stop frontier exploration: `true` resumes, `false` holds the robot |
| Raw Messages | `/explore/status` | Exploration state as text; the quickest way to see whether it is still looking for frontiers or has finished |

## Troubleshooting

| Symptom | Cause | Check |
| --- | --- | --- |
| 3D view empty | Fixed frame wrong, or no TF at all | Set the fixed frame to `map`; then `ros2 run tf2_tools view_frames` |
| Map rotates on the spot | Two publishers of one transform | `view_frames`: `odom → base_footprint` must come from the EKF alone, with rf2o at `publish_tf: false` |
| Scan rotated against the map | `laser_yaw` is wrong | Redo the 50 cm box test in the `laser` frame and correct the URDF |
| Graph empty, map alive | `slam_toolbox` never left `unconfigured` | The launch must use a `LifecycleNode` and activate it; a plain `Node` publishes nothing and logs nothing |

The underlying reasons, and what each failure does to the map, are in
[`../slam.md`](../slam.md).

# SLAM journal

One entry per task from [slam_build_path.md](slam_build_path.md), in the user's own words.
Each entry: the date, the commit hash if code changed, what was done, the numbers,
and the answer to the task's "Explain it back" question.

> **Status (2026-11-01):** drafted by Claude from `docs/test_log.md`, `notes/notes.md` and
> `docs/CA3.md`, not written by the author. Facts and numbers come from those files; the
> "explain it back" answers are Claude's. Rewrite each answer in your own words before it goes
> into the report. Tasks 0.1 to 1.5 and 2.1 left no run record in the log, so their "what I did"
> lines say only what the logs show.

## 0.1 ROS 2 in one picture: nodes, topics, QoS
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: No run record in the log; `/scan` comes from `rplidar_node`, reliability best effort (seen in `ros2 topic info /scan -v`, 2026-11-01).
- Result / numbers: `/scan` publishes at about 7.1 Hz.
- Explain it back: Transient local means a late subscriber is given the last published message. `/map` changes rarely, so Foxglove connecting minutes after the last update would otherwise see nothing until the next one.

## 0.3 What SLAM is, and which kind you're using
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: Placed the stack by category: rf2o is scan-matching odometry, the EKF fuses it with the gyro, slam_toolbox is pose-graph SLAM (`docs/CA3.md`, D5).
- Result / numbers: —
- Explain it back: A particle filter proposes each particle's motion from odometry; with no wheel encoders the proposals are poor and it needs many particles. Loop closure in a pose graph adds a constraint between two distant poses and re-optimises the whole trajectory, so the drift is spread back over it. A filter cannot revise past poses.

## 1.1 Read a LaserScan by hand
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: No run record in the log.
- Result / numbers: —
- Explain it back: `inf` means no return (nothing within range, or the surface absorbed or deflected the beam). A short real reading means something is close. They are opposite situations.

## 1.2 See the scan in Foxglove
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: No run record in the log; scan viewed in Foxglove on 2026-11-01.
- Result / numbers: Walls show as lines of points; on 2026-11-01 Foxglove warned '57 Infinity invalid values' on `/scan`.
- Explain it back: A person's two legs are two separate objects, so each shows as a small arc.

## 1.3 Diagnose the missing points
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: Echo-rate probe on this Pi (`tools/probe_echo_rate.py`).
- Result / numbers: 26–29 % no-echo; gaps follow the room, not the driver (`docs/CA3.md`, OI-4).
- Explain it back: Gaps at the same angles however the robot points would mean something fixed to the robot, such as its own structure, a dirty window or a driver mask. Ours moved with the room, so they are the surfaces.

## 1.4 Find which way the lidar faces
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: Lidar mounting measured and put into the URDF (2026-10-31).
- Result / numbers: `base_footprint → laser` read x 0.020, z 0.152 m with `tf2_echo` (2026-11-01).
- Explain it back: If yaw were 180° off, pushing the robot forward would make rf2o report motion backwards (negative x).

## 1.5 Record and replay your first bag
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: Bags recorded on the Pi (`~/bags`, MCAP) and backed up to `bags/` on the Mac on 2026-11-01.
- Result / numbers: Bags 115 MB and maps 26 MB copied.
- Explain it back: A replay gives every parameter the same input, so any difference comes from the parameter. Redriving the robot gives a different path each time, so you cannot tell whether a change helped.

## 2.1 Measure the robot
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: Measured the wheel base and lidar and IMU mounting (2026-10-31).
- Result / numbers: `wheel_base` 0.156 m, in `drivers.yaml` and the URDF.
- Explain it back: When the robot turns, an off-centre lidar swings through an arc, so its position changes during a scan. The scan smears unless the offset is in the URDF. Driving straight moves every point by the same amount, so nothing smears.

## 2.2 Write the URDF
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: none (no code change)
- What I did: URDF written, validated with `check_urdf`, `view_frames` passed (CI also runs `check_urdf`).
- Result / numbers: Chain `base_footprint → base_link → laser, imu_link`.
- Explain it back: The EKF publishes `odom → base_footprint`, which must connect to the rest of the tree. If `base_footprint` were not a URDF link, `laser` and `imu_link` would hang off a tree with no connection to `odom`, and nothing could be looked up between them.

## 3.2 Run rf2o alone and push the robot by hand
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 0b65af7, 22329b9
- What I did: Hand tests of rf2o: a turn and a 1 m push, bags `2026-10-31_turn_194945` and `_push_195343`.
- Result / numbers: Turn: rf2o −352.9° against a true 360° (−2 %), gyro −360.2°. Push: 0.962 m against 1.000 m (−3.8 %). The 1 m push was preceded by a reposition and shows an unexplained 18° offset; redo it (open).
- Explain it back: Integrating rf2o's pose accumulates its error, and its pose and velocity come from the same scan match. The EKF integrates the velocity itself and weighs it against the gyro. Feeding it both would count the same information twice.

## 3.4 Understand the startup race
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 44f11a3
- What I did: `bash tools/startup_race.sh 10 2.0` and the control with delay 0.
- Result / numbers: 10/10 launches with no transform error at a 2 s delay (the log row for the 0 s control reads '0/3 errors'; check it before quoting it).
- Explain it back: rf2o reads `base_footprint → laser` once on the first scan. If it is missing, rf2o assumes a zero rotation. That happens to be right when `laser_yaw` is 0° and silently flips the sign of the odometry when it is 180°, so the bug would be hidden at 0° and fatal at 180°.

## 4.3 Write the covariance relay
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: d8f46bf
- What I did: Relay `/odom_rf2o → /odom_rf2o_cov` with fitted values, checked on a bag.
- Result / numbers: idx0 1e-3, idx35 4e-3, other diagonals 1e3; 7.06 Hz out, the same as rf2o.
- Explain it back: A relay adds the covariance without touching rf2o's source, so there is no fork to maintain and it survives an rf2o upgrade. The values live in one YAML file.

## 4.4 Calibrate the variances
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 79a4d9a
- What I did: `var_an.py` on the turn and push bags.
- Result / numbers: `vx_variance` 1e-4, `vyaw_variance` 5e-3, gyro 1e-4, each with its source in `odom_covariance.yaml`.
- Explain it back: If the same data is used to tune and to evaluate, the variances are fitted to the evaluation and the result looks better than it will on new data. Calibration and evaluation runs must be separate.

## 5.3 Write mapping.launch.py
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 25403ba, 60a904a, e08b445
- What I did: One command starts `base.launch.py` and slam_toolbox as a lifecycle node. On a bag: 2026-10-30, `still2` replay, `/map` 102x65. Live: 2026-11-01. A bug found: configure was sent before the node's lifecycle services existed when `include_base:=false`, so it failed and was never retried.
- Result / numbers: Live: `/slam_toolbox` active, `map → odom` and `odom → base_footprint` resolve, a 241 x 112 map saved. Two later bag runs with a hand-made rig failed (EKF silent, not this launch file).
- Explain it back: Each transition is asynchronous. Activation is only valid from `inactive`, which the node reaches when configuring finishes. Firing activate straight after configure asks for an invalid transition and is refused. Sending configure before the node's services exist fails for a related reason.

## 5.5 Tune on replays, then freeze
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 79a4d9a..9b90173, 60a904a
- What I did: Replays of `2026-10-31_map_200956`, one parameter changed per run; EKF 20 Hz check on 2026-11-01.
- Result / numbers: Loop closing off: closure 0.658 m against 0.109 m with it on; the other changes moved it by about 1 cm or less. At 20 Hz EKF: closure 0.115 m; the late-update count (1 against 0) is confounded by load.
- Explain it back: The bag's `/tf` already holds `odom → base_footprint` and `map → odom` from the original run. Replaying it next to a live EKF and slam_toolbox gives each transform two publishers, and the map jumps between them.

## 6.2 Run localisation
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 2840a03
- What I did: `navigation.launch.py` (base + `localization_slam_toolbox_node`) on `~/maps/2026-10-31_room2_graph`, start pose `map_start_pose: [0,0,0]`. `map_start_at_dock` is not supported in localisation mode.
- Result / numbers: Live scan points sit on the walls; pose x 0.01, y 0.03, yaw −1.9° after turning the robot to the old home heading.
- Explain it back: slam_toolbox has no global search. It matches the scan to the map inside a small window around its first guess (about ±0.5 m and ±20° here), so the start must be inside that window.

## 6.3 Set the start pose from Foxglove
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: bcc7fab
- What I did: Published a pose estimate on `/initialpose` after carrying the robot away from home.
- Result / numbers: Pose moved from (0.58, −0.28, −44°) to (1.82, −1.11, −29.5°); the points line up.
- Explain it back: The scan would be rotated by the heading error. Within about 20° the matcher repairs it once the robot moves. Beyond that it locks onto the wrong features, and the robot ends up confidently wrong; our 31° case failed.

## 6.4 Wrong-start test
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 0ba4767, 03aaad0
- What I did: Three start offsets from the home pose, each with a push of 0.5–1 m (one case read at rest).
- Result / numbers: 30 cm / 20° clockwise: converged (`map → odom` 0.35 m, −18°). 30 cm / 31°: did not converge (heading about 37° off). 60 cm / 30°: read at rest, inconclusive. Matching only runs after 0.1 m or 0.1 rad of travel.
- Explain it back: In a symmetric room scans from different poses look alike, for instance the same wall layout when turned by 180° or mirrored. The matcher then has several good-looking fits and can pick the wrong one.

## 7.1 Write the trajectory recorder
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 8664700, 6760d20
- What I did: `trajectory_recorder` in `slam_replay.launch.py`, TUM files written, shown in Foxglove.
- Result / numbers: `/slam/path` and `/odom/path` published; `slam_*.tum` and `odom_*.tum` written. Loop closure on the 5.5 base run 0.109 m over 42.0 m.
- Explain it back: Neither path is wrong by default. Odometry drifts steadily, and the SLAM path is pulled back by loop closure. Compare both with a known truth such as the start mark: the robot returned to it, so the path that ends there is the better one.

## 8.2 Build explore_lite
- Date: 2026-10-30 to 2026-11-01 (see `docs/test_log.md`)
- Commit: 61e5d29
- What I did: Cloned `m-explore-ros2` at 326cf8a and built it on the Pi.
- Result / numbers: Two packages built in 11 min 54 s; `explore` listed. A full `colcon build` on 2026-11-01 fails on the vendored `multirobot_map_merge`.
- Explain it back: A branch moves. Pinning the commit means the same code builds next month, and `deps.repos` records it.

<!-- Copy this block for each task:
## 0.1 ROS 2 in one picture: nodes, topics, QoS
- Date:
- Commit:
- What I did:
- Result / numbers:
- Explain it back:
-->

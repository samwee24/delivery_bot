# Handover: delivery_bot Nav2 1 m goal, new home pose — 2026-11-10 (evening)

> **To the new chat:** This is a handover from a previous conversation. Read the whole brief before
> replying. Then reply with a short summary (3–5 lines) of where things stand and what you'll do
> first, and wait for me to confirm before starting — unless I've already told you to go ahead.

## 1. Goal
Get a live Nav2 goal working on the CA3 room delivery robot: drive 1 m forward from the taped home mark and succeed, then go back to home. This is checkpoint 9.3 in `docs/slam_build_path.md` (OI-12). The CA3 presentation is Thu 2026-11-12, and every method must run live on the robot. Original request today: "send_goal /navigate_to_pose to x = 1, it doesn't move very much".

## 2. Context & background
- Repo: `/Users/shermanwee/Documents/MA4890/delivery_bot` (Mac), GitHub `samwee24/delivery_bot`. Read `AGENTS.md` first: rules on safety, provenance, append-only `notes/notes.md` and `evidence/`, PR titles `type: YYYY-MM-DD what`, a test or `no-test:` in the PR.
- Pi: `ssh robot@100.83.14.99` (Tailscale), Ubuntu 24.04, ROS 2 Jazzy, repo at `~/ros2_ws/src/delivery_bot`. Non-interactive ssh: `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash`. **The Pi has no scipy** (numpy only).
- Stack: rplidar A1M8, rf2o (laser odometry, publish_tf false), robot_localization EKF (`odom->base_footprint`), slam_toolbox localisation on map `~/maps/2026-10-31_room2` (`map->odom`), Nav2 with RPP controller, velocity_smoother, collision_monitor, and `motor_node` (teammate's). Mac copy of the map: `bags/maps/2026-10-31_room2.{yaml,pgm}`, `.venv` with numpy/scipy/matplotlib.
- The user is in the lab with the robot; they launch the stack themselves in a terminal and send goals. The motors belong to the teammate: **don't edit `motor_node` or the motor parts of `drivers.yaml`**.
- Pi load runs 13–22 under Nav2, which drives most of the TF-lateness faults.

## 3. Current state
- ✅ **Home moved** from (0, 0, 0) to **(-1.3, -0.3, yaw 2.635 rad = 151°)**, parallel to the walls on either side. Set in `navigation.launch.py` `map_start_pose`, `amcl.yaml` `initial_pose`, `goals.yaml` `home`. The test `test_amcl_frames_and_initial_pose` now checks all three agree. **The floor mark is taped.** Verified live: localisation-only run read (-1.302, -0.307, 149.1°), scan-to-map median 2.6 cm, 77–80 % of points within 10 cm.
- ✅ **transform_tolerance 0.5** on `local_costmap`, `global_costmap`, `behavior_server` (was default 0.3 / 0.1) in `delivery_bot_bringup/config/nav2_params.yaml`. New test `test_nav2_transform_tolerances_cover_slam_lag`. On the Pi: pulled cd44057, colcon built, `test_config_consistency.py` 23 passed.
- ✅ Both changes are on branch `fix/home-pose`, **PR 46** open (https://github.com/samwee24/delivery_bot/pull/46), not merged; CI result not checked. **The Pi is checked out on `fix/home-pose`**, not main.
- ⚠️ The stack started at 21:09 (launch PID 4615) **still runs the old tolerances**; it must be restarted.
- 🔄 Stopped here: the user is about to restart the stack, put the robot back on the mark, and send the 1 m robot-frame goal (the command is in section 5).

## 4. Decisions & reasoning
- **Home moved** because the old home (0, 0) had 0.21 m clearance and goal (1, 0) 0.16 m (distance transform of the map). Both are inside the 0.25 m inflation and the collision_monitor slowdown box (0.5 m ahead, ±0.2 m, ratio 0.3 → 0.045 m/s). The new spot has 0.67 m clearance. The user picked (-1.3, -0.3), first 135°, then asked for "parallel to the wall on its left and right" → fitted 151° (structure tensor: 151.4/151.1/147.9° over 1.0/1.5/2.5 m windows).
- **Tolerance 0.5** because the goal aborted with map->odom 0.37 s old (slam_toolbox lags under load).
- **Rejected:** goal (1, 0): too close to obstacles. Candidate home H1 (-2.09, 0.31), clearance 1.05: the user chose (-1.3, -0.3) instead.
- **Tried and failed:** live capture of 5 `ros2 topic echo` processes at load 16 → Nav2 shut down (`CRITICAL FAILURE: SERVER bt_navigator IS DOWN after not receiving a heartbeat for 10000 ms`). Python stdout to a file was also buffered (files empty). **Use at most one light echo, with `PYTHONUNBUFFERED=1`.**

## 5. Exact details
Goal history today:
- Old home: goal (1, 0) crept 0.21→0.34 m in ~3 min → `controller_server: Failed to make progress` (progress checker 0.5 m in 10 s).
- New home, goal (-2.175, 0.185): `Begin navigating from current location (-1.31, -0.30) to (-2.17, 0.18)`, aborted after 2.5 s:
  ```
  [controller_server]: Unable to transform robot pose into global plan's frame
  [tf_help]: Transform data too old when converting from map to odom
  [tf_help]: Data time: 1794316199s 912486921ns, Transform time: 1794316199s 541603106ns
  [controller_server]: Failed to transform end pose to global frame
  ```
  The motor watchdog stopped 1.7 s after the abort. **The user saw ~0.8 m of motion; the localiser said the robot ended at (-1.518, -0.169, 140.9°), ≈0.25 m from start.** Unexplained (section 7).
- Lidar not spinning (rf2o `Waiting for laser_scans....`): two launches overlapped, and the old one's shutdown stopped the lidar motor. Fixed live with `ros2 service call /start_motor std_srvs/srv/Empty "{}"` (/scan back to 7.6 Hz), but Nav2 was then stuck on `Waiting for service waypoint_follower/get_state...`, so a full restart was needed. Rule: one launch at a time, Ctrl+C, wait for the prompt, wait 20 s.

Commands:
```bash
# launch (live motors; user runs it in the foreground)
ros2 launch delivery_bot_bringup navigation.launch.py dry_run:=false bridge:=false
# 1 m forward in the robot's own frame
ros2 action send_goal --feedback /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: base_footprint}, pose: {position: {x: 1.0, y: 0.0}, orientation: {w: 1.0}}}}"
# same target in map frame from home
ros2 action send_goal --feedback /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: -2.175, y: 0.185}, orientation: {z: 0.968, w: 0.250}}}}"
# pose check
ros2 run tf2_ros tf2_echo map base_footprint
# localisation-only check (dry run, no Nav2), used for the mark check
ros2 launch delivery_bot_bringup navigation.launch.py nav:=false bridge:=false
```
- Pi helper `/tmp/loc_check.py` (not in the repo): 25 s of pose plus scan-to-map distance (numpy).
- Logs: `~/.ros/log/{bt_navigator,controller_server,lifecycle_manager,collision_monitor}_<pid>_*.log`; motor_node is `python3_<pid>_*.log` (logs `watchdog: no /cmd_vel for 0.52 s, stop`).
- Figures (in PR 46): `results/maps/2026-11-10_home_clearance.png`, `results/maps/2026-11-10_new_home.png`.

Motor facts (`delivery_bot_drivers/config/drivers.yaml`, teammate's): duty = `min_duty 0.08 + gain 0.41 × v`; rolling floor duty 0.12 ≈ 0.094–0.10 m/s, duty 0.10 stalls; kick 0.30 for 0.35 s, **only when the wheel starts from duty 0**.

Nav2 settings relevant to the stall (ours, `nav2_params.yaml`): RPP `desired_linear_vel 0.15`, `min_approach_linear_velocity 0.05`, `approach_velocity_scaling_dist 0.6`, `regulated_linear_scaling_min_speed 0.05`, `rotate_to_heading_angular_vel 1.0`; collision_monitor `slowdown_ratio 0.3`, `transform_tolerance 0.2`; progress_checker 0.5 m / 10 s; goal checker xy 0.10, yaw 0.3.

## 6. Corrections & gotchas
- "Restarted" once when the stack had not actually restarted (same launch PID). Check with `ps -eo pid,lstart,cmd | grep "[r]os2 launch"` before trusting it.
- Never start a second launch while one is running: it breaks the lidar.
- Heavy monitoring on the Pi kills Nav2 (heartbeat). Keep diagnostics minimal.
- After any run the robot's map pose is off: put it back on the tape before the next goal and stack restart.
- `pgrep -f "<pattern>"` over ssh also matches the ssh command itself (count is +1).

## 7. Open issues & unknowns
- **0.8 m seen vs 0.25 m localised.** Either rf2o under-read (OI-8: a person behind the robot gives 25–30 % of the true distance), or a speed overshoot (0.8 m in ~4 s ≈ 0.2 m/s > the 0.15 cap). The user didn't say whether it was taped or by eye, or whether someone stood behind the robot. Measure with a tape next run.
- **Stall floor (hypothesis, not yet measured):** Nav2 can command < 0.10 m/s (approach scaling down to 0.05, slowdown 0.045, curvature min 0.05, rotate in place gives a wheel 0.078 m/s), and the wheels stall without a re-kick. Expect it to stop short in the last ~0.6 m. Our-side fix: `min_approach_linear_velocity` and `regulated_linear_scaling_min_speed` → 0.10, `slowdown_ratio` → ~0.7, maybe `rotate_to_heading_angular_vel` up. Motor-side fix (teammate): never write a nonzero duty < 0.12, or re-kick a stalled wheel.
- collision_monitor `transform_tolerance` is still 0.2 (OI-12 earlier showed it stopping on "invalid source"); not raised yet.
- PR 46 CI not checked; the Pi must go back to `main` after the merge.
- `notes/notes.md` has the home-move entry; the tolerance change and today's goal results aren't in notes or `docs/test_log.md` yet. Also update `docs/system/06_troubleshooting.md` (the costmap TF-too-old row, the lidar overlap/`/start_motor` row) and the 9.3 OI-12 line in `docs/slam_build_path.md`.

## 8. Next steps
**For the new chat — in order:**
1. Confirm the stack was restarted (the launch start time is after cd44057 was built) and that the robot sits on the mark: `tf2_echo map base_footprint` ≈ (-1.3, -0.3, ~2.6 rad).
2. The user sends the 1 m robot-frame goal. Afterwards read the `bt_navigator`/`controller_server` logs and the final pose, and get the tape distance and sideways drift from the user.
3. If it stops short with `Failed to make progress`: apply the Nav2 minimum-speed fix (section 7) on `fix/home-pose` (or a new branch), add a config test, push, then on the Pi `git pull` and `colcon build --packages-select delivery_bot_bringup delivery_bot_slam`, restart, retry.
4. If it aborts on TF again: raise collision_monitor `transform_tolerance` and check `slam_localization.yaml` `transform_publish_period`.
5. When it succeeds: goal back to home, (-1.3, -0.3, 2.635). Then add `docs/test_log.md` rows and a notes entry, check CI on PR 46, and merge (the user decides).

**For the user (outside the chat):**
- Ctrl+C the 21:09 stack, robot on the tape, wait 20 s, launch, wait for `Managed nodes are active` + 10 s, keep the motor switch within reach and nobody behind the robot.
- Tape-measure every run (distance and sideways drift).
- Charge the motor battery (it fades after about one run per cycle).

## 9. Working preferences
Terse, direct replies with no filler. Do the work (commands over ssh, edits, PRs) rather than explaining; give runnable commands in their own `bash` blocks. Read-only checks on the Pi are fine at any time; the user starts and stops the live stack and sends goals. Keep diffs minimal, and every number comes with the command that produced it.

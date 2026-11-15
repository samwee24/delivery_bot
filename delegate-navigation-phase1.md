# Task: Navigation phase 1 — Nav2 in the stack, Foxglove navigation view, goal scripts (no motors)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Bring Nav2 up on the robot and make it fully visible and controllable from Foxglove, **before the motors exist**. When done: one Foxglove button starts a navigation stack (base + slam_toolbox localisation + Nav2); a committed Foxglove layout shows the map, costmaps, global and local plans, collision-monitor zones, robot footprint and the velocity commands; you can click a goal in Foxglove and see a path planned and `/cmd_vel` published (nothing moves: no motor node exists). `save_goal` and `deliver` work so the next robot session can save seat goals and run a delivery by hand-pushing. This is build-path stage 7/8 and CA3 phase P7 groundwork.

## Context
- Project: CA3 room delivery robot. Raspberry Pi 4B (4 GB), Ubuntu 24.04, **ROS 2 Jazzy**, RPLIDAR A1M8, rf2o + IMU fused by `robot_localization`, `slam_toolbox` localisation on a saved map, Nav2 1.3.13 (installed on the Pi: navigation2, nav2-bringup, nav2-simple-commander, nav2-collision-monitor, opennav-docking). **Read `AGENTS.md` first**; its rules apply (config not constants, notes append-only, evidence append-only, PR title format `type: YYYY-MM-DD what`, every number with its command, definition of done = pytest for logic).
- Mac working directory: `/Users/shermanwee/Documents/MA4890/delivery_bot`. The Mac has **no ROS and no PyYAML**: edit on the Mac, run builds and tests on the Pi.
- Pi: `ssh robot@100.83.14.99` (key auth). Repo on Pi: `~/ros2_ws/src/delivery_bot/`. SSH is non-interactive: start every remote command with `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash;`. The Pi **pulls your branch**, it never edits files.
- Build and test on the Pi: `cd ~/ros2_ws && colcon build --symlink-install --packages-skip multirobot_map_merge && colcon test --packages-skip multirobot_map_merge explore_lite && colcon test-result --verbose`, and for the non-package tools: `cd ~/ros2_ws/src/delivery_bot && python3 -m pytest tools/tests -q`.
- Foxglove: bridge runs inside `base.launch.py` (port 8765). `tools/robot_control.py` runs separately on the Pi (systemd user unit or by hand) and offers stack buttons.
- Key files:
  - `delivery_bot_bringup/launch/navigation.launch.py` — today: base + slam_toolbox localisation as a LifecycleNode (configure via TimerAction 5 s, activate on `inactive`). Docstring says Nav2 comes later. Map arg default `~/maps/2026-10-31_room2_graph`.
  - `delivery_bot_bringup/config/nav2_params.yaml` — Nav2 params: RPP controller 0.15 m/s, robot_radius 0.12, odom `/odometry/filtered`, frame `base_footprint`, velocity_smoother → `cmd_vel_smoothed` → `collision_monitor` (stop / slowdown / approach polygons, `visualize: true`) → `cmd_vel`. AMCL removed on purpose.
  - `delivery_bot_slam/test/test_launch_files.py`, `delivery_bot_slam/test/test_config_consistency.py` — existing launch/config tests; add to these, match their style.
  - `tools/robot_control.py` + `tools/tests/test_robot_control.py` — stack buttons (`STACKS` dict around line 57: `'localisation': (LAUNCH + 'navigation.launch.py bridge:=false', 'stack')`), routes around line 181, `stack_state()` line 130, docstring lists services and `/robot/status/stack` values.
  - `delivery_bot_mission/delivery_bot_mission/save_goal.py`, `deliver.py` — stubs (`raise NotImplementedError`) with docstrings describing the intended behaviour; entry points already in `setup.py`. `delivery_bot_mission/config/goals.yaml` holds only `home: {x: 0, y: 0, yaw: 0}`.
  - `docs/foxglove/*.json` (`slam_layout.json`, `cockpit_layout.json` for button/Indicator patterns), `docs/foxglove/README.md`, `tools/tests/test_layouts.py` (Indicator paths must name a field, e.g. `/robot/status/stack.data`).
  - `docs/test_log.md` (row format: `Date | Commit | Phase | Test | Result | Numbers | Notes`), `notes/notes.md` (newest block on top, append-only), `docs/slam_build_path.md` stage 7/8, `docs/system/06_troubleshooting.md` (add any new error with exact text).

## Before you start (user does this, confirm with them)
- PR 23 (`nav/collision-zones`, adds collision monitor zones to `nav2_params.yaml`) and PR 24 (OI-8) are **merged** into `main`. Check with `gh pr view 23 --json state` and `gh pr view 24 --json state`; if either is not `MERGED`, stop and ask the user to merge.
- Robot on, lidar spinning, charged battery, robot sitting on the taped home mark. No motors are connected or needed.

## Decisions already made (do not revisit)
- Nav2 comes from `nav2_bringup/launch/navigation_launch.py` (not `bringup_launch.py`, which would start AMCL and map_server; slam_toolbox already provides `/map` and `map → odom`).
- Pass `use_composition: 'False'` (standalone navigation_launch has no container to load into), `autostart: 'true'`, `params_file` = our `nav2_params.yaml`, `use_sim_time` forwarded.
- Nav2 must start only **after** slam_toolbox reaches `active` (otherwise the costmaps start without `/map` / `map → odom`). Use a second `OnStateTransition` handler (`goal_state='active'`) whose entities include the Nav2 launch. No fixed sleep.
- New launch argument `nav` (default `'true'`) gates the Nav2 include, so `navigation.launch.py nav:=false` is today's localisation-only stack.
- `robot_control.py`: `'localisation'` becomes `navigation.launch.py bridge:=false nav:=false`; add `'navigation'` = `navigation.launch.py bridge:=false nav:=true`, service `/stack/navigation`, and `navigation` as a `/robot/status/stack` value. The real motor node does not exist; **never** add `dry_run:=false` anywhere.
- Foxglove: a **new** file `docs/foxglove/navigation_layout.json` (same style as `slam_layout.json`), not a tab in the cockpit. Goals are sent with the 3D panel's publish tool on `/goal_pose` (bt_navigator listens there); initial pose on `/initialpose` as today.
- `deliver.py` uses `nav2_simple_commander.robot_navigator.BasicNavigator` (`goToPose`, `isTaskComplete`, `getResult`, `cancelTask`). Goals in order, then `home`. Per-goal optional `wait_s` in goals.yaml, else ROS parameter `wait_s` (default 5.0). Keep pure helpers (YAML loading, `{x,y,yaw}` → pose fields, yaw ↔ quaternion) free of rclpy so they are unit-testable.
- `save_goal.py` uses tf2 (`map` → `base_footprint`), writes `{x, y, yaw}` rounded to 3 decimals into goals.yaml, keeps all existing entries, refuses to overwrite an existing name unless parameter `overwrite:=true`.
- Do not tune Nav2 parameters in this phase. If something looks wrong (CPU, costmap, controller), record it and report; the planner decides.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 1: Sync and branch
- Do: `git checkout main && git pull`, then `git checkout -b nav/nav2-foxglove`. Leave untracked files (`reports/`, `research_notes/`, `delegate-*.md`) alone.
- Verify: `git log --oneline -3` includes the PR 23 and PR 24 merge commits; `grep -c collision_monitor delivery_bot_bringup/config/nav2_params.yaml` > 0.
- Done when: on the new branch from an up-to-date main.

### Step 2: Nav2 in navigation.launch.py
- Do: add the `nav` argument and the Nav2 include as decided (second OnStateTransition on `active`, `IfCondition(nav)`), passing `params_file`, `use_sim_time`, `autostart`, `use_composition`. Update the module docstring: remove "Nav2 is added in stage 7/8", describe `nav:=false`. Add tests to `delivery_bot_slam/test/test_launch_files.py` in the existing style: Nav2 include present and gated by `nav`, `use_composition` False, params file is `nav2_params.yaml` from `delivery_bot_bringup`, no AMCL/map_server node started, `nav` defaults to `true`.
- Verify: commit, push the branch; on the Pi `cd ~/ros2_ws/src/delivery_bot && git fetch && git checkout nav/nav2-foxglove && git pull`, then the build/test command from Context → all pass.
- Done when: build clean, new tests pass, a deliberately broken gate (e.g. drop the condition locally) would fail a test (reason it out; don't commit that).

### Step 3: Live bring-up check on the Pi (robot still, no motors)
- Do: stop any running stack (`/stack/stop` via `ros2 service call /stack/stop std_srvs/srv/Trigger` if robot_control runs, else check `ps` and ask the user before killing anything). Start `ros2 launch delivery_bot_bringup navigation.launch.py` in the background (setsid nohup, log to `/tmp/nav.log`). Wait ~60 s. Ask the user to set the initial pose in Foxglove (3D panel, "Publish pose estimate" on the home mark, facing along +x) if the scan does not already sit on the map.
- Verify, record each output:
  - `grep -E "Managed nodes are active|Failed|error" /tmp/nav.log | head` → "Managed nodes are active" for the navigation lifecycle manager; no node failed to configure. If `route_server` or `docking_server` fails configure, stop and report the exact line (do not remove them yourself).
  - `ros2 topic list | grep -E "plan|costmap|cmd_vel|collision|polygon|footprint"` → note the exact topic names (needed for the layout).
  - `ros2 run tf2_ros tf2_echo map base_footprint` → a transform; `ros2 topic info /tf` shows no new publisher of `odom → base_footprint` besides `ekf_filter_node` (check with `ros2 run tf2_tools view_frames` if unsure).
  - Send a goal 1 m ahead: `ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0}, orientation: {w: 1.0}}}}" &` then `ros2 topic echo /plan --once | head -20` (path exists) and `ros2 topic hz /cmd_vel` (≈10 Hz, linear.x ≤ 0.15). Then cancel (Ctrl+C the send_goal / `ros2 action` cancel).
  - Collision stop: send the goal again, ask the user to hold a box or hand 10–15 cm in front of the lidar; `ros2 topic echo /cmd_vel --once` → linear.x 0.0 and `/collision_monitor_state` shows the stop action. Cancel the goal.
  - Load: `uptime`, `top -bn1 | head -15`, `vcgencmd get_throttled` with the stack running; grep `/tmp/nav.log` for `Failed to meet update rate|Control loop missed`.
- Done when: all checks recorded with numbers. Stack can stay running for step 6.

### Step 4: robot_control navigation stack
- Do: as decided (STACKS entry, `/stack/navigation` route, `stack_state` includes `navigation` and checks it before `localisation` if the process patterns overlap, docstring lists). Update `tools/tests/test_robot_control.py` so it covers the new stack, its command line has `nav:=true`, localisation has `nav:=false`, and no command contains `dry_run:=false`.
- Verify: Pi `python3 -m pytest tools/tests -q` → pass. Restart robot_control on the Pi (`systemctl --user restart robot-control` if the unit exists, else ask the user how it is running) and `ros2 service list | grep /stack/navigation`.
- Done when: tests pass; calling `/stack/navigation` starts the stack and `/robot/status/stack` reads `navigation`.

### Step 5: save_goal and deliver
- Do: implement `save_goal.py` and `deliver.py` per their docstrings and the decisions. Add `delivery_bot_mission/test/test_goals.py`: yaw ↔ quaternion round-trip (0, ±π/2, π), goals loading (missing name → clear error, `home` required), pose conversion (`x, y, yaw` → position/orientation), save keeps existing entries and refuses overwrite without the flag. Add `nav2_simple_commander`, `tf2_ros`, `python3-yaml` as `exec_depend` in `delivery_bot_mission/package.xml` if missing.
- Verify: Pi build + `colcon test --packages-select delivery_bot_mission && colcon test-result --verbose` → pass. Live, stack running: `ros2 run delivery_bot_mission save_goal --ros-args -p goals_file:=/tmp/goals_test.yaml test_spot` (copy goals.yaml there first) → `/tmp/goals_test.yaml` has `test_spot` near 0,0. `ros2 run delivery_bot_mission deliver --ros-args -p goals_file:=/tmp/goals_test.yaml -- test_spot` → goal accepted, plan published, then Ctrl+C cancels cleanly (robot cannot move, so it will not arrive; that is expected).
- Done when: tests pass, both commands behave as above. Do **not** write real seat goals into the committed goals.yaml (that is phase 2).

### Step 6: Foxglove navigation layout
- Do: write `docs/foxglove/navigation_layout.json`, following `slam_layout.json` structure and `cockpit_layout.json` for buttons/Indicators. Panels:
  - 3D (follow `base_footprint`, fixed frame `map`, top-down): `/map`, `/global_costmap/costmap` and `/local_costmap/costmap` (costmap colour mode), `/plan` (global), `/local_plan` (or the RPP lookahead/`/received_global_plan`, whichever exist from step 3), `/scan`, the three collision-monitor polygon topics, `/local_costmap/published_footprint`, robot model, TF. Publish tool set to pose `/goal_pose`, pose-estimate `/initialpose`.
  - Plot: `/cmd_vel.linear.x`, `/cmd_vel.angular.z`, `/cmd_vel_smoothed.linear.x`, `/odometry/filtered.twist.twist.linear.x`.
  - Indicators: `/robot/status/stack.data`, collision monitor state action field (exact field from `ros2 interface show nav2_msgs/msg/CollisionMonitorState`), `/robot/status/undervolt.data`.
  - Buttons (Call Service, `std_srvs/srv/Trigger`): `/stack/navigation`, `/stack/localisation`, `/stack/stop`.
  - Raw Messages: `/navigate_to_pose/_action/feedback` (distance remaining) or `/behavior_tree_log` if feedback is not visible.
  Add a "Navigation layout" section to `docs/foxglove/README.md`: what each panel shows and what "wrong" looks like (path through a wall = map/frame problem; costmap not on walls = TF; `/cmd_vel` zero while plan exists = collision monitor or controller).
- Verify: Pi `python3 -m pytest tools/tests/test_layouts.py -q` → pass. `python3 -c "import json;json.load(open('docs/foxglove/navigation_layout.json'))"` → no error. Then ask the user to import it in Foxglove (Layouts → Import) with the stack running, click a goal 1 m ahead, and tell you what they see: map + costmaps + path + zones + `/cmd_vel` plot moving. Fix only what the user reports missing (topic name typos), max 2 rounds.
- Done when: user confirms the path, costmaps and zones are visible and a clicked goal produces a plan and `/cmd_vel`.

### Step 7: Record and PR
- Do: on the Mac:
  - `docs/test_log.md`: dated rows for step 3 checks (lifecycle active, plan, `/cmd_vel` rate and max, collision stop, load/throttled), step 5 commands, step 6 Foxglove confirmation. Commit = the hash under test.
  - `notes/notes.md`: new top block `## <date> (Pi, live) · Nav2 up without motors, Foxglove navigation view`, numbers + what's next.
  - `docs/slam_build_path.md` stage 7/8 and `docs/CA3.md` P7 row: status "Nav2 runs and plans without motors (<date>)"; P7 itself stays not done.
  - `docs/system/06_troubleshooting.md`: any new error hit, with exact text.
  - Stop the stack on the Pi (`/stack/stop`), `git checkout main` on the Pi.
- Verify: `git diff --stat main` touches only the files named in this prompt; `git diff main -- notes/notes.md` has only added lines.
- Then ask the user "Open the PR?". On yes: `gh pr create --base main --title "nav: <date> Nav2 in the navigation stack, Foxglove navigation layout, goal scripts"`; body = summary, Pi commands with results (rule 6), tests added. End the body with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Wait for `gh pr checks` → all green; if a check fails, read the log and fix within these files (max 2 attempts). Do not merge.
- Done when: PR open, CI green.

## Out of scope
Do not change: `nav2_params.yaml` values (no tuning), `slam_localization.yaml`, `slam_mapping.yaml`, `ekf.yaml`, `base.launch.py`, `motor_node.py` and anything else under `delivery_bot_drivers/` (motors belong to a teammate), the URDF, old rows/blocks in `docs/test_log.md` / `notes/notes.md`, anything existing in `evidence/`, the committed `goals.yaml`.
Do not add: a motor node or any GPIO code, `dry_run:=false` anywhere, AMCL or map_server, new third-party packages beyond the Nav2 ones already installed, extra Foxglove layouts beyond `navigation_layout.json`.
Never let anything publish to the motors; there is no motor node and that is intended.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file, topic or function doesn't exist, a Nav2 node fails to configure, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found, quoting the shortest decisive error line.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- When the user must do something physical or in Foxglove, give one short numbered instruction at a time and wait for their reply.
- Trivial things a step obviously needs (an import, a missing exec_depend) you may handle; list each under Deviations.
- Commit after each step that changes files, message `<type>: <date> <what>` (e.g. `nav: 2026-11-04 Nav2 include gated by nav arg`), each ending with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Push the branch after each commit so the Pi can pull it.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: Navigation phase 1

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 1: Sync and branch — <one line>
- [ ] ...

### Verification results
<each verify command you ran and its result (pass/fail, key output lines and numbers)>

### Topic names found (step 3)
<exact plan / costmap / polygon / footprint / collision-state topics>

### Files changed
- `<path>` — <what changed>

### Deviations
<"None" if none>

### Problems / open questions
<CPU load, missed control loops, anything the planner must decide; "None" if none>
```

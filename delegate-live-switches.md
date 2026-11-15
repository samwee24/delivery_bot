# Task: Live config switches and run sheet for the driven experiments (plan H)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Make every method of the CA3 experiments selectable by a launch argument on the real robot, and add the two tools that make 50+ live runs consistent: a timed-motion script and a run sheet. When done: `navigation.launch.py` can start the stack with any of four odometry configs (rf2o + IMU, rf2o only, IMU only, no EKF) and either localiser (`slam_toolbox` or AMCL); `tools/timed_move.py` drives an open-loop 1 m straight or 360° spin through Nav2's collision monitor; `tools/run_cell.py` starts one experiment cell, records its bag and prints the test_log row. All logic has tests; a smoke run on the Pi shows each switch starts; a PR is open. This is the "build before the driven session" list (`docs/slam_build_path.md` Progress 9.2) for the experiments in `docs/report_plan.md` §4 (plan H: every method run live, empty room vs people walking).

## Context
- Project: CA3 room delivery robot. Raspberry Pi 4B, Ubuntu 24.04, **ROS 2 Jazzy**, RPLIDAR A1M8, MPU6050, rf2o + IMU fused by `robot_localization` EKF, `slam_toolbox` localisation on a saved map, Nav2 1.3.x (`navigation_launch.py`, RPP controller, velocity_smoother → collision_monitor → `/cmd_vel`). **Read `AGENTS.md` first**; its rules apply (safety is structural, config not constants, every number with its command, `notes/notes.md` and `evidence/` append-only, PR title `type: YYYY-MM-DD what`, definition of done = pytest for logic). `docs/report_plan.md` and `docs/slam_build_path.md` may only exist on branch `docs/report-plan-matrix` (PR 31) if it is not merged: read them with `git show origin/docs/report-plan-matrix:<path>`.
- Mac repo: `/Users/shermanwee/Documents/MA4890/delivery_bot`. **Another session works in that checkout and switches its branches: do not work there.** Make your own worktree (Step 0). The Mac has **no ROS and no PyYAML**: edit on the Mac, build/test/run on the Pi.
- Pi: `ssh robot@100.83.14.99` (key auth). SSH is non-interactive: start every remote command with `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash;` and, after Step 0, `source ~/planh_ws/install/setup.bash`.
- **The Pi's main clone `~/ros2_ws/src/delivery_bot/` is on branch `test/motors-nav-2026-11-09`, used by a teammate's motor tests, and that branch's `base.launch.py` starts a live motor node. Do not switch, pull, edit, build or launch from it.** You get an overlay workspace `~/planh_ws` built on top of `~/ros2_ws` (Step 0). Your branch is cut from `main`, whose `base.launch.py` does not start any motor node, so launching your overlay cannot move the wheels.
- Key files (on `main`):
  - `delivery_bot_bringup/launch/base.launch.py` — lidar, rf2o (`publish_tf: false`), `odom_covariance_relay`, `imu_node`, `ekf_filter_node` (params `config/ekf.yaml`, line ~81), foxglove_bridge; args `dry_run`, `bridge`, `use_sim_time`, `serial_port`, `rf2o_delay`.
  - `delivery_bot_bringup/launch/navigation.launch.py` — includes base (arg `include_base`), then `slam_toolbox` localisation as a `LifecycleNode` (configure, then activate on `inactive`), then Nav2 `navigation_launch.py` in an `OnStateTransition(goal_state='active')` handler; args `use_sim_time`, `nav`, `bridge`, `include_base`, `map` (default `~/maps/2026-10-31_room2_graph`).
  - `delivery_bot_bringup/config/ekf.yaml` — baseline: `odom0: /odom_rf2o_cov` (vx, vyaw), `imu0: /imu/data` (vyaw), `frequency: 20.0`, `two_d_mode: true`.
  - `delivery_bot_bringup/config/nav2_params.yaml` — Nav2 params; line 8 says "AMCL is removed: slam_toolbox localization provides map + map->odom". `collision_monitor` block (line ~275) names its input and output topics; read it.
  - `delivery_bot_bringup/CMakeLists.txt` — installs `launch` and `config` directories (subdirectories of `config/` are installed too; check).
  - `delivery_bot_slam/test/test_launch_files.py` — parses every launch file in `delivery_bot_bringup` and `delivery_bot_slam` (`generate()`, `walk()`, `nodes()`, `declared()` helpers); add launch tests here in the same style.
  - `delivery_bot_slam/test/test_config_consistency.py` — cross-file config checks (`share()`, `params()`, `MAX_SPEED = 0.15`); add config tests here.
  - `tools/tests/` — pytest for `tools/` scripts (see `test_push_an.py` for style); `tools/robot_control.py` for how the repo starts stacks with `subprocess`.
  - Maps on the Pi: `~/maps/2026-10-31_room2.yaml` + `.pgm` (occupancy grid, for AMCL's `map_server`) and `~/maps/2026-10-31_room2_graph.{posegraph,data}` (for `slam_toolbox`). Both come from the same 2026-10-31 mapping run.
  - `.github/pull_request_template.md` — its checklist forbids a `/cmd_vel` publisher outside the motor node (see decisions).

## Decisions already made (do not revisit)
- **EKF variants** live in `delivery_bot_bringup/config/ekf_variants/`: `rf2o_imu.yaml` (copy of `ekf.yaml`), `rf2o_only.yaml` (no `imu0` block), `imu_only.yaml` (no `odom0` block; position never moves in the EKF, scan matching does translation, which is the point). Each gets a one-line header comment naming its inputs and "E2 variant". `ekf.yaml` itself is not edited.
- **`base.launch.py`** gains `ekf_params_file` (default: the installed `config/ekf.yaml`, so default behaviour is unchanged) and `ekf` (default `'true'`). `ekf:=false` skips `ekf_filter_node` and starts `tf2_ros static_transform_publisher` with identity `odom → base_footprint` instead (the "none" config: slam_toolbox does pure scan matching). Because `robot_localization` with zero inputs is not something to rely on. Keep the edit small and away from other lines: branch `feat/motors` rewrites much of this file and will be rebased onto yours.
- **`navigation.launch.py`** gains `ekf_params_file` and `ekf` (forwarded to the base include) and `localizer` (default `'slam'`, the current behaviour; or `'amcl'`). For `amcl`: do not start slam_toolbox; start `nav2_map_server` `map_server` with `yaml_filename` = new arg `map_yaml` (default `~/maps/2026-10-31_room2.yaml`, expanded), `nav2_amcl` `amcl` with params from a **new file** `delivery_bot_bringup/config/amcl.yaml`, and a `nav2_lifecycle_manager` `lifecycle_manager_localization` (`autostart: true`, `node_names: [map_server, amcl]`). Nav2 must start only after localisation is up in both branches: for `slam`, keep the existing `OnStateTransition(goal_state='active')` handler; for `amcl`, start Nav2 from a `TimerAction` of 5 s after the lifecycle manager (the lifecycle manager has no state transition event to hook). `nav2_params.yaml` is not edited, and its "AMCL is removed" comment stays true for the default.
- **`amcl.yaml`** (node `amcl`): `base_frame_id: base_footprint`, `odom_frame_id: odom`, `global_frame_id: map`, `scan_topic: scan`, `robot_model_type: nav2_amcl::DifferentialMotionModel`, `laser_model_type: likelihood_field`, `max_beams: 60`, `min_particles: 500`, `max_particles: 2000`, `set_initial_pose: true`, `initial_pose: {x: 0.0, y: 0.0, z: 0.0, yaw: 0.0}` (the robot starts on the taped home mark, which is 0, 0, 0 in `goals.yaml`), `tf_broadcast: true`, `transform_tolerance: 1.0`, `update_min_d: 0.05`, `update_min_a: 0.1`. Everything else Nav2's default. Mark these in a header comment as *brief default* (not tuned).
- **Timed motion** `tools/timed_move.py straight|spin [--speed V]`: open loop, 20 Hz, then a zero command and exit. `straight`: 0.10 m/s for 10.0 s (1.00 m). `spin`: 0.5 rad/s for 2π/0.5 s (360°). Refuse `|v| > 0.15` m/s (AGENTS rule 1) and `|w| > 1.0` rad/s. It publishes on the **collision monitor's input topic** (read the name from `nav2_params.yaml`; expected `cmd_vel_smoothed`), never on `/cmd_vel`, so Nav2's collision monitor still stops it for obstacles and the PR-template rule "no `/cmd_vel` publisher outside the motor node" holds. It therefore needs the Nav2 stack running (`nav:=true`). Message type: a `--stamped` flag (default from what the collision monitor's input actually is; check in Step 6). Keep the motion profile (list of (t, v, w) or duration and speeds, caps) in a pure function the test imports without rclpy. Open loop on purpose: E2 compares odometry configs, so the motion must not depend on the estimator under test.
- **Run sheet** `tools/run_cell.py <exp> <cell> <run> [--dry]`: pure function `cell_plan(exp, cell)` returns the launch command and bag topics; `--dry` prints the plan only. Cells:
  - `E2`: cell `<config>_<cond>` with config `rf2o_imu|rf2o_only|imu_only|none` and cond `empty|people` → `navigation.launch.py nav:=true localizer:=slam` plus `ekf_params_file:=<installed ekf_variants/<config>.yaml>` or `ekf:=false` for `none`.
  - `E3`: cell `<loc>_<cond>` with loc `slam|amcl` → `navigation.launch.py nav:=true localizer:=<loc>` (baseline EKF). Also cell `<loc>_wrongstart`.
  - `E4`: cell `stepin` → `navigation.launch.py nav:=true localizer:=slam`.
  - `E1`: cell `demo` → same as E4.
  It starts the launch (`subprocess`, own process group), waits until `/odometry/filtered` (or `/tf` for `none`) is publishing (max 40 s), records `ros2 bag record -s mcap -o ~/bags/<YYYY-MM-DD>_<exp>_<cell>_run<N>` with topics `/scan /imu/data /odom_rf2o /odometry/filtered /tf /tf_static /cmd_vel /cmd_vel_smoothed /amcl_pose /pose /marker` (missing topics are fine), waits for Enter, then stops the bag and the launch with SIGINT and prints one `docs/test_log.md` row (date, `git rev-parse --short HEAD`, phase `9`, the exact launch command, `vcgencmd get_throttled` before and after, Result/Numbers left as `TODO`). It never passes `dry_run:=false`, never starts a motor node itself, and refuses to run if a bag with that name exists.
- Rejected: editing `ekf.yaml` or `nav2_params.yaml`; AMCL via `nav2_bringup/bringup_launch.py` (also starts its own Nav2 and map server); closed-loop Nav2 `driveOnHeading`/`spin` behaviours for E2 (with `imu_only` or `none` the odometry never reports the distance, so the robot would not stop); publishing on `/cmd_vel` directly.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 0: Isolated workspaces
- Do: Mac: `cd /Users/shermanwee/Documents/MA4890/delivery_bot && git fetch && git worktree add ../delivery_bot_planh -b nav/live-switches origin/main`; work only in `../delivery_bot_planh`. Pi: `mkdir -p ~/planh_ws/src && cd ~/planh_ws/src && git clone https://github.com/samwee24/delivery_bot.git`.
- Verify: `git -C ../delivery_bot_planh branch --show-current` → `nav/live-switches`; on the Pi `git -C ~/ros2_ws/src/delivery_bot branch --show-current` is still `test/motors-nav-2026-11-09`.
- Done when: both exist and the Pi's main clone is untouched.

### Step 1: EKF variants
- Do: create the three files as decided. In `test_config_consistency.py` add: each variant parses; any `odom0` is `/odom_rf2o_cov`; `rf2o_only` has no `imu0`; `imu_only` has no `odom0`; `rf2o_imu` equals `ekf.yaml` as parsed YAML. Confirm `CMakeLists.txt` installs `config/ekf_variants/` (if the `DIRECTORY config` rule already covers subdirectories, change nothing).
- Verify: commit, push, then on the Pi `cd ~/planh_ws/src/delivery_bot && git fetch && git switch nav/live-switches && cd ~/planh_ws && colcon build --symlink-install --packages-select delivery_bot_bringup delivery_bot_slam && colcon test --packages-select delivery_bot_slam && colcon test-result --verbose` → 0 failures; `ls ~/planh_ws/install/delivery_bot_bringup/share/delivery_bot_bringup/config/ekf_variants/` lists 3 files.
- Done when: tests pass and the variants are installed.

### Step 2: `ekf` and `ekf_params_file` in base.launch.py
- Do: as decided; update the module docstring's argument list. Tests in `test_launch_files.py`: both arguments exist with the decided defaults; the EKF node is conditional on `ekf`; a `static_transform_publisher` node exists, conditional on `ekf` being false, publishing `odom` → `base_footprint`; the existing `dry_run` default test still passes unchanged.
- Verify: Pi build and `colcon test` as in Step 1 → 0 failures.
- Done when: tests pass.

### Step 3: `localizer`, forwarding and AMCL in navigation.launch.py
- Do: create `amcl.yaml`; add the arguments and the AMCL branch as decided; update the docstring. Tests: `localizer` defaults to `slam`; `ekf` and `ekf_params_file` are declared and forwarded to the base include; `map_server`, `amcl` and `lifecycle_manager_localization` exist and are conditional on `localizer == amcl`; the slam_toolbox `LifecycleNode` is conditional on `localizer == slam`; Nav2's `navigation_launch.py` is still included (no `bringup_launch.py`). In `test_config_consistency.py`: `amcl.yaml` frames are `base_footprint`/`odom`/`map` and the initial pose is 0, 0, 0.
- Verify: Pi build and test → 0 failures.
- Done when: tests pass. Commit and push (checkpoint).

### Step 4: Timed motion script
- Do: write `tools/timed_move.py` as decided, plus `tools/tests/test_timed_move.py`: straight profile covers 1.00 m ± 0.01; spin covers 2π ± 0.01 rad; the last command is zero; speeds above the caps raise; the module imports without rclpy at top level.
- Verify: on the Pi `cd ~/planh_ws/src/delivery_bot && git pull && python3 -m pytest tools/tests -q` → all pass.
- Done when: tests pass.

### Step 5: Run sheet
- Do: write `tools/run_cell.py` as decided, plus `tools/tests/test_run_cell.py`: every listed cell maps to the decided launch command; `none` gives `ekf:=false`; unknown exp or cell raises; the bag name follows `<date>_<exp>_<cell>_run<N>`; no plan contains `dry_run`.
- Verify: Pi pytest → all pass; `python3 tools/run_cell.py E2 none_people 1 --dry` and `python3 tools/run_cell.py E3 amcl_empty 1 --dry` print the expected command.
- Done when: tests pass and the dry plans read right. Commit and push (checkpoint).

### Step 6: Smoke run on the Pi (no motion)
- Do: first check the Pi is free: `ros2 node list` on the default domain shows nothing and `pgrep -f rplidar` is empty. **If any stack is running, stop and report**: the lidar is shared and the teammate's branch drives motors. If free, ask the user (in your report-style message, then wait) to confirm the robot sits on the taped home mark and the motor switch is OFF. Then, with `export ROS_DOMAIN_ID=42` and only the `~/planh_ws` overlay sourced on top of `~/ros2_ws`, run each for about 30 s, then Ctrl+C:
  1. `ros2 launch delivery_bot_bringup navigation.launch.py nav:=true localizer:=slam bridge:=false` → `ros2 topic hz /odometry/filtered` ~20 Hz; `ros2 lifecycle get /slam_toolbox` → active; `ros2 node list` shows `collision_monitor`.
  2. Same with `ekf:=false` → no `ekf_filter_node`; `ros2 run tf2_ros tf2_echo odom base_footprint` shows identity; slam_toolbox active.
  3. Same with `ekf_params_file:=<installed>/ekf_variants/imu_only.yaml` → `ros2 param get /ekf_filter_node odom0` fails (parameter not set).
  4. `localizer:=amcl` → `ros2 lifecycle get /amcl` and `/map_server` → active; `ros2 topic echo /amcl_pose --once` near (0, 0); `ros2 run tf2_ros tf2_echo map base_footprint` near (0, 0) with the robot on the home mark. Compare with the `map → base_footprint` from run 1: both should be within about 0.2 m of each other; report both numbers.
  5. With run 1's stack up: `ros2 topic info /cmd_vel_smoothed -v` and `ros2 topic info /cmd_vel -v` → record the message type of each publisher and subscriber; set `timed_move.py`'s `--stamped` default to match the collision monitor's input and re-run the Step 4 tests. Then `python3 tools/timed_move.py straight` while `ros2 topic echo /cmd_vel` shows commands coming out of the collision monitor (no motor node runs on `main`, so nothing moves).
- Verify: each check above as stated; record each command and result.
- Done when: all five pass, or the failing one is reported with its exact error text.

### Step 7: Records and PR
- Do: add one `docs/test_log.md` row per smoke check in Step 6 (date, commit, phase `9`, exact command, result, numbers). Add a `notes/notes.md` block on top (newest first, under the `---`; never edit old blocks). In `docs/system/05_config_reference.md` add the `amcl.yaml` values and the three EKF variants with provenance *brief default*. In `docs/slam_build_path.md` Progress 9.2 (if the file exists on `main`; if not, skip and say so), tick the items you finished with the date and a pointer to the test_log rows. If you hit a new error, add it with its exact text to `docs/system/06_troubleshooting.md`. Open a PR from `nav/live-switches` to `main`, titled `nav: <today YYYY-MM-DD> live switches: EKF variants, ekf:=false, AMCL localizer, timed_move, run_cell`, using the repo PR template; state that `tools/timed_move.py` publishes on the collision monitor's input, not `/cmd_vel`, and that `feat/motors` will need a rebase over `base.launch.py`.
- Verify: on the Pi `colcon test --packages-select delivery_bot_slam && colcon test-result --verbose` and `python3 -m pytest tools/tests -q` in `~/planh_ws` pass; `git diff origin/main --stat` lists only the files below.
- Done when: the PR is open; report its URL.

## Out of scope
Do not change: `delivery_bot_bringup/config/ekf.yaml`, `nav2_params.yaml`, `slam_localization.yaml`, `slam_mapping.yaml`, anything in `delivery_bot_drivers/` (the motor node belongs to the teammate's `feat/motors`), `delivery_bot_mission/`, `tools/robot_control.py`, `mapping.launch.py`, `explore.launch.py`, CI config, old `notes/notes.md` blocks, existing `evidence/` files, `docs/report_plan.md`, `report/*`. Never touch the Pi's `~/ros2_ws/src/delivery_bot` clone, never start a motor node, never pass `dry_run:=false`, never drive the robot.
Do not add: Foxglove buttons for the new arguments, tuning of AMCL or Nav2 beyond the decided values, waypoint or loop-driving scripts, new pip/apt packages.

Files you should end up touching: `delivery_bot_bringup/config/ekf_variants/{rf2o_imu,rf2o_only,imu_only}.yaml`, `delivery_bot_bringup/config/amcl.yaml`, `delivery_bot_bringup/launch/{base,navigation}.launch.py`, possibly `delivery_bot_bringup/CMakeLists.txt`, `delivery_bot_slam/test/{test_launch_files,test_config_consistency}.py`, `tools/{timed_move,run_cell}.py`, `tools/tests/{test_timed_move,test_run_cell}.py`, `docs/test_log.md`, `notes/notes.md`, `docs/system/05_config_reference.md`, maybe `docs/system/06_troubleshooting.md`, maybe `docs/slam_build_path.md`.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, the code is structured differently, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a missing type annotation, a typo in the instructions) you may handle; list each one under Deviations in the report.
- Commit after each step with message `step N: <title>` on `nav/live-switches`, and push so the Pi can pull. The Pi never commits.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: Live config switches and run sheet

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 0: Isolated workspaces — <one line>
- [x] Step 1: EKF variants — <...>
- [ ] Step N: <title> — <why not done>

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Smoke numbers
<amcl_pose and map->base_footprint with each localiser on the home mark; message types on /cmd_vel_smoothed and /cmd_vel (publishers and subscribers); EKF rate>

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what you found that contradicts the plan, what the planner needs to decide; "None" if none>
```

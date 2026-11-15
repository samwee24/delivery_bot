# Task: Replay matrix phase 1 — odometry configs (E2) and lidar degradation (E5) on existing bags

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Build an offline replay harness that runs the same recorded lidar/IMU bags through several estimator configurations and scan degradations, then run it on the bags that already exist on the robot's Pi. When done: four EKF variant configs, a scan-degradation node, a batch runner and an analysis script exist with tests; a results CSV and a dated evidence log hold distance/yaw per (bag, config, degradation, replay); `docs/test_log.md` and `notes/notes.md` record it; a PR is open. This feeds the CA3 report's RQ2 ("which odometry matters, and when?") and RQ1 ("how cheap can the lidar be?"); the plan is `docs/report_plan.md` §3–4 (on branch `docs/report-plan-matrix`, PR 31, maybe not merged yet: read it with `git show origin/docs/report-plan-matrix:docs/report_plan.md`).

## Context
- Project: CA3 room delivery robot. Raspberry Pi 4B (4 cores, 3.7 GB RAM), Ubuntu 24.04, **ROS 2 Jazzy**, RPLIDAR A1M8, MPU6050 IMU, rf2o laser odometry + IMU fused by `robot_localization` EKF, `slam_toolbox`. **Read `AGENTS.md` first**; its rules apply (config not constants, every number with its command, `notes/notes.md` and `evidence/` append-only, PR title `type: YYYY-MM-DD what`, definition of done = pytest for logic).
- Mac repo: `/Users/shermanwee/Documents/MA4890/delivery_bot`. **Another session is working in that checkout and switches branches in it.** Do not work there: create your own worktree (Step 0). The Mac has **no ROS and no PyYAML**: edit on the Mac, build/test/run on the Pi.
- Pi: `ssh robot@100.83.14.99` (key auth). SSH is non-interactive: start every remote command with `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash;` (plus the matrix overlay, Step 0).
- **The Pi's main clone `~/ros2_ws/src/delivery_bot/` is on branch `test/motors-nav-2026-11-09`, in use by a teammate's motor tests. Do not switch, pull, edit or build in it.** You get your own overlay workspace (Step 0).
- Bags: `~/bags` on the Pi only, MCAP. Use exactly these six:
  - `2026-10-31_push_195343` — 1.000 m tape push, live rf2o read 0.962 m in window 39–50 s (test_log row "live push on the good bag by window")
  - `2026-10-31_turn_194945` — one hand-turned full turn (360°), 148 s
  - `2026-11-01_push_225752` — ~1.00 m push, a person walked behind the robot
  - `2026-11-01_push_230535` — 1.20 m push, a person walked behind the robot
  - `2026-11-03_135611_push_actrue` — 1.000 m push, nobody in the scan, `angle_compensate:=true`
  - `2026-11-03_140352_push_acfalse` — 1.000 m push, nobody in the scan, `angle_compensate:=false` (17.5 s)
  All carry `/scan`, `/imu/data`, `/tf`, `/tf_static`, `/odom_rf2o`. Push/turn windows (t0, t1 in s from the first `/scan`) are in `docs/test_log.md` rows for each bag; the 11-03 ones are in the OI-8 rows of 2026-11-03.
- Key files:
  - `delivery_bot_slam/launch/slam_replay.launch.py` — offline replay: rf2o (`publish_tf: false`) → `odom_covariance_relay` → `ekf_filter_node` → `slam_toolbox` → `trajectory_recorder`; args `slam_mode`, `ekf_params_file`, `foxglove`, `tum_output_dir` (writes `odom_*.tum` = `/odometry/filtered` and `slam_*.tum` = map pose on shutdown), `use_sim_time` default true. Read its docstring: play only `/scan /imu/data /tf_static`, never `/tf`.
  - `delivery_bot_bringup/config/ekf.yaml` — baseline: `odom0: /odom_rf2o_cov` with vx and vyaw, `imu0: /imu/data` with vyaw only, `frequency: 20.0`, `two_d_mode: true`.
  - `delivery_bot_slam/delivery_bot_slam/trajectory_recorder.py` — TUM writer (format: `t x y z qx qy qz qw`).
  - `tools/analysis/rf2o_fmt.sh` — the existing replay pattern to copy: `export ROS_DOMAIN_ID=42`, `setsid nohup` nodes, `ros2 bag play $BAG --clock --topics ...`, `--remap /scan:=/scan_raw` when a scan filter node sits in between, `pkill` cleanup, `vcgencmd get_throttled` logged.
  - `tools/analysis/scan_minrange.py` — the existing scan filter pattern (`/scan_raw` → `/scan`, env var parameter, `qos_profile_sensor_data`).
  - `tools/analysis/push_an.py`, `tools/analysis/turn_an.py` — existing window/yaw helpers; reuse `window()` and the unwrap logic rather than rewriting them. `tools/tests/test_push_an.py` shows the test style.
  - `delivery_bot_slam/test/test_launch_files.py` — launch tests; add to it in the same style.

## Decisions already made (do not revisit)
- **Four odometry configs**, as YAML variants of `ekf.yaml` in `delivery_bot_bringup/config/ekf_variants/`, passed to `slam_replay.launch.py` by source path (`ekf_params_file:=<abs path>`), so no install step is needed:
  - `rf2o_imu.yaml` — identical to `ekf.yaml` (baseline; copy, don't symlink)
  - `rf2o_only.yaml` — `imu0` block removed
  - `imu_only.yaml` — `odom0` block removed; `imu0` vyaw only (position then never moves in the EKF; slam_toolbox scan matching does translation — that is the point of the config)
  - `none` — no EKF at all; see next bullet
- **"none" = no EKF**: add a launch argument `ekf` (default `'true'`) to `slam_replay.launch.py`. When `'false'`, do not start `ekf_filter_node`; start `tf2_ros static_transform_publisher` publishing identity `odom → base_footprint` with `use_sim_time: true` instead. slam_toolbox then does pure scan matching. Because robot_localization's behaviour with zero inputs is not something to rely on.
- **Degradation node** `tools/analysis/scan_degrade.py`: `/scan_raw` → `/scan`, parameters from env vars `BEAM_KEEP` (keep every k-th beam, default 1; set `angle_increment *= k`, recompute `angle_max`, slice `intensities` the same way), `SCAN_KEEP` (publish every n-th scan, default 1), `MAXR` (ranges above it → `inf`, default off). Put the per-message maths in a pure function `degrade(ranges, intensities, angle_min, angle_increment, beam_keep, maxr)` with no rclpy import at module top level that the test can import. Supersedes nothing: leave `scan_minrange.py` alone.
- **Levels** for E5: `BEAM_KEEP` 2, 3, 4; `SCAN_KEEP` 2, 3; `MAXR` 4, 3, 2 (m). One axis at a time, others at default. Plus level `none` (no degradation, no node).
- **Matrix to run** (≥ 3 replays per cell, because replays of one bag vary about 12 % run to run, measured 2026-11-03):
  - E2: 4 configs × 6 bags × no degradation × 3 replays = 72 runs.
  - E5: config `rf2o_imu` and config `none` × bags `2026-10-31_push_195343`, `2026-11-03_140352_push_acfalse`, `2026-10-31_turn_194945` × 8 degradation levels × 3 replays = 144 runs.
- slam_toolbox in `slam_mode:=mapping` (short bags, map built from scratch). `foxglove:=false`. Playback `--rate 1.0`. `ROS_DOMAIN_ID=42` for every replay so nothing live is touched.
- **Metrics per run**, over the bag's logged window: from `odom_*.tum` (before SLAM) and `slam_*.tum` (after SLAM): straight-line distance (m) and yaw change (deg); for the turn bag, unwrapped yaw over the window. Time base: TUM stamps minus the header stamp of the bag's first `/scan`. Also record the live `/odom_rf2o` result from the bag itself (`push_an.py <bag> t0 t1 --sim`) once per bag as the live reference column.
- **Ground truth**: tape distance per bag (1.000 / 1.00 / 1.20 / 1.000 / 1.000 m) and 360° for the turn. Ratio = measured / truth.
- **Results**: one CSV `results/matrix/2026-11-09_e2_e5_runs.csv` (one row per run: date, commit, bag, config, degradation, replay, odom_dist, odom_yaw, slam_dist, slam_yaw, truth, odom_ratio, slam_ratio, throttled), plus `results/matrix/2026-11-09_e2_e5_summary.csv` (mean and min–max per cell). Raw runner log as a new file `evidence/lidar/2026-11-XX_matrix_runs.txt` (date = day the batch finished; append-only directory, never overwrite).
- No `evo` (not installed on the Pi; do not install it). The window metrics above are enough for phase 1.
- Rejected: replaying `/tf` (double publisher, map jumps); editing `ekf.yaml` in place; adding AMCL (phase 2); installing packages with pip or apt.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 0: Isolated workspaces on the Mac and the Pi
- Do: On the Mac: `cd /Users/shermanwee/Documents/MA4890/delivery_bot && git fetch && git worktree add ../delivery_bot_matrix -b slam/replay-matrix origin/main`; work only in `../delivery_bot_matrix` from now on. On the Pi: `mkdir -p ~/matrix_ws/src && cd ~/matrix_ws/src && git clone https://github.com/samwee24/delivery_bot.git` (skip clone if it exists). Overlay = `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash; source ~/matrix_ws/install/setup.bash` (the last only after the first build).
- Verify: `git -C ../delivery_bot_matrix branch --show-current` → `slam/replay-matrix`; on the Pi `ls ~/matrix_ws/src/delivery_bot/AGENTS.md` exists and `git -C ~/ros2_ws/src/delivery_bot branch --show-current` is still `test/motors-nav-2026-11-09`.
- Done when: both workspaces exist and the Pi's main clone is untouched.

### Step 1: EKF variants and the `ekf` launch argument
- Do: create the three YAML files in `delivery_bot_bringup/config/ekf_variants/` as decided (keep all comments that still apply; add a one-line header comment saying which inputs it uses and that it is an E2 variant). In `slam_replay.launch.py` add `DeclareLaunchArgument('ekf', default_value='true')`, put `IfCondition` on the EKF node and `UnlessCondition` on a new `static_transform_publisher` node (`odom` → `base_footprint`, zeros, `use_sim_time` from the launch config); document `ekf` in the docstring's argument list. Add tests to `delivery_bot_slam/test/test_launch_files.py`: the `ekf` argument exists with default `'true'`; the static publisher is conditional on `ekf` being false. Add to `delivery_bot_slam/test/test_config_consistency.py` (or a new test file next to it, matching its style): each variant's `odom0`, if present, is `/odom_rf2o_cov`; `rf2o_only` has no `imu0`; `imu_only` has no `odom0`; `rf2o_imu` equals `ekf.yaml` as parsed YAML.
- Verify: commit, push the branch, then on the Pi: `cd ~/matrix_ws/src/delivery_bot && git fetch && git switch slam/replay-matrix && cd ~/matrix_ws && colcon build --symlink-install --packages-select delivery_bot_slam delivery_bot_bringup && colcon test --packages-select delivery_bot_slam delivery_bot_bringup && colcon test-result --verbose` → 0 failures.
- Done when: tests pass on the Pi.

### Step 2: Degradation node
- Do: write `tools/analysis/scan_degrade.py` as decided, modelled on `scan_minrange.py`. Write `tools/tests/test_scan_degrade.py`: `BEAM_KEEP=2` halves the beam count and doubles `angle_increment`, first angle unchanged; `MAXR=2` turns 2.5 into `inf` and leaves 1.5; defaults return the input unchanged; intensities stay aligned with ranges.
- Verify: on the Pi `cd ~/matrix_ws/src/delivery_bot && git pull && python3 -m pytest tools/tests -q` → all pass.
- Done when: tests pass.

### Step 3: Analysis script
- Do: write `tools/analysis/matrix_an.py`: `matrix_an.py <bag> <tum_dir> <t0> <t1>` prints one line `odom_dist odom_yaw slam_dist slam_yaw` (m, deg). Reads the first `/scan` header stamp from the bag (rosbag2_py, as `push_an.py` does), loads the newest `odom_*.tum` and `slam_*.tum` in `<tum_dir>`, converts quaternions to yaw, and uses `push_an.window()` for distance/yaw and `turn_an`'s unwrap for yaw over long windows (import them; don't copy). Keep TUM parsing and time shifting in pure functions; add `tools/tests/test_matrix_an.py` covering TUM parsing, yaw from quaternion, time shift, and an unwrapped 360° turn.
- Verify: Pi pytest as in Step 2 → all pass.
- Done when: tests pass.

### Step 4: Runner and a single smoke run
- Do: write `tools/analysis/matrix_run.sh <bag> <config> <degradation> <replay> <outroot>`, modelled on `rf2o_fmt.sh`: `ROS_DOMAIN_ID=42`; source the overlay; `config` is `rf2o_imu|rf2o_only|imu_only|none` (`none` → `ekf:=false`, else `ekf_params_file:=$HOME/matrix_ws/src/delivery_bot/delivery_bot_bringup/config/ekf_variants/<config>.yaml`); `degradation` is `none|beam2|beam3|beam4|scan2|scan3|range4|range3|range2` (anything but `none` starts `scan_degrade.py` with the env var and plays with `--remap /scan:=/scan_raw`); output dir `<outroot>/<bag>/<config>/<degradation>/r<replay>` as `tum_output_dir`; **skip the run if that dir already holds a `slam_*.tum`** (so the batch can resume); launch `slam_replay.launch.py slam_mode:=mapping foxglove:=false`, wait for `/slam_toolbox` to report `active` (poll `ros2 lifecycle get /slam_toolbox`, max 30 s), play `--clock --rate 1.0 --topics /scan /imu/data /tf_static`, then stop the launch with SIGINT (so the recorder writes TUM files) and `pkill` leftovers like `rf2o_fmt.sh` does; log `vcgencmd get_throttled` before and after. Write `tools/analysis/matrix_batch.sh` that loops over exactly the E2 and E5 lists from the decisions and appends each run's stdout/stderr summary line to one log file.
- Verify: before running anything, check the Pi is free: `ros2 node list` on the default domain shows nothing and `uptime` load < 1.5. If a live stack or motor test is running, **stop and report** (do not run on top of it). Then run one smoke cell: `bash tools/analysis/matrix_run.sh 2026-10-31_push_195343 rf2o_imu none 1 ~/matrix_out` and `python3 tools/analysis/matrix_an.py ~/bags/2026-10-31_push_195343 ~/matrix_out/2026-10-31_push_195343/rf2o_imu/none/r1 39 50` → prints four numbers; `odom_dist` should be in the same range as earlier replays of this bag (0.53–0.68 m); if it is near 0 or above 1.5 m, stop and report.
- Done when: one run produces both TUM files and plausible numbers. Commit and push (checkpoint).

### Step 5: Run the batch
- Do: on the Pi, run `matrix_batch.sh` detached (`setsid nohup ... &`), output root `~/matrix_out`, log `~/matrix_out/batch.log`. Expect several hours. Check progress occasionally with a cheap command (`ls ~/matrix_out/*/*/*/* -d | wc -l`, `tail -3 ~/matrix_out/batch.log`); do not poll in a tight loop. If the user or the teammate needs the Pi for live work, kill the batch (`pkill -f matrix_batch.sh` and the replay processes) and resume later — the skip rule makes it safe.
- Verify: when finished, 216 run directories each with `odom_*.tum` and `slam_*.tum`; list any that failed.
- Done when: all 216 runs exist (or the failures are listed with their log lines).

### Step 6: Results, evidence, logs
- Do: write `tools/analysis/matrix_collect.py` (pure aggregation logic tested in `tools/tests/test_matrix_collect.py`: mean, min, max per cell, ratio against truth) that walks `~/matrix_out`, calls the `matrix_an.py` functions with each bag's window, and writes the two CSVs. Run it on the Pi, copy both CSVs and `batch.log` to the Mac worktree: CSVs to `results/matrix/`, the log to a new `evidence/lidar/<date>_matrix_runs.txt`. Add one `docs/test_log.md` row per experiment (E2, E5) with the exact commands, commit, and the key summary numbers (for E2: slam_ratio mean and range per config, empty-room bags vs person-behind bags; for E5: the level at which slam_ratio first leaves 0.87–1.13 for each config, or "none within range"). Add a `notes/notes.md` block on top (newest first, under the `---`; never edit old blocks). Do **not** write conclusions or "Our take" text; report numbers only, provenance *measured (offline replay)*.
- Verify: `python3 -m pytest tools/tests -q` on the Pi passes; the CSV row count is 216 + header.
- Done when: files are in the worktree and committed.

### Step 7: Final check and PR
- Do: on the Pi run `colcon test --packages-select delivery_bot_slam delivery_bot_bringup && colcon test-result --verbose` and `python3 -m pytest tools/tests -q` in `~/matrix_ws`; review `git diff origin/main --stat`. Open a PR from `slam/replay-matrix` to `main` titled `slam: <today YYYY-MM-DD> replay matrix: odometry configs and lidar degradation on existing bags`, using the repo's PR template, with the Pi commands and key numbers.
- Verify: tests pass; diff touches only the files listed below.
- Done when: PR is open; report the URL.

## Out of scope
Do not change: `delivery_bot_bringup/config/ekf.yaml`, `nav2_params.yaml`, `slam_mapping.yaml`, `slam_localization.yaml`, any `delivery_bot_drivers` or `delivery_bot_mission` file, `tools/robot_control.py`, existing `tools/analysis/*` scripts, CI config, old `notes/notes.md` blocks, existing `evidence/` files, `docs/report_plan.md`, `report/*`. Never touch the Pi's `~/ros2_ws/src/delivery_bot` clone or its branch. Never start the motor node or pass `dry_run:=false`.
Do not add: AMCL or any localisation-mode replay (phase 2), `evo`, new pip/apt packages, conclusions or report prose.

Files you should end up touching: `delivery_bot_bringup/config/ekf_variants/{rf2o_imu,rf2o_only,imu_only}.yaml`, `delivery_bot_slam/launch/slam_replay.launch.py`, `delivery_bot_slam/test/test_launch_files.py`, `delivery_bot_slam/test/test_config_consistency.py` (or one new test file beside it), `tools/analysis/{scan_degrade.py,matrix_an.py,matrix_run.sh,matrix_batch.sh,matrix_collect.py}`, `tools/tests/{test_scan_degrade.py,test_matrix_an.py,test_matrix_collect.py}`, `results/matrix/*.csv`, one new `evidence/lidar/*_matrix_runs.txt`, `docs/test_log.md`, `notes/notes.md`.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, the code is structured differently, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a missing type annotation, a typo in the instructions) you may handle; list each one under Deviations in the report.
- A bag whose window you cannot find in `docs/test_log.md` is a stop-and-report, not a guess.
- Commit after each step with message `step N: <title>` on `slam/replay-matrix`, push so the Pi can pull. The Pi never commits.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: Replay matrix phase 1

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 0: Isolated workspaces — <one line>
- [x] Step 1: EKF variants and ekf argument — <...>
- [ ] Step N: <title> — <why not done>

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Key numbers
<E2: slam_ratio and odom_ratio mean (min–max) per config, empty-room vs person-behind bags; E5: per config, first level outside 0.87–1.13; live rf2o reference per bag>

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what you found that contradicts the plan, what the planner needs to decide; "None" if none>
```

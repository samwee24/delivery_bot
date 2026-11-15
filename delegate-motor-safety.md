# Task: Motor safety fixes on feat/motors (dry run back, lidar stop, stamped cmd_vel)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Make the teammate's new motor node safe enough to drive in Tuesday's experiments, without changing how it drives. When done: `motor_node` has a dry run again (default on, no GPIO), stops linear motion itself when the lidar sees something within `stop_dist_m` in the direction of travel (and stops everything if the scan goes stale), Nav2 publishes `TwistStamped` so it can talk to the motor node, the duty maths has tests, docs match the code, and a PR into the teammate's branch `feat/motors` is open for her to review. The motor side belongs to the teammate (Chloe): this is a one-off fix the project owner approved, delivered as a PR she approves, not a rewrite.

## Context
- Project: CA3 room delivery robot. Raspberry Pi 4B, Ubuntu 24.04, **ROS 2 Jazzy**, RPLIDAR A1M8 on `/scan`, L298N motor driver on GPIO via gpiozero + `LGPIOFactory`, Nav2 1.3.x (RPP → velocity_smoother → `cmd_vel_smoothed` → collision_monitor → `/cmd_vel`). **Read `AGENTS.md` on `main` first** (`git show origin/main:AGENTS.md`); rule 1: "Safety is structural. Motors are driven only through the safety node/watchdog (`stop_dist_m`, `watchdog_s`, SIGINT zeroes PWM)". Other rules: config not constants, every number with its command, `notes/notes.md` and `evidence/` append-only, PR title `type: YYYY-MM-DD what`, definition of done = pytest for logic.
- Mac repo: `/Users/shermanwee/Documents/MA4890/delivery_bot`. **Another session works in that checkout and switches its branches: do not work there.** Make your own worktree (Step 0). The Mac has **no ROS**: edit on the Mac, build/test on the Pi.
- Pi: `ssh robot@100.83.14.99` (key auth). SSH is non-interactive: start every remote command with `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash;` and, after Step 0, `source ~/motorfix_ws/install/setup.bash`.
- **The Pi's main clone `~/ros2_ws/src/delivery_bot/` is on `test/motors-nav-2026-11-09` (a merge of `feat/motors`, `nav/nav2-glue`, `slam/explore`). Do not switch, pull, edit, build or launch from it.** Use the overlay `~/motorfix_ws` (Step 0).
- What `feat/motors` (commits 3d295f7, 3fed2ff, by the teammate) changed against `main` — read the diff with `git diff origin/main...origin/feat/motors`:
  - `delivery_bot_drivers/delivery_bot_drivers/motor_node.py` — implemented: `/cmd_vel` (`TwistStamped`) → 20 Hz `_control_step` → `v_left/right = v ∓ w·wheel_base/2` → `_duty_for()` (duty = `min_duty + gain·|speed|`, 0 below `min_wheel_speed`, clamped to `max_duty`) → `set_wheel()` (direction pins then PWM); watchdog `watchdog_s` 0.5 s → `stop()`; `main()` calls `stop_all()` in `finally`. gpiozero imported inside `__init__`. **No dry run**: always opens GPIO; `dry_run` parameter ignored (not declared). `_on_imu` raises `NotImplementedError` and is not subscribed.
  - `delivery_bot_drivers/config/drivers.yaml` — right pins 26/16, `min_duty: 0.11`, `gain_left: 3.00`, `gain_right: 1.00`, `dry_run: false`, `use_stamped: true` (unused).
  - `delivery_bot_bringup/launch/base.launch.py` — starts `motor_node`; `dry_run` default changed `'true'` → `'false'`; adds an unused `motor` argument; reformats many lines.
  - `delivery_bot_slam/test/test_launch_files.py` — `test_base_declares_dry_run_true_by_default` edited to assert `'false'` (the test's name and comment still say true).
  - `AGENTS.md`, `README.md`, `docs/system/{01,02,03,04,05,07}*.md`, `docs/wiring.md` — reworded to "motors always live, no dry run"; `05_config_reference.md` says `min_duty 0.15` while the YAML says 0.11.
- Safety values (from `docs/system/05_config_reference.md`, *brief default*): `stop_dist_m: 0.20`, `stop_half_angle_deg: 35`, `watchdog_s: 0.5`, `v_max: 0.15`.
- `delivery_bot_bringup/config/nav2_params.yaml` — Nav2 params. **Already fixed in PR 32** (`fix/nav2-stamped-cmd-vel`, into `main`): `enable_stamped_cmd_vel: true` on controller_server, behavior_server, velocity_smoother, collision_monitor, docking_server, with a config test; checked on the Pi 2026-11-09 that every `/cmd_vel*` publisher and subscriber is `TwistStamped`. `feat/motors` does not have it until it is rebased on `main` after PR 32 merges.
- `delivery_bot_description/urdf/delivery_bot.urdf.xacro` — the `base_link → laser` joint; its yaw tells which scan angle points forward.
- Tests: `delivery_bot_drivers/test/` (has `test_imu_node.py` for style), `delivery_bot_slam/test/test_launch_files.py` (`declared()` helper), `delivery_bot_slam/test/test_config_consistency.py` (`share()`, `params()`, `MAX_SPEED`).
- `.github/pull_request_template.md` — the checklist the PR must fill.

## Decisions already made (do not revisit)
- **Branch off `feat/motors`, PR back into `feat/motors`** (base = `feat/motors`, not `main`), so the teammate reviews and merges into her own branch. Keep her driving logic and her measured values (`min_duty 0.11`, gains 3.0/1.0, pins 26/16) exactly as they are.
- **Dry run lives in the node.** `motor_node` declares `dry_run` (default `True`). In dry run it never imports gpiozero or opens pins; `set_wheel()`/`stop()` only record the last commanded duty and direction per wheel and log them at most once per second (`throttle_duration_sec=1.0`). `base.launch.py` default goes back to `dry_run:='true'`; the edited test goes back to asserting `'true'`; `drivers.yaml` `dry_run: true` with the comment "the launch file decides; live needs dry_run:=false on the command line". Remove the unused `motor` launch argument. Do not write `dry_run:=false` into any file outside markdown (CI rejects it).
- **Pure functions for the maths**, module level, no GPIO, so tests can import them: `wheel_speeds(v, w, wheel_base) -> (v_left, v_right)`, `duty_for(speed, gain, min_duty, max_duty, min_wheel_speed) -> (duty, direction)`, `blocked(ranges, angle_min, angle_increment, range_min, v, stop_dist, half_angle, forward_angle) -> bool`. The class calls them; behaviour stays identical to the teammate's code for the first two.
- **Lidar stop inside `motor_node`**, so it covers every `/cmd_vel` source (Nav2, teleop, scripts), not just Nav2: subscribe `/scan` (`qos_profile_sensor_data`), keep the latest scan and its arrival time. In `_control_step`, after the watchdog: if the last scan is older than `scan_timeout_s` (0.5) → `stop()` and warn (throttled 1 s) — fail safe. Otherwise, if `v > 0` and `blocked(...)` for the forward sector, or `v < 0` and blocked for the rear sector (forward_angle + π), set `v = 0` for this step and keep `w` (the robot may still turn away). `blocked` counts only finite ranges ≥ `range_min`; no-echo (`inf`) counts as free — a known limit of this lidar (26–29 % no-echo, dark or glass surfaces), to be listed as a residual hazard, not fixed here. New parameters in `drivers.yaml`: `stop_dist_m: 0.20`, `stop_half_angle_deg: 35.0`, `scan_timeout_s: 0.5`, `laser_forward_rad` (the scan angle that points along base +x, derived from the URDF joint yaw; write the derivation in the comment, provenance *measured, URDF*).
- **`/cmd_vel` type is settled by PR 32** (Nav2 publishes `TwistStamped`). Do not edit `nav2_params.yaml` in this task. The motor node stays `TwistStamped`-only; teleop keeps `-p stamped:=true`. Remove the unused `use_stamped` line from `drivers.yaml` and fix its wrong comment ("Nav2 Jazzy publishes TwistStamped" is only true with the PR 32 flag).
- Out of this job: the gyro loop (`_on_imu`, `use_gyro_loop`, `kp_omega`, `ki_omega`), gain calibration, a `/cmd_vel` arbiter between teleop and Nav2.
- Rejected: a separate safety node between Nav2 and the motors (more topics, more to break before Tuesday); relying on Nav2's collision monitor alone (teleop and scripts bypass it); changing the gains or `min_duty`.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 0: Isolated workspaces
- Do: Mac: `cd /Users/shermanwee/Documents/MA4890/delivery_bot && git fetch && git worktree add ../delivery_bot_motorfix -b fix/motor-safety origin/feat/motors`; work only in `../delivery_bot_motorfix`. Pi: `mkdir -p ~/motorfix_ws/src && cd ~/motorfix_ws/src && git clone https://github.com/samwee24/delivery_bot.git`.
- Verify: `git -C ../delivery_bot_motorfix log --oneline -1` → `3fed2ff adjusted gains roughly`; Pi `git -C ~/ros2_ws/src/delivery_bot branch --show-current` still `test/motors-nav-2026-11-09`.
- Done when: both exist, the Pi's main clone untouched.

### Step 1: Pure functions and their tests
- Do: in `motor_node.py` add `wheel_speeds`, `duty_for` and `blocked` at module level as decided, and make `_control_step`/`_duty_for` use the first two (no behaviour change). Write `delivery_bot_drivers/test/test_motor_node.py`: straight (`w=0`) gives equal wheel speeds; spin (`v=0`) gives opposite; `duty_for` returns 0 duty below `min_wheel_speed`, `min_duty + gain·speed` in range, `max_duty` at the cap, direction −1 for negative speed; `blocked` is true for an obstacle at 0.15 m dead ahead with `v>0`, false for the same obstacle behind with `v>0`, true behind with `v<0`, false at 0.25 m, false when the only close range is `inf` or below `range_min`, and respects `forward_angle` (an obstacle at the rotated forward angle blocks).
- Verify: commit, push; Pi: `cd ~/motorfix_ws/src/delivery_bot && git fetch && git switch fix/motor-safety && cd ~/motorfix_ws && colcon build --symlink-install --packages-select delivery_bot_drivers delivery_bot_bringup delivery_bot_slam delivery_bot_description && colcon test --packages-select delivery_bot_drivers && colcon test-result --verbose` → 0 failures (flake8 and pep257 included).
- Done when: tests pass.

### Step 2: Dry run back
- Do: as decided in `motor_node.py` (declare `dry_run`; no gpiozero import or pin opening in dry run; `stop_all()` safe in both modes), `drivers.yaml`, `base.launch.py` (default `'true'`, drop `motor` arg; keep the teammate's other lines), `test_launch_files.py` (assert `'true'` again). Add to `test_motor_node.py`: constructing the node with `dry_run=True` on a machine without gpiozero works and `set_wheel` records the duty (use `rclpy.init()`/`shutdown()` in a fixture, as `test_imu_node.py` does if it constructs nodes; if constructing a node in tests is not the repo's pattern, test only that `dry_run` is declared with default True by parsing the module, and say so under Deviations).
- Verify: Pi build and `colcon test --packages-select delivery_bot_drivers delivery_bot_slam && colcon test-result --verbose` → 0 failures.
- Done when: tests pass.

### Step 3: Lidar stop
- Do: read the URDF laser joint, work out `laser_forward_rad`, add the four parameters to `drivers.yaml` with provenance comments, add the `/scan` subscription, stale-scan stop and sector check to `_control_step` as decided. Update the module docstring's safety contract (dry run, watchdog, lidar stop, stale scan, shutdown).
- Verify: Pi build and drivers tests → 0 failures.
- Done when: tests pass. Commit and push (checkpoint).

### Step 4: Bring in the stamped Nav2 config
- Do: if PR 32 is merged (`gh pr view 32 --json state` → `MERGED`), `git merge origin/main` into `fix/motor-safety` and resolve conflicts keeping both sides (the teammate's motor lines in `base.launch.py` and `drivers.yaml`, your Step 2–3 changes, `main`'s `nav2_params.yaml`). If PR 32 is not merged, stop and ask the user to merge it first. Remove the `use_stamped` line from `drivers.yaml`.
- Verify: `grep -c "enable_stamped_cmd_vel: true" delivery_bot_bringup/config/nav2_params.yaml` → 5; Pi build and `colcon test --packages-select delivery_bot_drivers delivery_bot_slam && colcon test-result --verbose` → 0 failures.
- Done when: the branch has the stamped Nav2 config and all tests pass.

### Step 5: Dry-run smoke on the Pi (nothing moves)
- Do: check the Pi is free first (`ros2 node list` on the default domain empty, `pgrep -f rplidar` empty); **if a stack is running, stop and report.** Ask the user to confirm the **motor switch is OFF** and the robot is on the floor in the open, then wait for their yes. Then, `export ROS_DOMAIN_ID=42`, only the `~/motorfix_ws` overlay on top of `~/ros2_ws`:
  1. `ros2 launch delivery_bot_bringup navigation.launch.py nav:=true bridge:=false` (default `dry_run`). `ros2 param get /motor_node dry_run` → True; motor_node log says dry run.
  2. `ros2 topic info /cmd_vel -v` and `ros2 topic info /cmd_vel_smoothed -v` → every publisher and subscriber is `geometry_msgs/msg/TwistStamped`. For each Nav2 node, `ros2 param get <node> enable_stamped_cmd_vel` → True (this also confirms which nodes have it; adjust Step 4 if one is missing and re-run its tests).
  3. In a second shell: `ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.10}}}"` → motor_node logs non-zero duties both wheels, direction +1. Ask the user to hold a hand or a box about 0.15 m in front of the robot → log shows linear zeroed (duty 0); away → duties return. Then the same with `x: -0.10` and the box behind.
  4. Stop the pub → within 0.5 s log shows the watchdog stop.
  5. With the pub running, stop the lidar driver (`pkill -f rplidar`) → log shows the stale-scan stop within about 0.5 s.
- Verify: each item as stated; record the exact commands and the log lines.
- Done when: all five pass, or the failing one is reported with its exact text. **Do not run anything live (`dry_run:=false`) in this task**; the first live run with wheels raised is the teammate's, after review.

### Step 6: Docs and records
- Do: change back the wording `feat/motors` made in `AGENTS.md`, `README.md` and `docs/system/*.md` from "always live, no dry run" to: dry run by default, live needs `dry_run:=false` on the command line, motor_node has a lidar stop (`stop_dist_m` 0.20 m, ±35°) and a stale-scan stop besides the watchdog; keep her other doc changes (pins, gains). Fix `min_duty` in `05_config_reference.md` to 0.11 (the YAML value). Add the no-echo limit to `docs/system/06_troubleshooting.md` or the hazard notes as a residual hazard. Add one `docs/test_log.md` row per Step 5 check and a `notes/notes.md` block on top (newest first, under `---`; never edit old blocks).
- Verify: `git diff origin/feat/motors --stat` lists only the files named in this prompt; `grep -rn "dry_run:=false" --include=*.py --include=*.yaml .` finds nothing.
- Done when: committed and pushed.

### Step 7: PR into feat/motors
- Do: `gh pr create --base feat/motors --head fix/motor-safety --title "fix: <today YYYY-MM-DD> motor safety: dry run back, lidar stop, stamped cmd_vel"`, body from the PR template: what changed and why (one line each: dry run removed made every stack drive the wheels; no lidar stop meant teleop and scripts had no obstacle stop; Nav2 Twist vs motor TwistStamped meant no motion under Nav2), the Step 5 commands and results, that her driving logic and measured values are unchanged, and that a wheels-raised live test is for her after review. Do not @-mention anyone.
- Verify: `gh pr view --json url,baseRefName` → base `feat/motors`.
- Done when: the PR is open; report its URL.

## Out of scope
Do not change: the duty formula, `min_duty`, gains, pins, `pwm_hz`, `max_duty`, `watchdog_s`, `wheel_base`; the gyro loop; `delivery_bot_mission/`; `tools/`; `ekf.yaml`, `slam_*.yaml`; collision monitor zone values; CI config; old `notes/notes.md` blocks; existing `evidence/` files; the Pi's `~/ros2_ws/src/delivery_bot` clone. Never run the motors live, never write `dry_run:=false` in a non-markdown file, never merge the PR yourself.
Do not add: a separate safety node, a `/cmd_vel` arbiter, new pip/apt packages, Foxglove changes.

Files you should end up touching: `delivery_bot_drivers/delivery_bot_drivers/motor_node.py`, `delivery_bot_drivers/config/drivers.yaml`, `delivery_bot_drivers/test/test_motor_node.py` (new), `delivery_bot_bringup/launch/base.launch.py`, `delivery_bot_slam/test/test_launch_files.py`, `AGENTS.md`, `README.md`, `docs/system/*.md`, `docs/test_log.md`, `notes/notes.md`.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, the code is structured differently, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a missing type annotation, a typo in the instructions) you may handle; list each one under Deviations in the report.
- Commit after each step with message `step N: <title>` on `fix/motor-safety`, and push so the Pi can pull. The Pi never commits.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: Motor safety fixes

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 0: Isolated workspaces — <one line>
- [x] Step 1: Pure functions and tests — <...>
- [ ] Step N: <title> — <why not done>

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Smoke results
<dry_run value; message type per publisher/subscriber on /cmd_vel and /cmd_vel_smoothed; which Nav2 nodes have enable_stamped_cmd_vel; lidar stop front and rear (distance used, log line); watchdog and stale-scan stop times; laser_forward_rad and how it was derived>

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what you found that contradicts the plan, what the planner needs to decide; "None" if none>
```

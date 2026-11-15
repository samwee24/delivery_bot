# Task: driven-session prep (Nav2 bond timeout, run_cell live args, motor check tool, bag summary, run order)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Today (Tue 2026-11-10) the team drives the robot for the CA3 experiments. Four things block or slow that session and none needs the robot to fix:
1. Nav2 shuts itself down under load.
2. `tools/run_cell.py` can't start the motors live.
3. The pre-run power check lives in `/tmp` and is lost on every reboot.
4. There is no quick per-bag summary.
When done, all four are fixed in one PR with CI green, plus a one-page run order for the session.

## Context
- Project: ROS 2 Jazzy delivery robot on a Raspberry Pi 4B (L298N motors, RPLidar A1M8, MPU6050). Read `AGENTS.md` first (short); it is the project rulebook.
- Working directory: `/Users/shermanwee/Documents/MA4890/delivery_bot` (the Mac). Branch `prep/driven-session` is already created from `main` at `b896de2` and checked out. **The Mac has no ROS**, and the Pi is powered off, so you cannot run launch files or anything that imports `rclpy`/`rosbag2_py`/`gpiozero`. CI (`build-and-test`) runs the ROS package tests; you run only plain pytest locally.
- How to test locally: `python3 -m pytest tools/tests -q` (must pass). Package tests (`delivery_bot_slam/test/test_launch_files.py` etc.) run only in CI.
- Key files:
  - `delivery_bot_bringup/launch/navigation.launch.py`: includes `nav2_bringup/launch/navigation_launch.py` twice (slam branch inside an `OnStateTransition`, amcl branch inside a `TimerAction`).
  - `delivery_bot_slam/launch/explore.launch.py`: includes the same Nav2 launch.
  - `delivery_bot_bringup/config/nav2_params.yaml`: Nav2 parameters (top-level keys are node names, e.g. `velocity_smoother:` at line ~266, `collision_monitor:` ~283).
  - `delivery_bot_slam/test/test_launch_files.py`: launch tests; existing tests read launch source text with regexes (see `test_navigation_nav2_uses_our_params_without_composition`). Copy that style.
  - `tools/run_cell.py` + `tools/tests/test_run_cell.py`: experiment runner and its tests (`BASE` list at line 12 of the test).
  - `tools/timed_move.py`: open-loop straight/spin publisher (reference for CLI style and the speed caps).
  - `docs/system/05_config_reference.md`, `docs/system/06_troubleshooting.md`: config reference and troubleshooting tables (edit in place).
- Conventions: match the style of the file you edit. Tools have a module docstring with a `Usage:` line, pure functions with tests in `tools/tests/test_<name>.py`, and imports of ROS/GPIO libraries *inside* `main()` so the module imports without them (see `timed_move.py`).

## Decisions already made (do not revisit)
- **`bond_timeout` = 10.0 s** for Nav2's lifecycle manager (Jazzy default 4.0). On 2026-11-09, at load 20-30 on 4 cores, it logged `CRITICAL FAILURE: SERVER smoother_server IS DOWN after not receiving a heartbeat for 4000 ms` (also route_server, planner_server) and shut Nav2 down 2-3 s into every timed run.
- **How it is applied:** Jazzy's `nav2_bringup/launch/navigation_launch.py` starts `lifecycle_manager_navigation` with only `autostart` and `node_names`. It does **not** pass our `params_file`, so a YAML entry alone is silently ignored. The value therefore lives in YAML (AGENTS rule 3: config, never constants) and the launch file reads it and applies it with `launch_ros.actions.SetParameter`. SetParameter sets a global parameter for every node started after it in the launch, including nodes in included launch files. Nodes that don't declare `bond_timeout` ignore it.
  - Rejected: vendoring a copy of `navigation_launch.py` (250 lines to maintain).
  - Rejected: `bond_timeout: 0.0`, which disables the bond, so a really dead server would go unnoticed.
- **Value type must be float.** Pass a Python `float` to SetParameter, not a `LaunchConfiguration` string. The lifecycle manager declares a double, and a string override crashes it.
- **`run_cell.py` gets pass-through launch args after `--`.** For example `python3 tools/run_cell.py E2 rf2o_imu_empty 1 -- dry_run:=false`. Today it launches `navigation.launch.py` without `dry_run:=false`, so `motor_node` runs dry and nothing moves.
  - CI job `repo-rules` rejects any committed non-markdown line matching `dry_run(:=|=| *: *)(false|0)`, and AGENTS says live motors are a deliberate act typed on the command line. So the operator types it; the code never contains it.
  - Do not build that string in code by concatenation to dodge the CI check: that defeats a safety rule.
- **`run_cell.py` adds `bridge:=false` by default** (Foxglove off) to cut CPU load during runs. Add a `--bridge` flag that leaves it out. `bridge` is an existing launch argument of `navigation.launch.py`.
- **`tools/motor_check.py` is a deliberate bench tool that writes GPIO directly.** It is the only exception to AGENTS rule 1 ("motors only through motor_node"). It is allowed because:
  - It refuses to run while any `motor_node` process exists.
  - It caps duty at 0.35 and run length at 3.0 s.
  - It zeroes PWM in a `finally`.
  It replaces `/tmp/duty_run.py`, which on 2026-11-09 told a dead motor battery apart from a software fault.
  Settings: PWM 100 Hz; pins BCM ENA 12, IN1 5, IN2 6, ENB 13, IN3 26, IN4 16 (same as `delivery_bot_drivers/config/drivers.yaml`); gpiozero `PWMOutputDevice`/`DigitalOutputDevice` with `gpiozero.pins.lgpio.LGPIOFactory`; forward = IN1 and IN3 on, IN2 and IN4 off.
- **Expected results to print in `motor_check.py` help:**
  - `run 0.30 2` should travel about 0.9 m (measured 0.87-0.90 m on 2026-11-09).
  - The staircase is kick 0.30 for 0.15 s, then duty 0.20, 0.16, 0.14, 0.12, 0.10 for 1.5 s each. Measured rolling speeds were 0.293, 0.213, 0.156, 0.094 and 0.004 m/s; 0.10 stalls.
- **`tools/analysis/bag_summary.py` reads bags with `rosbag2_py`** (imported inside the reader function, like the existing tools).
  - The maths is a pure function with a local test.
  - It reports forward distance and heading change from `/odom_rf2o` and `/odometry/filtered`, plus the commanded distance and angle integrated from `/cmd_vel`.
  - It does **not** report rf2o sideways drift as a result: on 2026-11-09 rf2o said 16 cm right where the tape said 3 cm left. Print it labelled "(unreliable, use tape)".

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 1: `bond_timeout` in YAML
- Do: in `delivery_bot_bringup/config/nav2_params.yaml`, add this top-level block (placement: just above `velocity_smoother:`), matching the file's 2-space indent:
  ```yaml
  lifecycle_manager_navigation:
    ros__parameters:
      # 2026-11-09: default 4.0 s tripped at load 20-30 ("SERVER smoother_server IS DOWN
      # after not receiving a heartbeat for 4000 ms"), Nav2 went down mid-run. Brief value,
      # not yet measured. nav2_bringup does not pass this file to its lifecycle manager, so
      # navigation.launch.py and explore.launch.py read it and apply it with SetParameter.
      bond_timeout: 10.0
  ```
- Verify: `python3 -c "import yaml; print(yaml.safe_load(open('delivery_bot_bringup/config/nav2_params.yaml'))['lifecycle_manager_navigation']['ros__parameters']['bond_timeout'])"` → `10.0`
- Done when: the value loads as a float from the YAML.

### Step 2: apply it in both launch files
- Do: in `delivery_bot_bringup/launch/navigation.launch.py` and `delivery_bot_slam/launch/explore.launch.py`:
  - Add `import yaml` and `from launch_ros.actions import SetParameter` (extend the existing `launch_ros.actions` import).
  - Inside `generate_launch_description()`, read `nav2_params.yaml` from the `delivery_bot_bringup` share directory. Both files already build that path for `params_file`; reuse it.
  - Make `SetParameter(name='bond_timeout', value=float(<loaded value>))` the **first** entity in the returned `LaunchDescription` list, so it is in effect before any Nav2 include runs.
  - Do not change anything else in either file.
- Verify: `python3 -m py_compile delivery_bot_bringup/launch/navigation.launch.py delivery_bot_slam/launch/explore.launch.py` → no output. Then `grep -n "SetParameter\|bond_timeout" delivery_bot_bringup/launch/navigation.launch.py delivery_bot_slam/launch/explore.launch.py` shows the import and the call in both.
- Done when: both files compile and set `bond_timeout` from the YAML as their first launch entity.

### Step 3: launch tests for Step 2
- Do: in `delivery_bot_slam/test/test_launch_files.py`, add two tests in the existing source-reading style:
  - (a) For both `navigation.launch.py` and `explore.launch.py`: the source contains `SetParameter(name='bond_timeout'` and reads `nav2_params.yaml`.
  - (b) The YAML value `lifecycle_manager_navigation.ros__parameters.bond_timeout` is a float greater than 4.0.
  Use the existing path constants (`NAV`, `EXPLORE`, `LAUNCH_DIRS`) where they fit; read the YAML via a path relative to the test file, like the other tests locate files.
- Verify: `python3 -m py_compile delivery_bot_slam/test/test_launch_files.py`. The tests themselves run in CI (they import `launch`); note that in the report.
- Done when: the two tests exist and compile.
- Then commit: `nav: 2026-11-10 Nav2 bond_timeout 10 s from nav2_params.yaml via SetParameter`.

### Step 4: `run_cell.py` live args and `bridge:=false`
- Do: in `tools/run_cell.py`:
  1. `cell_plan()` appends `'bridge:=false'` to the launch command unless a new parameter `bridge: bool = False` is true.
  2. `main()` accepts extra launch arguments after `--`. Use `argparse.REMAINDER`, or split `sys.argv` at `--` before parsing; pick whichever stays simplest. Append them unchanged to the end of the launch command.
  3. Each extra must match `^[A-Za-z_][A-Za-z0-9_]*:=\S+$`, else exit with an error (no shell injection, no stray words).
  4. Add the `--bridge` flag.
  5. The test_log row it prints must include the extras, so the run records whether motors were live.
  6. Update the module docstring: the Usage line (show `-- dry_run:=false` as the way to drive live, in the docstring text only), and replace "Never starts a motor node, never sets dry_run" with a true statement: the default launch has `motor_node` in dry run, and live motors need `-- dry_run:=false` typed by the operator.
- Do: in `tools/tests/test_run_cell.py`:
  - Update `BASE`/expectations for the default `bridge:=false`.
  - Add tests: `bridge=True` omits it; extras are appended in order; a malformed extra (`"foo"`, `"a:=b; rm"`) is rejected; the default plan still contains no `dry_run`.
  - If the extras parsing lives in `main()`, factor the validation into a small pure function (e.g. `check_extras(list[str]) -> list[str]`) so it can be tested.
  - The test file must not contain the literal `dry_run:=false` (CI rule). For a "live" example in a test, use another argument such as `localizer:=amcl`.
- Verify: `python3 -m pytest tools/tests/test_run_cell.py -q` → all pass. `grep -rn "dry_run:=false" tools/ --include=*.py` must show only docstring lines in `run_cell.py`.
- **Stop** if a docstring line still trips CI. CI excludes only `*.md` files, so a `.py` docstring containing `dry_run:=false` **will** fail `repo-rules`. In that case, word the docstring as `-- dry_run:=<false>` or `dry_run set to false`, so the regex `dry_run(:=|=| *: *)(false|0)` does not match. Check with: `git diff main -- tools | grep -E '^\+' | grep -Ei 'dry_run(:=|=| *: *)(false|0)'` → no output.
- Done when: tests pass and that grep prints nothing.

### Step 5: `tools/motor_check.py`
- Do: create it with:
  - Usage `python3 tools/motor_check.py run DUTY SECONDS` or `python3 tools/motor_check.py stair`.
  - Pure functions:
    - `check_run(duty: float, seconds: float) -> None` raises `ValueError` unless `0 < duty <= 0.35` and `0 < seconds <= 3.0`.
    - `stair_schedule() -> list[tuple[float, float]]` returns `[(0.30, 0.15), (0.20, 1.5), (0.16, 1.5), (0.14, 1.5), (0.12, 1.5), (0.10, 1.5)]`.
    - `motor_node_running() -> bool` returns whether `pgrep -f motor_node` finds a process (subprocess; returns False if pgrep is missing).
  - `main()`:
    1. Refuse with a clear message and exit code 1 if `motor_node_running()`.
    2. Otherwise import gpiozero inside `main`, drive both wheels forward at 100 Hz with the decided pins, and rewrite the duty every 50 ms for the run length (as `motor_node` does).
    3. Print a wall-clock timestamp at each duty change, so a bag of `/odom_rf2o` can be lined up.
    4. In `finally`, set both PWM to 0, all pins off, and close all devices.
  - Docstring: say it is the deliberate exception to AGENTS rule 1 and why (power check that bypasses `motor_node`, refuses while it runs, caps 0.35 / 3 s), the expected results from the Decisions section, and that a silent run means motor power, not code (OI-9 in `docs/CA3.md`).
  - Create `tools/tests/test_motor_check.py` testing `check_run` bounds (0.35 ok, 0.36 rejected, 3.0 ok, 3.1 rejected, 0 rejected) and that `stair_schedule()` starts with the kick and ends at 0.10.
- Verify: `python3 -m pytest tools/tests/test_motor_check.py -q` → pass; `python3 tools/motor_check.py --help` works on the Mac (no gpiozero import at module level).
- Done when: tests pass and `--help` prints usage.
- Then commit: `tools: 2026-11-10 motor_check.py power check (replaces /tmp/duty_run.py) and run_cell live args`.

### Step 6: `tools/analysis/bag_summary.py`
- Do: create it with:
  - Usage `python3 tools/analysis/bag_summary.py BAG [BAG ...]`.
  - A pure function `summarise(cmd, odom)`:
    - `cmd` is a list of `(t, v, w)` from `/cmd_vel` (`twist.linear.x`, `twist.angular.z`; the topic is `geometry_msgs/msg/TwistStamped`).
    - `odom` is a dict `topic -> list of (t, x, y, yaw)`.
    - It returns a dict with:
      - `cmd_s`: time from first to last non-zero command.
      - `cmd_dist` and `cmd_angle`: each non-zero command's v and w times the time to the next message, with that gap capped at 0.5 s (the motor watchdog).
      - per odom topic: `along` (displacement projected on the start heading), `side` and `dheading_deg` (yaw change, wrapped to ±180).
  - A reader `read_bag(path)` that imports `rosbag2_py`, `rclpy.serialization` and `rosidl_runtime_py.utilities` **inside the function**. It reads `/cmd_vel`, `/odom_rf2o` and `/odometry/filtered` (whichever exist; quaternion → yaw), using receive timestamps.
  - `main()` prints one markdown table row per bag: bag name, cmd_s, cmd_dist, cmd_angle, then along and dheading per topic, then `side` labelled `(unreliable, use tape)`.
  - Create `tools/tests/test_bag_summary.py` with synthetic data:
    - a 1 m straight at 0.15 m/s gives `along` ≈ 1.0 and `cmd_dist` ≈ 1.0 (20 Hz commands);
    - a 360° spin gives `dheading_deg` near 0 after wrapping, and `cmd_angle` ≈ 2π;
    - a 2 s gap in commands counts only 0.5 s.
- Verify: `python3 -m pytest tools/tests/test_bag_summary.py -q` → pass; `python3 tools/analysis/bag_summary.py --help` works on the Mac.
- Done when: tests pass.

### Step 7: docs
- Do:
  - (a) `docs/system/05_config_reference.md`: in the planning and control section (find where `nav2_params.yaml` values are listed), add a row for `lifecycle_manager_navigation.bond_timeout` = 10.0 s, provenance "brief value 2026-11-10, Jazzy default 4.0 tripped at load 20-30", applied by SetParameter in `navigation.launch.py` and `explore.launch.py`.
  - (b) `docs/system/06_troubleshooting.md`, two new rows in the matching tables:
    - Symptom `CRITICAL FAILURE: SERVER <name> IS DOWN after not receiving a heartbeat for 4000 ms` (Nav2 deactivates, the collision monitor stops passing `/cmd_vel`, motion stops 2-3 s into a run). Cause: CPU load 20-30 delays heartbeats. Fix: `bond_timeout` 10 s (this PR), `bridge:=false`, camera off. Check with `ros2 param get /lifecycle_manager_navigation bond_timeout`.
    - In the Motors table: "Before a block of driven runs: `python3 tools/motor_check.py run 0.30 2` (about 0.9 m); silent = motor power (OI-9)".
  - (c) Create `docs/run_order.md`: the driven-session order, one page, using the content in the appendix below verbatim apart from formatting.
- Verify: `git diff --stat` lists only files named in Steps 1-7.
- Done when: the three docs are written.
- Then commit: `docs: 2026-11-10 run order, bond_timeout and motor_check in config and troubleshooting`.

### Step 8: final check, push, PR
- Do:
  - Run the full local suite and check the CI safety grep.
  - Push the branch and open a PR to `main` with `gh pr create`:
    - Title `nav: 2026-11-10 driven-session prep: Nav2 bond_timeout, run_cell live args, motor_check, bag_summary`.
    - Body follows `.github/pull_request_template.md`. Under "How it was checked", list the local pytest results and say the launch tests run in CI.
    - Add `Pi check pending: ros2 param get /lifecycle_manager_navigation bond_timeout → 10.0; tools/motor_check.py run 0.30 2 → about 0.9 m`.
    - End the body with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
  - Wait for CI with `gh pr checks <n> --watch`. **Do not merge.**
- Verify:
  - `python3 -m pytest tools/tests -q` → all pass.
  - `git diff main -- . ':!*.md' | grep -E '^\+' | grep -Ei 'dry_run(:=|=| *: *)(false|0)'` → no output.
  - `gh pr checks <n>` → all pass.
- Done when: the PR is open with all checks green, unmerged.

## Appendix: content for `docs/run_order.md`

Title: "Driven session run order (2026-11-10)". Sections:

1. **Before power-up:** motor battery charged, voltage measured and written down; a spare if there is one; wiring and common ground reseated; floor marks (home, 1 m line) taped.
2. **On the Pi:**
   1. `cd ~/ros2_ws/src/delivery_bot && git pull`.
   2. `vcgencmd get_throttled` → `0x0`.
   3. `python3 tools/motor_check.py run 0.30 2` → about 0.9 m. Silent means stop and fix the power first.
3. **Every block:** repeat the motor check after any battery swap or if a run is silent. If a run goes silent, mark it `invalid` in `docs/test_log.md`, never `fail`.
4. **Stack rules:**
   - Start in tmux in the foreground; stop with Ctrl-C and wait 20 s before the next start.
   - Drive live only with `-- dry_run:=false` on the command line.
   - Keep Foxglove off unless needed (`run_cell.py` default); camera off.
   - After start, `ros2 param get /lifecycle_manager_navigation bond_timeout` → 10.0.
5. **Order (most valuable first; stop where time or battery runs out):**
   1. CP5: two more 1 m straights on `base.launch.py` with `python3 tools/timed_move.py straight --speed 0.15 --topic cmd_vel` (bar 0.90-1.10 m, ≤ 10 cm sideways by tape).
   2. One straight under `navigation.launch.py` (timed_move default topic), to confirm Nav2 stays up.
   3. Nav2 goal to (1, 0) and back from the home mark.
   4. E2 `rf2o_imu_empty`: straight ×3, spin ×3.
   5. E2 `rf2o_imu_people`: straight ×3, spin ×3.
   6. E3 `slam_empty` ×3, `amcl_empty` ×3.
   7. E3 `slam_people`, `amcl_people`.
   8. E4 step-ins ×3.
   9. E1 demo ×5.
   10. Remaining E2 configs (`rf2o_only`, `imu_only`, `none`) and E3 wrong starts.
6. **Per run:**
   - Start with `python3 tools/run_cell.py <exp> <cell> <run> -- dry_run:=false`; drive with `tools/timed_move.py` in a second shell; tape forward and sideways.
   - Paste the printed row into `docs/test_log.md` with the tape numbers.
   - `python3 tools/analysis/bag_summary.py ~/bags/<bag>` for the odometry numbers.
7. **Fallback if driving fails:** push with a stick for E2 (nobody behind the robot except in people runs).

## Out of scope
- Do not change:
  - `delivery_bot_drivers/` (`motor_node.py`, `drivers.yaml`: the teammate's code, calibrated yesterday);
  - `tools/timed_move.py` (its speed caps);
  - `.github/` (CI);
  - `notes/notes.md`;
  - `evidence/`;
  - `AGENTS.md`;
  - `docs/slam_build_path.md`;
  - `docs/CA3.md`;
  - any Nav2 parameter other than the new `bond_timeout` block.
- Do not add: dependencies, new launch arguments in launch files, a lidar side check, a gyro loop, report or slide content. Do not commit the untracked `delegate-*.md`, `reports/` or `research_notes/` files.
- Do not merge the PR, push to `main`, or SSH to the Pi.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, the code is structured differently, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a missing type annotation, a typo in the instructions) you may handle; list each one under Deviations in the report.
- Commit at the points marked "Then commit", with the message given, ending with a blank line and `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Stage only the files the steps name (`git add <paths>`, never `git add -A`).

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: driven-session prep

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 1: <title> — <one line on what was done>
- [ ] Step N: <title> — <why not done>

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what you found that contradicts the plan, what the planner needs to decide; "None" if none>

### PR
<URL and CI status>
```

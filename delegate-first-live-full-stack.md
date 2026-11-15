````
# Task: first live full-stack run of the merged motor code (supervised)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Run the robot's full stack (lidar, rf2o, EKF, slam_toolbox localisation, Nav2, live motors) on the floor for the first time with the code now on `main`, and record the result. The teammate has already checked wheel direction and driven the robot by teleop (arrow keys / Foxglove), but on her code from before the safety fixes: the motor node's lidar stop and stale-scan stop have only ever run in dry run, and no 1 m straight has ever been recorded. So the run goes: lidar-stop check on the floor, three 1 m straights, then Nav2 goals. Every stage ends in rows in `docs/test_log.md`. This is the gate before tomorrow's (Tue 2026-11-10) driven experiment session.

## Context
- Project: Raspberry Pi 4B delivery robot, ROS 2 Jazzy. RPLidar A1M8, MPU6050 IMU, L298N motor driver. We own only the motor node, IMU node, URDF and scripts; estimation, mapping and navigation are packages (rf2o, robot_localization, slam_toolbox, Nav2).
- Working directory (Mac): `/Users/shermanwee/Documents/MA4890/delivery_bot`. Read `AGENTS.md` there first (short).
- Pi: `ssh robot@100.83.14.99` (key auth works). Repo on the Pi: `~/ros2_ws/src/delivery_bot`, workspace `~/ros2_ws`. SSH is non-interactive, so every remote command must start with `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash`.
- Both the Mac and the Pi are on `main` at `8153ab6` or later; the Pi is already built (`colcon test`: 108 tests, 0 failures).
- A HUMAN is at the robot. The motor battery switch is the kill switch. You cannot see the robot: every physical check is a question to the user.
- Key files (read, do not edit):
  - `delivery_bot_drivers/delivery_bot_drivers/motor_node.py` — subscribes `/cmd_vel` (`geometry_msgs/TwistStamped` only) and `/scan`; dry run by default; 0.5 s watchdog; lidar stop zeroes linear motion when something is within 0.20 m inside ±35° of the direction of travel; stops everything if `/scan` is older than 0.5 s. Log lines to look for: `watchdog: no /cmd_vel for`, `lidar stop: obstacle within`, `stale scan`.
  - `delivery_bot_drivers/config/drivers.yaml` — `min_duty` 0.11, `gain_left` 3.0, `gain_right` 1.0 (rough, by the teammate), `max_duty` 0.85.
  - `delivery_bot_bringup/launch/base.launch.py` — sensors, EKF, motor node, foxglove bridge. Args: `dry_run` (default `true`), `bridge` (default `true`).
  - `delivery_bot_bringup/launch/navigation.launch.py` — includes base, adds slam_toolbox localisation on `~/maps/2026-10-31_room2_graph` and Nav2 (`nav` default `true`). The home mark is map (0, 0), yaw 0.
  - `tools/timed_move.py` — `python3 tools/timed_move.py straight` drives 1.00 m at 0.10 m/s open loop (10 s) on `cmd_vel_smoothed`, through Nav2's collision monitor. Needs the Nav2 stack running.
  - `docs/test_log.md` — table `| Date | Commit | Phase | Test | Result | Numbers | Notes |`; copy the style of the 2026-11-09 rows. Use Phase `2` for motor rows and `7` for Nav2 rows.
  - `notes/notes.md` — append-only lab notebook, newest block at the top, under the header.
- How stacks are run on the Pi: in a tmux session, so they keep running across SSH calls and can be stopped with SIGINT:
  - start: `ssh robot@100.83.14.99 "tmux new -d -s stack 'source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && <launch command> 2>&1 | tee ~/stack_<name>.log'"`
  - stop: `ssh robot@100.83.14.99 "tmux send-keys -t stack C-c"`, wait 10 s, then `ssh robot@100.83.14.99 "tmux kill-session -t stack 2>/dev/null; pgrep -af 'rplidar|motor_node|ros2 launch|nav2|slam_toolbox' | grep -v pgrep"` must print nothing.
  - after a stop, wait 20 s before the next start (lidar start hang, OI-6).
  - Nav2 and localisation need about 30 s after start before they are ready.
- Run every command against `ROS_DOMAIN_ID` unset (the default domain), so Foxglove on the user's machine sees it.

## Decisions already made (do not revisit)
- Order is lidar-stop check → three straights → Nav2 goals. Wheel direction and teleop driving were already checked by the teammate, so there is no raised-wheels stage; do not re-test direction.
- Gains are NOT changed in this task. If the straight curves more than the pass bar, record it and stop; calibration is a separate task the teammate owns.
- Speed stays at or under 0.15 m/s (AGENTS rule 1). Use the speeds written in the steps.
- `dry_run:=false` is typed only on the command line. Never write it into any file except markdown (CI rejects it).
- Stacks are stopped with SIGINT via tmux, never `kill -9` and never `nohup ... &` (a backgrounded launch ignores SIGINT and leaves the lidar spinning so the next start gets no `/scan`).
- Rejected: running the E2/E3 experiment cells (`tools/run_cell.py`) today. That is tomorrow's session.

## Steps
Do these in order. Finish and verify each step before starting the next. A **HUMAN GATE** means: ask the user the question written there, end your turn, and continue only after they answer yes. If at any moment the user reports unexpected motion, first tell them to switch the motor battery off, then stop the stack and go to the report.

### Step 1: Preflight
- Do: on the Mac, `git switch main && git pull --ff-only`, then `git switch -c nav/first-live-run`. On the Pi: `cd ~/ros2_ws/src/delivery_bot && git log --oneline -1` and the leftover check from Context (`pgrep ...`).
- Verify: the Pi commit is `8153ab6` or later; the `pgrep` prints nothing.
- Done when: both copies are on current `main` and nothing ROS is running on the Pi.

### Step 2: Power under load (dry run, nothing moves)
- Do: start `ros2 launch delivery_bot_bringup navigation.launch.py` (dry run is the default) in tmux with log `~/stack_power.log`. After 30 s, sample 18 times, every 10 s: `vcgencmd get_throttled; vcgencmd measure_temp; vcgencmd measure_volts core`. Also run `ros2 param get /motor_node dry_run` once. Then stop the stack.
- Verify: `dry_run` reads `True`. For `get_throttled`, bits 0x50000 are sticky "since boot" history; only the low bits matter now: bit 0x1 (under-voltage now) and bit 0x4 (throttled now). Pass = the value ANDed with 0xF is 0 in all 18 samples.
- Done when: you have the 18 samples written down and a pass/fail. If it fails, stop here and report (driving on an under-volted Pi spoils every number tomorrow).

### Step 3: Full stack up, lidar-stop check on the floor
- **HUMAN GATE A:** "Robot on the taped home mark facing its 0 deg direction (localisation starts from there, so it must be on the mark when the stack starts), motor battery charged and switched on, hand on the motor switch, a box placed about 10 cm in front of the robot. Ready to start the full stack with live motors?"
- Do: start `ros2 launch delivery_bot_bringup navigation.launch.py dry_run:=false` in tmux, log `~/stack_floor.log`. Wait 40 s. Then, one at a time:
  1. `ros2 param get /motor_node dry_run` → must read `False`, else stop the stack and report. `ros2 topic info /cmd_vel -v` → `TwistStamped`.
  2. Front stop: `ros2 topic pub -r 20 -t 60 /cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.10}}}"` (3 s, published straight to the motor node, so Nav2's collision monitor is bypassed and only the motor node's own stop is tested). Ask: did the robot stay still? Check the log for `lidar stop: obstacle within 0.2 m`.
  3. Rear stop: ask the user to move the box to about 10 cm behind the robot, then the same command with `x: -0.10`. Same checks.
  4. Watchdog: check the log for `watchdog: no /cmd_vel` about 0.5 s after each publisher ended.
- Verify: robot did not move in 2 and 3; all three log lines present. Copy the exact log lines.
- Done when: all checks pass. Keep the stack running for Step 4. If the robot moved toward the box, tell the user to switch the motor battery off, stop the stack and report.

### Step 4: One metre straight on the floor
- **HUMAN GATE B:** "Box removed. Robot on the taped home mark facing its 0 deg direction, at least 1.5 m clear ahead and 0.5 m clear to each side (no wall within 0.6 m of the path, or the collision monitor slows it), tape measure ready, hand on the motor switch. Ready?"
- Do: with the Step 3 stack still running, read the start pose with `timeout 5 ros2 run tf2_ros tf2_echo map base_footprint` (last printed translation and yaw). Run `cd ~/ros2_ws/src/delivery_bot && python3 tools/timed_move.py straight`. Read the end pose the same way. Ask the user: distance travelled along the tape (m) and sideways offset of the robot centre from the line (cm).
- Repeat 3 times in total. Before each repeat: ask the user to put the robot back on the mark and confirm. Keep the stack running between repeats.
- Verify: pass bar (design plan P6): 1.00 m ± 0.10 m along and ≤ 10 cm sideways, in all 3 runs. Also compute the slam_toolbox distance (end minus start) for each run.
- Done when: 3 runs are written down with tape and slam numbers. If any run misses the bar, stop the stack and go to the report; do not change gains.

### Step 5: Nav2 goals
- **HUMAN GATE C:** "Robot back on the home mark, the area between the mark and 1 m straight ahead clear, hand on the motor switch. Ready for Nav2 to drive it to (1, 0) and back?"
- Do: with the stack from Step 4 still running, send `ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0}, orientation: {w: 1.0}}}}" --feedback | tail -20`. Record the result status and read the final pose with `tf2_echo` as in Step 4. Ask the user for the tape distance from the home mark to the robot centre. Then send the same goal with `x: 0.0` and ask for the distance from the home mark.
- Verify: both goals end with status `SUCCEEDED`; note the final map pose and tape distances (no pass bar, these are recorded only).
- Done when: both goals are recorded. Then stop the stack and run the leftover check.

### Step 6: Log and PR
- Do: add one row per check to `docs/test_log.md` (Steps 2–5: power, each lidar-stop check, each straight run, each Nav2 goal), with the commit hash, the exact command, pass/fail, and the numbers. Add one block at the top of `notes/notes.md` (below the header and its `---`) titled `## 2026-11-09 (Pi, live) · first live full-stack run: lidar stop, 1 m straight, Nav2 goals`: what ran, results, what failed, next. Then `git add docs/test_log.md notes/notes.md`, commit `nav: 2026-11-09 first live full-stack run`, push, and `gh pr create --base main --title "nav: 2026-11-09 first live full-stack run"` with a body that lists the commands and results and ends with `no-test: log rows only, no code changed`.
- Verify: `git diff main --stat` shows only those two files; `gh pr checks` shows `repo-rules` passing (the `secrets` check may fail because gitleaks cannot download; that is a known infrastructure issue, mention it, do not try to fix it).
- Done when: the PR is open. Do not merge it.

## Out of scope
Do not change: any code, launch file or YAML (`drivers.yaml` gains and pins included), the CI config, `evidence/`, the teammate's branch `feat/motors`.
Do not add: experiment runs (`tools/run_cell.py`), saved goals (`save_goal`), new scripts, speeds above those in the steps.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before using them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, the code is structured differently, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Stop any running stack with SIGINT, then go straight to the report and describe what you found.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a missing type annotation, a typo in the instructions) you may handle; list each one under Deviations in the report.
- Never leave a stack running when you end a turn at a point that is not a HUMAN GATE inside Steps 3–5.
- Commit only in Step 6.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: first live full-stack run

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 1: Preflight — <one line on what was done>
- [x] Step 2: Power under load — <...>
- [ ] Step 3: ... — <why not done>

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what you found that contradicts the plan, what the planner needs to decide; "None" if none>
```
````

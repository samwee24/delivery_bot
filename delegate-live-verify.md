# Task: Finish verifying PR 33 on the robot (pose comparison, run_cell live, CI)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
PR 33 (https://github.com/samwee24/delivery_bot/pull/33, branch `nav/live-switches`) adds launch switches (`ekf:=false`, `ekf_params_file:=`, `localizer:=slam|amcl`) and two tools (`tools/timed_move.py`, `tools/run_cell.py`) for the CA3 driven experiments. Unit tests and a smoke run already pass. Three things are still unverified: (1) with the robot on its taped home mark, what pose each localiser reports; (2) `tools/run_cell.py` has never run live; (3) CI on the PR. When done, all three are checked, any fix is pushed to the PR branch, and `docs/test_log.md` and `notes/notes.md` record the results with the commands that produced them.

## Context
- Project: CA3 room delivery robot. Raspberry Pi 4B, Ubuntu 24.04, **ROS 2 Jazzy**, RPLIDAR A1M8, MPU6050, rf2o + IMU fused by `robot_localization`, `slam_toolbox` localisation on a saved map, Nav2 1.3.x. Read `AGENTS.md` first; its rules apply (safety is structural, config not constants, every number travels with the command that produced it, `notes/notes.md` is append-only newest first, `evidence/` is append-only, PR title format `type: YYYY-MM-DD what`).
- Mac repo `/Users/shermanwee/Documents/MA4890/delivery_bot` is used by another session that switches branches: **do not work there**. Use the existing worktree `/Users/shermanwee/Documents/MA4890/delivery_bot_planh` (branch `nav/live-switches`; `git pull` first). The Mac has no ROS and no pytest: edit on the Mac, test and run on the Pi.
- Pi: `ssh robot@100.83.14.99` (key auth). SSH is non-interactive. Your overlay workspace is `~/planh_ws` (clone at `~/planh_ws/src/delivery_bot`, tracks `origin/nav/live-switches`; the Pi never commits). `~/planh_ws/env.sh` already exists and does: source `/opt/ros/jazzy/setup.bash`, `~/ros2_ws/install/setup.bash`, `~/planh_ws/install/setup.bash`, `export ROS_DOMAIN_ID=42`. Start remote commands with `source ~/planh_ws/env.sh`.
- **Never touch `~/ros2_ws/src/delivery_bot`** (a teammate's clone, on a motor-test branch whose `base.launch.py` starts a live motor node). Your branch is cut from `main`, which starts no motor node.
- Build/test on the Pi: `cd ~/planh_ws && colcon build --symlink-install --packages-select delivery_bot_bringup delivery_bot_slam && source install/setup.bash && colcon test --packages-select delivery_bot_slam && colcon test-result --verbose`, and `cd ~/planh_ws/src/delivery_bot && python3 -m pytest tools/tests -q` (needs `env.sh` sourced). Expected today: 66 colcon tests 0 failures 1 skipped; 94 pytest passed.
- Key files:
  - `delivery_bot_bringup/launch/navigation.launch.py` — `localizer:=slam` (default) starts slam_toolbox localisation; `localizer:=amcl` starts `map_server` + `amcl` (`config/amcl.yaml`, initial pose 0, 0, 0) + `lifecycle_manager_localization`, and Nav2 5 s later.
  - `tools/run_cell.py <exp> <cell> <run> [--dry]` — starts the launch (own process group), waits for `/odometry/filtered` (`/tf` for E2 `none`), records `~/bags/<date>_<exp>_<cell>_run<N>` (MCAP), waits for Enter, SIGINTs bag then launch, prints a `docs/test_log.md` row. Refuses an existing bag name. Cells: `E2 <rf2o_imu|rf2o_only|imu_only|none>_<empty|people>`, `E3 <slam|amcl>_<empty|people|wrongstart>`, `E4 stepin`, `E1 demo`.
  - `docs/test_log.md` (table rows, newest last), `notes/notes.md` (blocks, newest first under the first `---`), `docs/system/06_troubleshooting.md`.
- Conventions: match the existing rows in `docs/test_log.md`; PR title and commits carry the date; commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Decisions already made (do not revisit)
- **Start stacks with job control and stop them with SIGINT.** A launch backgrounded with plain `nohup ... &` ignores SIGINT, so `rplidar_node` is never shut down and the next launch gets **no `/scan`** (symptoms: `rf2o` logs `Waiting for laser_scans....` forever, no `Got first Laser Scan`, AMCL never logs `createLaserObject`, Nav2 reports `Failed to activate global_costmap because transform from base_footprint to map did not become available before timeout`). Use a script that begins with `set -m`, runs `ros2 launch ... > log 2>&1 &`, and stops it with `kill -INT %1; wait %1`. Do not use `pkill -KILL` patterns or broad `pkill -f`; to clean up use only the pid you started.
- The 5 s Nav2 delay in the AMCL branch is correct (an earlier 20 s change was reverted; the failure it chased was the lidar problem above). Do not change it.
- `map_start_pose` for slam_toolbox and `initial_pose` for AMCL are both 0, 0, 0 = the taped home mark (`goals.yaml` home). AMCL keeps reporting about its initial pose until the robot moves, so the AMCL reading mostly confirms AMCL is running; the informative number is how far slam_toolbox's `map -> base_footprint` is from (0, 0) when the robot sits on the mark.
- Everything runs with `bridge:=false`, no motor node, motor switch OFF, the robot does not move. `dry_run:=false` is never passed anywhere.
- Rejected: fixing numbers by editing configs to make the comparison pass (report the numbers as they are); deleting the smoke bags afterwards (leave them, list them in the report).

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 0: Preconditions (stop and ask the user here)
- Do: on the Pi check it is free: `source ~/planh_ws/env.sh; ros2 node list` shows nothing, `ROS_DOMAIN_ID=0 ros2 node list` shows nothing, and `ps -eo args | grep -E "jazzy/lib/(rplidar|nav2)|ekf_node|motor_node" | grep -v grep` is empty. If anything is running, **stop and report** (the lidar is shared). If free, ask the user in a plain message and **wait for a yes**: "Is the robot on the taped home mark, facing the way it faced for mapping, with the motor switch OFF?" Do not launch anything before the yes. Then `cd ~/planh_ws/src/delivery_bot && git fetch -q && git reset -q --hard origin/nav/live-switches && git log --oneline -1`, rebuild and run the colcon and pytest commands above; on the Mac `cd /Users/shermanwee/Documents/MA4890/delivery_bot_planh && git pull`.
- Verify: tests give the expected counts (or better), `git log --oneline -1` on the Pi matches the Mac worktree.
- Done when: the user said yes and the Pi build and tests pass.

### Step 1: slam vs AMCL pose on the home mark
- Do: write `~/planh_ws/pose.sh` on the Pi (not in the repo) taking `slam` or `amcl`:
  ```
  set -m
  source ~/planh_ws/env.sh
  cd ~/planh_ws
  ros2 launch delivery_bot_bringup navigation.launch.py nav:=true localizer:=$1 bridge:=false > pose_$1_$2.log 2>&1 &
  sleep 60
  echo "scan: $(grep -c 'Got first Laser' pose_$1_$2.log)"
  for i in 1 2 3; do timeout 10 ros2 run tf2_ros tf2_echo map base_footprint 2>&1 | grep -m1 -A4 'At time' | grep -E 'Translation|degree'; done
  [ "$1" = amcl ] && timeout 15 ros2 topic echo /amcl_pose --once --field pose.pose
  kill -INT %1; wait %1 2>/dev/null; sleep 3
  echo "leftovers: $(ps -eo args | grep -E 'jazzy/lib/(rplidar|nav2)|ekf_node' | grep -v grep | wc -l)"
  ```
  Run `bash ~/planh_ws/pose.sh slam 1`, then `amcl 1`, then `slam 2`, then `amcl 2`, one at a time. Record translation (x, y in m) and yaw (degrees) from each run, and whether `scan:` was 1 and `leftovers:` 0.
- Verify: every run shows `scan: 1` and `leftovers: 0`; slam readings agree between its two runs to within about 0.1 m and 5 degrees (if not, say so; do not average them away). Compute the distance of each slam reading from (0, 0) and the slam-vs-AMCL difference.
- Done when: four runs recorded. Expected, not required: slam within about 0.2 m of (0, 0); AMCL about (0, 0). If a run shows `scan: 0`, the lidar is wedged: check the previous run left `leftovers: 0`, wait 20 s and rerun once; if it repeats, stop and report.

### Step 2: run_cell.py live (two cells)
- Do: from `~/planh_ws/src/delivery_bot`, with `source ~/planh_ws/env.sh`: first `python3 tools/run_cell.py E3 amcl_empty 99 --dry` to see the plan. Then run it live with a delayed Enter so no tty is needed: `(sleep 45; echo) | python3 tools/run_cell.py E3 amcl_empty 99`. Run number 99 marks these as smoke bags. Then the same for `E2 none_empty 99` (this exercises `ekf:=false` and the `/tf` wait path). Then rerun `E3 amcl_empty 99` once more and confirm it refuses.
- Verify, per live run: exit code 0; the printed row starts `| <today> | <commit> | 9 |` and contains the launch command, the bag path, `get_throttled before` and `after`; `ros2 bag info ~/bags/<date>_E3_amcl_empty_run99` shows storage `mcap`, a duration of roughly 40 s or more, and non-zero message counts for `/scan` and `/tf` (and `/odometry/filtered` for E3; E2 `none` has no `/odometry/filtered`, say what the bag does contain); `ps -eo args | grep -E 'jazzy/lib/(rplidar|nav2)|ekf_node|ros2 bag' | grep -v grep` is empty afterwards. The third run prints `refusing:` and exits 1 without starting anything.
- Done when: both bags exist and read back, no leftovers, the refusal works. If `run_cell.py` leaves processes behind or crashes, that is a bug in `tools/run_cell.py`: fix it in the Mac worktree (smallest change, add or extend a test in `tools/tests/test_run_cell.py` if you changed logic), push, `git pull` on the Pi, rerun the failing cell. Two fix attempts at most, then stop and report.

### Step 3: PR 33 CI
- Do: `gh pr checks 33` (repo `samwee24/delivery_bot`). Jobs to watch: `repo-rules`, `secrets`, `build-and-test`, GitGuardian. If `build-and-test` is still pending, wait with `gh pr checks 33 --watch` (max 15 minutes). If a job fails, read it with `gh run view <run-id> --log-failed`, and fix only what this PR caused (tests, flake8, a docs rule), within the Mac worktree; a failure that also happens on `main` or comes from a changed GitHub setup (for example the known setup-ros 404, rerun fixes it) is not yours: rerun once with `gh run rerun <run-id> --failed`, then report.
- Verify: all checks pass, or each failure is explained.
- Done when: CI is green, or the report names each red job with its error text.

### Step 4: Records
- Do: in the Mac worktree: append one row per Step 1 run pair and per Step 2 cell to the end of `docs/test_log.md` (date, short commit of the PR head, phase `9`, exact commands, result, numbers) in the same style as the existing 2026-11-09 smoke rows; add a block at the top of `notes/notes.md` (newest first, under the first `---`, do not edit old blocks) with the date, what ran, the numbers and what is still open; in `AGENTS.md` replace the "Not yet done: slam-vs-AMCL pose comparison on the home mark, `run_cell.py` live." part of the "Live switches" row with the results (or keep it if a step failed). Any new error you hit goes into `docs/system/06_troubleshooting.md` with its exact text. Commit (`nav: 2026-11-09 live verification rows` style, with the date you run it), push to `nav/live-switches`, `git pull` on the Pi.
- Verify: `gh pr checks 33` after the push (wait for `repo-rules` at least); `git diff origin/main --stat` shows only the earlier PR files plus the docs you edited.
- Done when: pushed, `repo-rules` green. **Do not merge the PR.**

## Out of scope
Do not change: `ekf.yaml`, `nav2_params.yaml`, `slam_localization.yaml`, `slam_mapping.yaml`, `amcl.yaml`, the launch files, `delivery_bot_drivers/`, `delivery_bot_mission/`, `tools/robot_control.py`, CI config, old `notes/notes.md` blocks, existing `evidence/` files. Never touch `~/ros2_ws/src/delivery_bot` on the Pi, never start a motor node, never pass `dry_run:=false`, never drive the robot, never run `tools/timed_move.py`. Do not merge or approve the PR, do not delete bags.
Do not add: features, AMCL or Nav2 tuning, new dependencies, Foxglove buttons.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or command doesn't exist, the structure is different, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a typo in the instructions) you may handle; list each one under Deviations in the report.
- Commit only in Step 2 (if you fix `run_cell.py`) and Step 4, on `nav/live-switches` in the Mac worktree, then push. The Pi never commits.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: Finish verifying PR 33 on the robot

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 0: Preconditions — <...>
- [x] Step 1: slam vs AMCL pose — <...>
- [ ] Step N: <title> — <why not done>

### Pose numbers
<per run: localiser, run, x, y, yaw, scan 1/0, leftovers; slam distance from (0, 0); slam-vs-AMCL difference>

### run_cell results
<per cell: exit code, printed row, ros2 bag info summary (duration, message counts for /scan /tf /odometry/filtered), leftovers, refusal output>

### CI
<each job and its state; for failures the error text and what you did>

### Verification results
<each verify command you ran and its result>

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what contradicts the plan, what the planner needs to decide; "None" if none>
```

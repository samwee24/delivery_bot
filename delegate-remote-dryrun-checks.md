# Task: remote dry-run checks on the Pi before the driven session

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Today (Tue 2026-11-10) the team drives the robot for the CA3 experiments. Before anyone goes to the robot, check over SSH, with the motors in **dry run** (no wheel moves), that:
1. the Pi runs the latest `main`;
2. Nav2 now survives timed moves under full load (yesterday it shut itself down 2-3 s into every run);
3. turning Foxglove off lowers the load;
4. `tools/run_cell.py` records a bag end to end;
5. the Pi's own power holds under load.
Also back up the existing bags to the Mac. Record every result as a row in `docs/test_log.md` and open a docs PR.

## Context
- Project: ROS 2 Jazzy delivery robot on a Raspberry Pi 4B. Read `AGENTS.md` first (short); it is the rulebook (rules 1, 5, 6 and the Conventions section matter here).
- Mac working directory: `/Users/shermanwee/Documents/MA4890/delivery_bot` (repo, no ROS installed). Start with `git switch main && git pull`.
- Pi: `ssh robot@100.83.14.99` (Tailscale; key auth already works; use `-o BatchMode=yes`). Repo on the Pi: `~/ros2_ws/src/delivery_bot`. Install is `--symlink-install`, so `git pull` alone updates Python, launch files and YAML; no rebuild needed.
- Every SSH command must first run `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash` (`.bashrc` is not sourced).
- **Start stacks inside tmux and stop them with Ctrl-C through tmux** (`tmux send-keys -t <session> C-c`), then wait until `pgrep -f "ros2 launch|motor_node|rplidar"` is empty (up to 60 s) and another 20 s before the next start. Never background a launch with `nohup` or `&`: it ignores SIGINT and leaves the lidar stuck.
- To keep a stack's output: `export PYTHONUNBUFFERED=1; ros2 launch ... 2>&1 | tee /tmp/<name>.log` inside the tmux command.
- State at planning time: the Pi was up and idle, on the deleted local branch `fix/motor-gains` at `56abb59`. `vcgencmd get_throttled` read `0x50000`: under-voltage and throttling **occurred since boot** (sticky bits 16 and 18). The bits that matter **now** are 0x1 (under-voltage now) and 0x4 (throttled now).
- Key files and tools (already on `main`):
  - `delivery_bot_bringup/launch/navigation.launch.py`: full stack; arguments `bridge` (Foxglove, default `true`) and `nav` (default `true`). `motor_node` runs in dry run unless told otherwise.
  - `delivery_bot_bringup/config/nav2_params.yaml`: `lifecycle_manager_navigation.ros__parameters.bond_timeout: 10.0`. The launch file applies it with `SetParameter`.
  - `tools/timed_move.py`: `python3 tools/timed_move.py straight --speed 0.15` publishes a 1 m straight (6.67 s) on `/cmd_vel_smoothed`, the collision monitor input. Needs Nav2 up.
  - `tools/run_cell.py`: `python3 tools/run_cell.py <exp> <cell> <run> [--dry] [--bridge] [-- name:=value ...]`. It starts its own `navigation.launch.py` with `bridge:=false`, waits for odometry, records a bag to `~/bags/<date>_<exp>_<cell>_run<N>`, then waits for Enter (`input()`), stops and prints a test_log row.
  - `tools/analysis/bag_summary.py BAG [BAG ...]`: prints a per-bag summary row.
  - `docs/test_log.md`: table `| Date | Commit | Phase | Test | Result | Numbers | Notes |`, one row per test, appended at the end; Phase is `2` for these.

## Decisions already made (do not revisit)
- **Motors stay in dry run for the whole task.** Never pass a `dry_run` argument to anything. Before every `timed_move.py` run, `ros2 param get /motor_node dry_run` must print `Boolean value is: True`. If it prints anything else, stop the stack and stop the task. Nobody is at the robot; a live wheel could drive it off a table.
- **Do not run `tools/motor_check.py`.** It drives the wheels directly.
- **The Nav2 test runs with `bridge:=true` (the default), the worst case,** so a pass means the 10 s `bond_timeout` holds even with Foxglove on. The pass criterion: zero lines matching `CRITICAL FAILURE` or `IS DOWN` in the stack log across 3 timed moves, and `Managed nodes are active` logged once only.
- **Load and power are sampled every 2 s during each timed move** with `cat /proc/loadavg; vcgencmd get_throttled` (in a background loop on the Pi writing to a file, stopped after the run). Report the peak 1-minute load and every distinct `get_throttled` value seen.
- **The backup is copy-only:** `rsync -a` from the Pi to the Mac, never `--delete`, never removing anything on the Pi.
- **The smoke bag from Step 5 is run number 0** and stays in `~/bags` (bags are append-only evidence; `run_cell.py` refuses to overwrite, so run 0 can't clash with real runs, which start at 1).
- Results go in `docs/test_log.md` (append rows) and a new top block in `notes/notes.md` (append-only, newest first, above the current first `## ` heading). No other doc changes.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 1: sync the Pi to `main`
- Do: on the Pi, `cd ~/ros2_ws/src/delivery_bot && git status --short`. If it lists any modified tracked file (lines not starting with `??`), **stop** and report it. Otherwise `git fetch origin && git switch main && git pull`.
- Verify: `git log -1 --oneline` on the Pi equals `git log -1 --oneline origin/main` on the Mac. `grep -n bond_timeout delivery_bot_bringup/config/nav2_params.yaml` shows `10.0`. `ls tools/motor_check.py tools/analysis/bag_summary.py` succeeds.
- Done when: the Pi is on `main` at the same commit as GitHub.

### Step 2: start the full stack in dry run and check the parameters
- Do: `tmux new -d -s nav "bash -c 'source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash; export PYTHONUNBUFFERED=1; ros2 launch delivery_bot_bringup navigation.launch.py 2>&1 | tee /tmp/nav_dry.log'"`. Wait until `grep -a "Managed nodes are active" /tmp/nav_dry.log` matches (poll every 10 s, up to 150 s).
- Verify:
  - `ros2 param get /lifecycle_manager_navigation bond_timeout` → `Double value is: 10.0`
  - `ros2 param get /motor_node dry_run` → `Boolean value is: True`
- Stop if: no "Managed nodes are active" after 150 s, `bond_timeout` is not 10.0, or `dry_run` is not True. Stop the stack, then report with the last 30 lines of `/tmp/nav_dry.log`.
- Done when: both values read as above.

### Step 3: Nav2 survival under 3 timed moves (Foxglove on)
- Do, three times, 20 s apart:
  1. Start the sampler: `(while true; do echo "$(date +%s) $(cut -d' ' -f1 /proc/loadavg) $(vcgencmd get_throttled)"; sleep 2; done) > /tmp/load_runN.txt &`. Note its PID and kill it after the move.
  2. Run `cd ~/ros2_ws/src/delivery_bot && python3 tools/timed_move.py straight --speed 0.15`.
  3. Kill the sampler.
- Then:
  - count `grep -ac "CRITICAL FAILURE\|IS DOWN" /tmp/nav_dry.log`;
  - count `grep -ac "Managed nodes are active" /tmp/nav_dry.log`;
  - take the peak load and the distinct throttled values from the three sample files.
- Verify: the CRITICAL/IS DOWN count is 0, the "active" count is 1, and each `timed_move.py` printed `straight: 6.67 s, 1.000 m`.
- If Nav2 does go down, do not retry or change anything: record it as `fail` with the exact log line and continue to Step 4.
- Done when: three moves ran and the counts are recorded.

### Step 4: load with Foxglove off
- Do:
  1. Stop the stack (Ctrl-C through tmux, wait as described in Context).
  2. Start it again with `bridge:=false` appended to the launch command, log to `/tmp/nav_dry_nobridge.log`.
  3. Wait for "Managed nodes are active" and check `dry_run` is True again.
  4. Do one timed move with the sampler running.
  5. Stop the stack.
- Verify: peak load recorded for this run; CRITICAL count in the new log is 0. Stack fully stopped afterwards (`pgrep -f "ros2 launch|motor_node|rplidar"` empty).
- Done when: you have peak load with Foxglove on (Step 3) and off (this step).

### Step 5: `run_cell.py` end to end (dry run)
- Do: after the 20 s wait, start `tmux new -d -s cell "bash -c 'source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash; cd ~/ros2_ws/src/delivery_bot; python3 tools/run_cell.py E2 rf2o_imu_empty 0 2>&1 | tee /tmp/cell0.log'"`.
  - Wait until `/tmp/cell0.log` contains `recording` (up to 120 s).
  - From a second SSH command, run one `python3 tools/timed_move.py straight --speed 0.15`. Check `dry_run` first (the launch is run_cell's own).
  - Wait 5 s, then `tmux send-keys -t cell Enter`.
  - Wait for the process to finish (up to 60 s) and for `pgrep -f "ros2 launch|motor_node|rplidar"` to be empty.
- Verify:
  - `/tmp/cell0.log` ends with a test_log row;
  - `ls -d ~/bags/*_E2_rf2o_imu_empty_run0` exists;
  - `ros2 bag info <that dir>` shows non-zero counts for `/scan`, `/odom_rf2o`, `/odometry/filtered`, `/cmd_vel`;
  - `python3 tools/analysis/bag_summary.py <that dir>` prints a row with about 6.6 s of commands.
- Stop if `run_cell.py` errors or the bag is missing. Report the log tail.
- Done when: the bag exists with all four topics and `bag_summary.py` reads it.

### Step 6: back up bags and maps to the Mac
- Do, on the Mac:
  ```
  rsync -a robot@100.83.14.99:bags/ ../delivery_bot_pi_backup/bags/
  rsync -a robot@100.83.14.99:maps/ ../delivery_bot_pi_backup/maps/
  ```
  (no `--delete`).
- Verify: `du -sh ../delivery_bot_pi_backup/bags` is at least the Pi's `du -sh ~/bags` (about 150 MB plus the Step 5 bag); the run-0 bag directory exists on the Mac.
- Done when: the copy completes without errors.

### Step 7: record the results
- Do, on the Mac:
  1. `git switch -c docs/remote-dryrun-checks`.
  2. Append one row per step 2-6 to `docs/test_log.md`: date `2026-11-10`, commit = the Pi's short hash, phase `2`, the exact command in the Test column, `pass`/`fail` in Result, the numbers in Numbers.
     - Step 3: CRITICAL count, active count, peak load, throttled values.
     - Step 4: peak load, Foxglove off vs on.
     - Step 5: bag name, topic counts, bag_summary cmd_s.
     - Step 6: sizes.
     - Notes: "dry run, no wheel moved".
  3. Add a short top block to `notes/notes.md` (heading `## 2026-11-10 (Pi, remote, dry run) · Nav2 heartbeat, load, run_cell smoke, backup`, 4-6 lines, then `---`). It must say whether OI-10 (Nav2 heartbeat shutdown) looks fixed in dry run and whether the Pi's own power showed under-voltage *now* (0x1) under load.
  4. Commit `docs: 2026-11-10 remote dry-run checks: Nav2 bond_timeout, load, run_cell smoke` with trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
  5. Push and open a PR to `main`: title the same as the commit, body following `.github/pull_request_template.md`, `no-test: docs only (results of Pi dry-run checks)`, ending with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
  6. Wait for `gh pr checks <n> --watch`. Do not merge.
- Verify: `gh pr checks <n>` all pass; `git diff main --stat` lists only `docs/test_log.md` and `notes/notes.md`.
- Done when: the PR is open and green.

## Out of scope
Do not change:
- any code, launch file or YAML (including `nav2_params.yaml` and `drivers.yaml`, even if Nav2 fails);
- the Pi's system config, power settings, sudo anything;
- `evidence/`.

Do not:
- run `motor_check.py`;
- pass any `dry_run` argument;
- delete or move anything on the Pi;
- reboot the Pi;
- merge the PR;
- commit the untracked `delegate-*.md`, `reports/` or `research_notes/` files.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, the code is structured differently, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found.
- Before stopping for any reason, make sure no stack is left running on the Pi (Ctrl-C through tmux, then `pgrep` empty).
- If SSH stops answering, wait 60 s and retry once. If it still fails, stop and report: the Pi may have rebooted, which is itself a power finding.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a missing type annotation, a typo in the instructions) you may handle; list each one under Deviations in the report.
- Commit only in Step 7, staging only `docs/test_log.md` and `notes/notes.md` by name.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: remote dry-run checks

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 1: <title> — <one line on what was done>
- [ ] Step N: <title> — <why not done>

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Key numbers
- bond_timeout on the Pi:
- Nav2 CRITICAL count over 3 moves (Foxglove on):
- Peak 1-min load, Foxglove on / off:
- get_throttled values seen:
- run-0 bag name and topic counts:
- Backup size on the Mac:

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what you found that contradicts the plan, what the planner needs to decide; "None" if none>

### PR
<URL and CI status>
```

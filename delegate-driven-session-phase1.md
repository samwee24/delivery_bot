# Task: driven session, phase 1 (power gate, motor check, CP5 straights, Nav2 goal)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
Today (Tue 2026-11-10) the operator is in the lab with the robot. You drive the Pi over SSH; the operator places the robot, holds the motor switch, and reads the tape. This phase answers, in order:
1. Is the Pi's own power supply good enough for Nav2 (OI-11)?
2. Does the motor battery deliver (motor check)?
3. Do 1 m straights pass on `base.launch.py` (CP5: 2 more passes needed; pass 1 was 0.96 m, 3 cm left on 2026-11-09)?
4. Does Nav2 stay up through a live straight, and reach a goal at (1, 0) and come back?

Then record everything in `docs/test_log.md` and `notes/notes.md` and open a docs PR. The experiments (E2, E3, E4, E1) are the next phase, not this one.

## Context
- Project: ROS 2 Jazzy delivery robot, Raspberry Pi 4B. Read `AGENTS.md` (short, the rulebook) and `docs/run_order.md` (today's checklist; this task follows its §1-§5 items 1-3) before starting.
- Mac repo: `/Users/shermanwee/Documents/MA4890/delivery_bot`. Start with `git switch main && git pull`. Check `gh pr view 41 --json state --jq .state` prints `MERGED`; if not, stop and ask the operator to merge PR 41 first.
- Pi: `ssh -o BatchMode=yes robot@100.83.14.99` (Tailscale). Fallback `robot@192.168.31.109`. Repo on the Pi: `~/ros2_ws/src/delivery_bot` (`--symlink-install`, so `git pull` is enough, no rebuild).
- Every SSH command first runs `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash`.
- **Stacks:** start inside tmux, log with `export PYTHONUNBUFFERED=1; ... 2>&1 | tee /tmp/<name>.log`. Stop with `tmux send-keys -t <session> C-c`, then wait until `ps -eo args | grep -E "[r]os2 launch|[m]otor_node|[r]plidar"` is empty (up to 60 s), then 20 s more before the next start. Never `nohup`/`&` a launch. Do not use `pgrep -f` over SSH (it matches its own shell).
- **Bags:** `ros2 bag record -s mcap -o ~/bags/<name> <topics>` in its own tmux session, stopped with C-c; check `metadata.yaml` exists afterwards. Bags are append-only: never overwrite or delete one.
- `vcgencmd get_throttled` bits: 0x1 under-voltage now, 0x4 throttled now; 0x10000/0x40000 are sticky history since boot.
- Known hardware facts:
  - The motor battery gives about one run per power cycle (OI-9). A run where the wheels don't turn, or `motor_node` logs only `watchdog`, is a battery problem: mark it `invalid`, never `fail`.
  - Motor settings were calibrated on 2026-11-09 (`drivers.yaml`: 100 Hz PWM, gains 0.41, kick 0.30 for 0.35 s). They belong to the teammate.
  - The collision monitor's slowdown zone cuts speed to 0.3× near walls, so Nav2 runs need clear floor (at least 0.5 m around the path).
  - Nav2 goal tolerance is 0.10 m xy, 0.3 rad yaw (`nav2_params.yaml`, FollowPath goal checker). The 2026-11-08 planner check planned (1, 0) as a 1.18 m path.
- `docs/test_log.md`: table `| Date | Commit | Phase | Test | Result | Numbers | Notes |`, rows appended at the end.

## Talking to the operator
You need the operator for every physical action. Before each one, ask with one short, concrete question and wait for the answer:
- placement: "Robot on the home mark, facing along the 1 m line, 1.5 m clear ahead?"
- battery: "Motor battery switched off and on?" (before every live run, because of OI-9)
- ready: "Hand on the motor switch, ready?" Do not start any wheel motion without a yes to this.
- results: "Tape: forward distance (m) and sideways offset (cm, left or right)?"
If the operator reports anything unexpected (robot veers, doesn't stop, smoke, a wire), stop the stack at once and stop the task.

## Decisions already made (do not revisit)
- **Live motors only from the command line of the launch you start**, as `dry_run:=false` typed in the tmux command. Never write `dry_run:=false` into any file other than markdown. Never raise `v_max` or any speed above 0.15 m/s.
- **Do not edit any code, launch file or YAML**, including `drivers.yaml` (the teammate's) and `nav2_params.yaml`. If straights fail the bar, record and stop; no tuning.
- **Power gate decides the Nav2 steps.** If any sample in Step 2 has bit 0x1 or 0x4, the supply is still bad: do Steps 3-4 (motor check, CP5 on `base.launch.py`), skip Steps 5-6, and go to Step 7. Nav2 under a browning-out supply is not worth the battery.
- **CP5 bar:** forward 0.90-1.10 m by tape, sideways ≤ 10 cm. Two runs today.
- **`tools/motor_check.py`** is the only direct-GPIO tool allowed, and only in Step 3, with the operator's yes. It refuses while `motor_node` runs.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 1: sync and idle power
- Do: on the Pi, `cd ~/ros2_ws/src/delivery_bot && git status --short` (stop if a tracked file is modified), `git switch main && git pull`. Run the `ps` check (must be empty), `uptime`, `vcgencmd get_throttled`.
- Ask the operator: was the Pi's supply replaced with a 5.1 V 3 A Pi 4 supply, and when did the Pi last boot?
- Verify: Pi `git log -1 --oneline` equals Mac `git log -1 --oneline origin/main`.
- Done when: commit, uptime, idle `get_throttled` and the supply answer are noted.

### Step 2: power gate under Nav2 load (dry run, no wheel moves)
- Do:
  1. Start a sampler: `(while true; do echo "$(date +%s) $(cut -d' ' -f1 /proc/loadavg) $(vcgencmd get_throttled)"; sleep 2; done) > /tmp/power_gate.txt &`, PID saved to `/tmp/sampler.pid`.
  2. `tmux new -d -s nav "bash -c '<source lines>; export PYTHONUNBUFFERED=1; ros2 launch delivery_bot_bringup navigation.launch.py bridge:=false 2>&1 | tee /tmp/nav_gate.log'"` (no `dry_run` argument: dry run is the default).
  3. Poll every 10 s for `Managed nodes are active` (up to 300 s), note the seconds; then sample 60 s more.
  4. Stop the stack, then the sampler (`kill $(cat /tmp/sampler.pid)`).
- Verify: `ros2 param get /lifecycle_manager_navigation bond_timeout` read `10.0` while it ran; `grep -ac "CRITICAL FAILURE\|IS DOWN" /tmp/nav_gate.log`.
- Report from `/tmp/power_gate.txt`: peak load1, distinct `get_throttled` values, samples with 0x1 (N of M).
- Done when: verdict **GOOD** (no 0x1/0x4 in any sample, Nav2 active, CRITICAL 0) or **BAD** (anything else). Tell the operator the verdict.

### Step 3: motor check (wheels move)
- Do: robot on the floor at the start of the 1 m line, clear ahead; battery cycled; operator ready. Then `python3 tools/motor_check.py run 0.30 2`. Ask for the tape distance.
- Verify: 0.80-1.00 m (expected 0.87-0.90). Silent or under 0.5 m: ask the operator to cycle or charge the battery and retry once. If it's still silent, stop the task (motor power, OI-9).
- Done when: one run in range.

### Step 4: CP5 straights on `base.launch.py` ×2 (live)
- Do, for run 2 and run 3:
  1. Placement, battery, ready (see Talking to the operator).
  2. `tmux new -d -s base "bash -c '<source lines>; export PYTHONUNBUFFERED=1; ros2 launch delivery_bot_bringup base.launch.py dry_run:=false 2>&1 | tee /tmp/base_cp5_N.log'"`. Wait for `/odom_rf2o` (`ros2 topic echo --once /odom_rf2o`, retry up to 60 s).
  3. Check `ros2 param get /motor_node dry_run` is `False` and `ros2 param get /motor_node gain_left` is `0.41`.
  4. Bag: `ros2 bag record -s mcap -o ~/bags/2026-11-10_CP5_straight_runN /cmd_vel /odom_rf2o` in tmux session `bag`; wait for `Recording...`.
  5. `cd ~/ros2_ws/src/delivery_bot && python3 tools/timed_move.py straight --speed 0.15 --topic cmd_vel`.
  6. Stop the bag (wait 3 s first), then the stack. Ask for the tape.
  7. `python3 tools/analysis/bag_summary.py ~/bags/2026-11-10_CP5_straight_runN` for the rf2o distance.
- Verify: tape within the CP5 bar.
- If a run fails the bar for a reason other than the battery: record it, do not retry beyond one more battery-cycled attempt, do not tune.
- Done when: two runs recorded (pass, fail or invalid each).

### Step 5: one live straight under `navigation.launch.py` (only if Step 2 was GOOD)
- Do: placement (clear 1.5 m, at least 0.5 m from walls), battery, ready. Start `navigation.launch.py bridge:=false dry_run:=false` in tmux `nav`, logged to `/tmp/nav_live1.log`. Wait for `Managed nodes are active`; check `bond_timeout` 10.0 and `dry_run` False. Run `python3 tools/timed_move.py straight --speed 0.15` (default topic, the collision monitor input). Wait 15 s. Ask for the tape. Keep the stack running if CRITICAL is 0.
- Verify: `grep -ac "CRITICAL FAILURE\|IS DOWN" /tmp/nav_live1.log` is 0. The distance is recorded but not judged (slowdown zone).
- Done when: the CRITICAL count and tape are recorded. If Nav2 went down, record the exact line, stop the stack, skip Step 6.

### Step 6: Nav2 goal to (1, 0) and back (only if Step 5 kept Nav2 up)
- Do:
  1. Operator carries the robot back to the home mark, facing +x (along the 1 m line). Battery cycled, ready.
  2. Check localisation: `ros2 run tf2_ros tf2_echo map base_footprint` (a few seconds, `timeout -s INT 6`). Translation must be within 0.10 m of (0, 0). If not, ask the operator to reposition once; if still off, record it and stop this step.
  3. `ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0}, orientation: {w: 1.0}}}}"`, with a 120 s `timeout -s INT`. Note the result status and time.
  4. Ask for the tape: where it stopped relative to the (1, 0) mark. Battery cycled, ready.
  5. Same goal to `x: 0.0`. Note the status. Ask for the tape relative to the home mark.
  6. Stop the stack; CRITICAL count in the log.
- Verify: both goals `SUCCEEDED`, each stop within 0.25 m of its mark by tape, CRITICAL 0.
- Done when: both goals are recorded.

### Step 7: back up, record, PR
- Do:
  1. Ensure nothing runs on the Pi (`ps` check empty; no sampler, no bag).
  2. On the Mac: `rsync -a robot@100.83.14.99:bags/ ../delivery_bot_pi_backup/bags/` (never `--delete`).
  3. `git switch -c docs/driven-session-cp5`. Append one row per step 2-6 to `docs/test_log.md`: date 2026-11-10, the Pi's short hash, phase `2` (Steps 2-5) or `7` (Step 6), the exact command, `pass`/`fail`/`invalid`, numbers (tape, rf2o, load, throttled, CRITICAL count, goal status). Note `dry run, no wheel moved` on Step 2's row.
  4. New top block in `notes/notes.md` above the first `## ` heading: `## 2026-11-10 (Pi, lab) · power gate, motor check, CP5 straights, Nav2 goal`, 4-6 lines: supply verdict, CP5 result (3 of 3 passes or not), Nav2 result, what is ready for the experiments. Then `---`.
  5. Tick in `docs/slam_build_path.md` only lines that are now unambiguously done (the Pi supply check under 9.3, CP5 if 3 of 3 pass). Change nothing else there.
  6. Commit only those three files by name: `docs: 2026-11-10 driven session phase 1: power gate, CP5 straights, Nav2 goal`, trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
  7. Push; `gh pr create` to `main`, same title, body per `.github/pull_request_template.md` with `no-test: docs only (driven-session results)` and the Pi commands behind each number, ending with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. `gh pr checks <n> --watch`. Do not merge.
- Verify: checks pass; `git diff main --stat` lists only `docs/test_log.md`, `notes/notes.md`, `docs/slam_build_path.md`.
- Done when: PR open and green.

## Out of scope
- Do not change any code, launch file, YAML, `.github/`, or `evidence/`.
- Do not run E2/E3/E4/E1 cells or `tools/run_cell.py`; that is the next phase.
- Do not reboot the Pi, change system settings, or use sudo.
- Do not delete or move anything on the Pi or in the backup folder.
- Do not commit `delegate-*.md`, `reports/`, `research_notes/`, `.venv`.
- Do not merge the PR.

## How to work
- Follow the steps as written. Do not add features, refactor, rename, or change dependencies.
- If a step's instructions don't match what you find (a file, tool or option missing, a command failing for a reason unrelated to the robot), **stop** and report. Do not improvise.
- A run spoiled by the battery may be repeated once after a battery cycle; say so in the row.
- If SSH stops answering, wait 60 s and retry once; if it still fails, ask the operator whether the Pi rebooted (a power finding), then stop.
- Before stopping for any reason: stack, bag and sampler stopped on the Pi, and the operator told the motors are off.
- Trivial things a step obviously needs you may handle; list each under Deviations.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: driven session phase 1

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 1: <title> — <one line>
- [ ] Step N: <title> — <why not done>

### Verification results
<each verify command and its result, key output lines>

### Key numbers
- Supply replaced (operator): / idle get_throttled:
- Power gate: time to active, peak load, 0x1 samples N of M, verdict:
- Motor check tape:
- CP5 run 2 / run 3: tape forward, sideways, rf2o:
- Nav2 live straight: CRITICAL count, tape:
- Nav2 goal (1,0) / back: status, stop error by tape:

### Files changed
- `<path>` — <what changed>

### Deviations
<or "None">

### Problems / open questions
<or "None">

### PR
<URL and CI status>
```

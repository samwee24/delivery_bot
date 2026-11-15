# Task: OI-8 live push test (angle_compensate true vs false, nobody in the scan)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

This task is **interactive**: the user is at the robot and does the physical steps (battery, pushing). You run commands over SSH, tell the user exactly what to do and when, wait for them to say "done", then continue. Give one physical instruction at a time, in plain numbered lines.

## Goal
Settle open issue OI-8: rf2o laser odometry read only 24 % of the true distance on two hand pushes on 2026-11-01, against -3.8 % on 2026-10-31. Offline replay checks have run out; two suspects are left: (a) the 720-beam scan format produced by `angle_compensate:=true`, (b) a person walking behind the robot during the push. One live session with nobody in the scan, on a charged battery, run once with each `angle_compensate` setting, separates them. Result goes into `docs/test_log.md`, `notes/notes.md` and the OI-8 row of `docs/CA3.md`, through a PR.

## Context
- Project: CA3 room delivery robot. Raspberry Pi 4B, ROS 2 Jazzy, RPLIDAR A1M8, rf2o laser odometry. Read `AGENTS.md` first (short); its rules apply.
- Mac working directory: `/Users/shermanwee/Documents/MA4890/delivery_bot`
- Pi: `ssh robot@100.83.14.99` (Tailscale; key auth works). Repo on Pi: `~/ros2_ws/src/delivery_bot/`. SSH is non-interactive: every remote command must start with `source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash;`. Bags live in `~/bags` on the Pi only.
- Key files:
  - `tools/analysis/push_start.sh` — starts lidar + rf2o (`rf2o_alone.launch.py`) + IMU, then records a bag. Currently hard-codes `angle_compensate:=false`, names the bag `~/bags/2026-11-01_push_HHMMSS`, and does not record `/marker`.
  - `tools/analysis/push_stop.sh` — stops the bag and the nodes, then runs `push_an.py` on the newest `~/bags/2026-11-01_push_*` bag.
  - `tools/analysis/marker_pub.py` — publishes `/marker` strings from one publisher: `python3 tools/analysis/marker_pub.py "push start" 3 "push end"` style.
  - `tools/analysis/pushwall.py` — `pushwall.py <bag> [t_start t_end]`: per-second front (0 deg) and back (180 deg) wall range, rf2o x, rear points; with a window, rf2o straight-line distance and wall-range change. Times are seconds from the first `/scan`.
  - `tools/analysis/push_an.py` — `push_an.py <bag> [t0 t1]`: rf2o track and window distance.
  - `delivery_bot_slam/launch/rf2o_alone.launch.py` — takes `angle_compensate` (default `true`).
  - `docs/test_log.md` — one table row per run; columns `Date | Commit | Phase | Test | Result | Numbers | Notes`. See rows 55-63 for the OI-8 style.
  - `notes/notes.md` — lab notebook, newest block first, **append-only** (insert a new block under the `---` after the header; never edit old blocks).
  - `docs/CA3.md` — OI-8 row (around line 59), edited in place.

## Decisions already made (do not revisit)
- Push the robot with a stick, broom handle or string of at least 1 m; the user stands still, in **front** of the robot (ahead of travel direction) or at the side, at least 1.5 m away, and does not walk behind it. Because suspect (b) is a person in the scan behind the robot.
- Ground truth = a 1.000 m tape line on the floor, plus the front/back wall-range change from `pushwall.py`. Same as the 2026-10-31 good push (0.962 m).
- Two runs: **A** with `angle_compensate:=true` (current default), **B** with `angle_compensate:=false`. Same tape, same start, same speed (slow, about 10 s for 1 m).
- `vcgencmd get_throttled` logged before and after each run. Battery must be charged: if `get_throttled` shows bit 0 set (value ends in odd hex digit, e.g. `0x50005`, `0x1`) **before** run A, stop and tell the user to charge/swap; do not run on under-voltage.
- Pass line: rf2o window distance / true distance >= 0.87 counts as "reads correctly" (same line as earlier OI-8 rows).
- Do not change any config default or the rf2o/lidar YAML in this task, whatever the result. That is the planner's call afterwards.
- The camera stays off; no mapping or localisation stack runs during the test.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 1: Sync and branch
- Do: on the Mac, `git checkout main && git pull`, then `git checkout -b test/oi8-live-push`. Leave untracked `reports/`, `research_notes/` and this file alone.
- Verify: `git status -sb` → on `test/oi8-live-push`, no modified tracked files.
- Done when: branch exists locally.

### Step 2: Make push_start.sh / push_stop.sh take the setting
- Do: edit `tools/analysis/push_start.sh` so that `$1` is the angle_compensate value (default `true` if absent), it is passed to `rf2o_alone.launch.py angle_compensate:=$AC`, the bag is named `~/bags/$(date +%F)_push_ac${AC}_$(date +%H%M%S)`, `/marker` is added to the `ros2 bag record` topic list, and `vcgencmd get_throttled` is echoed at the start. Edit `tools/analysis/push_stop.sh` so it picks the newest `~/bags/*_push_*` bag and echoes `vcgencmd get_throttled` at the end. Nothing else changes.
- Verify: `bash -n tools/analysis/push_start.sh && bash -n tools/analysis/push_stop.sh` → no output. `grep -n 'dry_run' tools/analysis/push_*.sh` → nothing.
- Done when: both scripts parse; commit `tools: <today> push scripts take angle_compensate, record /marker`, `git push -u origin test/oi8-live-push`.

### Step 3: Pre-flight on the Pi
- Do: on the Pi, `cd ~/ros2_ws/src/delivery_bot && git fetch && git checkout test/oi8-live-push && git pull`. Then check nothing else is running: `ps -eo cmd | grep -cE '[s]lam_toolbox|[r]os2 launch|[r]plidar_c|[i]mu_node|[e]kf_node|[r]f2o|[r]os2 bag'` must be 0 (if not, ask the user before stopping anything; `robot_control.py` and the Foxglove bridge may stay). Run `vcgencmd get_throttled`.
- Tell the user: (1) charge or swap the Pi battery if not done, (2) lay or confirm a 1.000 m tape line on the floor with a clear start mark, away from walls by at least 0.5 m, (3) place the robot at the start, front pointing along the tape, (4) get a stick/broom/string.
- Verify: stale count 0; `get_throttled` bit 0 clear.
- Done when: user confirms the setup and throttled is clean. If throttled bit 0 is set, stop and report.

### Step 4: Run A (angle_compensate true)
- Do: `bash ~/ros2_ws/src/delivery_bot/tools/analysis/push_start.sh true` on the Pi (it waits ~35 s). Check its printed counts: S/N lines >= 1, rf2o odom lines > 0, imu fail 0, "Recording" present. Then tell the user: "Stand in front of the robot or to the side, 1.5 m+ away, still. I'll mark start." Run `python3 ~/ros2_ws/src/delivery_bot/tools/analysis/marker_pub.py "push start"`, then tell the user: "Push slowly along the tape to the 1 m mark, about 10 s, keep straight, then stop and say done. Don't step behind it." After "done", run `marker_pub.py "push end"`, wait 3 s, run `bash ~/ros2_ws/src/delivery_bot/tools/analysis/push_stop.sh`. Ask the user for the true distance travelled (tape reading, cm).
- Verify: push_stop prints the bag path, `left: 0`, throttled value, and a push_an track.
- Done when: bag exists, true distance noted.

### Step 5: Run B (angle_compensate false)
- Do: user returns the robot to the same start mark, same heading. Repeat step 4 exactly with `push_start.sh false`.
- Verify / Done when: as step 4.

### Step 6: Analyse both bags
- Do: for each bag, `python3 ~/ros2_ws/src/delivery_bot/tools/analysis/pushwall.py <bag>` to find the push window (front wall range starts falling / back wall rising; markers are a cross-check). Then `pushwall.py <bag> <t_start> <t_end>` with t_start = last still second, t_end = first still second after. Record: rf2o window distance, wall-range change front/back, ratio rf2o / tape, rear-points median and max, beam count per scan (from `ros2 bag info` or one scan), throttled before/after.
- Verify: wall-range change agrees with the tape within 5 cm (if not, say so; the tape number wins for the ratio but flag it). Rear points stay roughly constant (no person behind).
- Done when: you can fill this table:

| Run | angle_compensate | beams | tape m | wall change m | rf2o m | ratio | rear pts | throttled before/after |

Then apply the decision rule and state it in one line:
  - A >= 0.87 and B >= 0.87 → format cleared; the 2026-11-01 failure points at the person behind the robot (suspect b).
  - A < 0.87 and B >= 0.87 → suspect (a): `angle_compensate:=true` / 720-beam format breaks rf2o.
  - both < 0.87 → neither suspect explains it; OI-8 stays open, new cause needed.
  - A >= 0.87 and B < 0.87 → unexpected; report it, no conclusion.

### Step 7: Record
- Do: on the Mac (never edit these on the Pi):
  - `docs/test_log.md`: two rows (A, B), Commit = hash of step 2's commit, Phase 3, exact Pi commands, numbers from the table.
  - `notes/notes.md`: new block at the top (below the header's `---`), title `## <date> (Pi, live) · OI-8: live push, nobody in the scan`, with table, verdict line, next.
  - `docs/CA3.md` OI-8 row: replace the "Next:" clause with the result and the verdict line. Do not mark it resolved unless the rule gave case 1 or 2; even then write "cause identified", not "fixed".
  - Save the two pushwall window outputs as a new file `evidence/lidar/<date>_oi8_live_push.txt` (new file only, never edit existing evidence).
- Verify: `git diff --stat` touches only `tools/analysis/push_start.sh`, `tools/analysis/push_stop.sh`, `docs/test_log.md`, `notes/notes.md`, `docs/CA3.md`, the new evidence file. `git diff notes/notes.md` shows only added lines.
- Done when: committed as `test: <date> OI-8 live push angle_compensate true vs false`.

### Step 8: PR (ask first)
- Do: show the user the table and verdict, and ask "Open the PR?". On yes: `git push`, `gh pr create --base main --title "test: <date> OI-8 live push angle_compensate true vs false"`; body = what ran, the Pi commands, the table, verdict, and `no-test: shell glue for a hardware run, logged in docs/test_log.md`. End the body with the attribution line `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- Verify: `gh pr checks` → `repo-rules` green (wait for it; if it fails, read the log, fix within these files, max 2 attempts).
- Done when: PR open with CI green. Do not merge.
- Then: on the Pi, `git checkout main` so it is not left on the branch.

## Out of scope
Do not change: any YAML config, any launch file, `rf2o` settings, `robot_control.py`, motor code, `goals.yaml`, old rows/blocks in `docs/test_log.md` or `notes/notes.md`, anything in `evidence/` except the one new file.
Do not add: new analysis scripts (use the existing ones), extra test runs beyond A and B unless the user asks, a config change based on the result.
Never pass `dry_run:=false`; never drive motors.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, a node fails to start, the lidar gives no S/N, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found, with the shortest decisive error line.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- If a run is spoiled (someone walked behind, robot bumped, push not straight), tell the user and redo that run once; note the spoiled bag in the report.
- Trivial things a step obviously needs you may handle; list each one under Deviations.
- Commit only at the points the steps say. End every commit message with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: OI-8 live push test

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 1: Sync and branch — <one line>
- [ ] ...

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Result table and verdict
<the step 6 table, and the one-line decision-rule verdict>

### Files changed
- `<path>` — <what changed>

### Deviations
<"None" if none>

### Problems / open questions
<"None" if none>
```

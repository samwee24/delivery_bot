# Task: remote dry-run checks, retry (Foxglove off, longer start, power sampled)

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
A first attempt at these checks stopped: the full stack never finished starting. Nav2's lifecycle manager stalled while activating `docking_server` after 150 s, at load about 31. `vcgencmd get_throttled` read `0x50005`, which means the Pi's own supply was under-voltage and the CPU throttled during start-up.

Retry with lighter settings and record the power numbers. The result decides whether the Pi's supply has to be replaced before today's driven session:
1. Does Nav2 come up at all with Foxglove off?
2. Does it survive 3 timed moves with the 10 s `bond_timeout`?
3. Does `run_cell.py` record a bag?
4. Back up the bags.

## Context
- Read `delegate-remote-dryrun-checks.md` in the repo root. It is the first task's prompt, and its **Context**, **Decisions already made**, **Out of scope** and **How to work** sections all apply here unchanged. Its Steps 5, 6 and 7 are reused below.
- Already done in the first attempt (do not redo): the Pi is on `main` at the same commit as GitHub (`be4473e` or newer: run `git pull` on the Pi first, then check the hashes match).
- Lesson from the first attempt: `pgrep -f` over `ssh 'bash -c ...'` matches its own shell. To check for running stacks, use `ps -eo args | grep -E "[r]os2 launch|[m]otor_node|[r]plidar"` (empty output = nothing running).
- `get_throttled` bits: 0x1 = under-voltage now, 0x4 = throttled now, 0x10000/0x40000 = happened since boot (sticky). `0x50000` at idle is the sticky history; `0x50005` means under-voltage and throttling right now.

## Decisions already made (do not revisit)
- **Foxglove off is the main condition** (`bridge:=false` on `navigation.launch.py`), because the full-load start failed. Do not run a Foxglove-on comparison in this task.
- **Start-up wait is 300 s** (poll every 10 s for `Managed nodes are active`).
- **Power and load are sampled every 2 s from just before launch until the stack is stopped**, not only during moves. Use one background sampler writing `epoch load1 throttled` lines to `/tmp/power_retry.txt`, started before the launch and killed after the final stop.
- **Motors stay in dry run** (no `dry_run` argument anywhere). `ros2 param get /motor_node dry_run` must read `Boolean value is: True` before any `timed_move.py`. Never run `tools/motor_check.py`.
- If Nav2 still does not come up in 300 s: stop the stack, skip Steps B and C, still do Step D (backup) and Step E (log the failure with the power numbers). That result is the evidence the supply must change.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step A: start with Foxglove off, power sampled from the start
- Do:
  1. On the Pi, check nothing is running (`ps` check above) and `git pull`.
  2. Start the sampler: `(while true; do echo "$(date +%s) $(cut -d' ' -f1 /proc/loadavg) $(vcgencmd get_throttled)"; sleep 2; done) > /tmp/power_retry.txt &` and note its PID in `/tmp/sampler.pid`.
  3. Start `tmux new -d -s nav "bash -c 'source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash; export PYTHONUNBUFFERED=1; ros2 launch delivery_bot_bringup navigation.launch.py bridge:=false 2>&1 | tee /tmp/nav_dry2.log'"`.
  4. Poll for `Managed nodes are active` up to 300 s, and note the seconds it took.
- Verify:
  - `ros2 param get /lifecycle_manager_navigation bond_timeout` → `10.0`
  - `ros2 param get /motor_node dry_run` → `True`
- If not active by 300 s: copy the last 20 `lifecycle_manager` lines from the log, stop the stack, then go to Step D.
- Done when: Nav2 is active and both parameters read as above, or the timeout is recorded.

### Step B: 3 timed moves
- Do: three times, 20 s apart: check `dry_run` is True, then `cd ~/ros2_ws/src/delivery_bot && python3 tools/timed_move.py straight --speed 0.15`. Note each move's start and end epoch.
- Then count `grep -ac "CRITICAL FAILURE\|IS DOWN" /tmp/nav_dry2.log` and `grep -ac "Managed nodes are active" /tmp/nav_dry2.log`.
- Verify: CRITICAL count 0 and "active" count 1 means pass; anything else means fail. Record the exact lines.
- Then stop the stack (Ctrl-C through tmux, wait until the `ps` check is empty, then 20 s).
- Done when: three moves ran and the counts are recorded.

### Step C: `run_cell.py` smoke run
- Do: Step 5 of `delegate-remote-dryrun-checks.md` exactly. `run_cell.py` already uses `bridge:=false`.
- Done when: as written there.

### Step D: backup
- Do: Step 6 of `delegate-remote-dryrun-checks.md` exactly. Then stop the sampler (`kill $(cat /tmp/sampler.pid)`) and copy `/tmp/power_retry.txt` from the Pi to the Mac scratch dir.
- From the sampler file, report:
  - the peak load1;
  - every distinct `get_throttled` value with its first and last epoch;
  - how many samples had bit 0x1 (under-voltage now) set, as a count and a percentage;
  - for each of these phases, whether 0x1 appeared and the peak load: start-up (launch to active), moves, idle.
- Done when: backup done and the power summary computed.

### Step E: record
- Do: Step 7 of `delegate-remote-dryrun-checks.md`, with these changes:
  - Rows for Steps A-D of this task.
  - Step A's row gives the time to "active" (or "not active in 300 s") and the power numbers.
  - The notes block must state plainly whether the Pi's supply showed under-voltage now (0x1) during start-up and during moves. It must say whether the supply should be replaced before the driven session: replace it if any sample had 0x1.
  - Use the same branch name, commit message and PR rules, title `docs: 2026-11-10 remote dry-run checks (retry, Foxglove off): Nav2, Pi power, run_cell smoke`. Do not merge.
- Done when: PR open and green.

## Out of scope
Same as `delegate-remote-dryrun-checks.md`. Do not change any code, launch file or YAML, even to drop `docking_server` or other Nav2 servers. Do not reboot the Pi.

## How to work
Same as `delegate-remote-dryrun-checks.md`. Before stopping for any reason, make sure no stack and no sampler is left running on the Pi.

## Report
Use the Report structure from `delegate-remote-dryrun-checks.md`, with "Key numbers" extended by:
- Time to "Managed nodes are active" (Foxglove off):
- Samples with under-voltage now (0x1): N of M (x %), during start-up / moves / idle:
- Supply verdict (replace before session: yes/no):

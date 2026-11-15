# Task: Mac analysis setup and docs for the Pi power finding

You are the executor for a task that has already been planned and decided. Your job is to carry out the steps below exactly, verify each one, and report back. You are not being asked to redesign anything.

## Goal
The robot's Raspberry Pi has a failing power supply. On 2026-11-10 `vcgencmd get_throttled` showed under-voltage *now* (bit 0x1) in 67.5 % of samples: 27 of 29 during Nav2 start-up, 21 of 21 during commands, and some at load 3.5. The CPU throttles, and Nav2 shut itself down even at idle with a 10 s `bond_timeout`. Until someone swaps the supply, the robot can't be used for the Nav2 experiments.

This task does the work that needs no robot:
1. Make the experiment analysis run on the Mac, so bags can be summarised and compared with `evo` there instead of on the overloaded Pi.
2. Record the power finding in the project docs, so the team fixes the supply before driving.

## Context
- Project: ROS 2 Jazzy delivery robot (Raspberry Pi 4B). Read `AGENTS.md` first (short); it is the rulebook.
- Working directory: `/Users/shermanwee/Documents/MA4890/delivery_bot` (Mac, macOS, **no ROS installed**). Do not SSH to the Pi in this task.
- **Precondition:** PR 40 (`docs/remote-dryrun-checks`) must be merged before you start, because both add a top block to `notes/notes.md`. Check with `gh pr view 40 --json state --jq .state`; it must print `MERGED`. If it doesn't, stop and report. Then `git switch main && git pull && git switch -c tools/mac-analysis`.
- Bag backup (copied from the Pi; read-only for you): `../delivery_bot_pi_backup/bags/`. Each bag is a directory with `metadata.yaml` and one `.mcap` file. Useful ones:
  - `2026-10-31_push_195343`: a 1 m hand push. rf2o read 0.962 m on 2026-10-31, so `/odom_rf2o` should show about 0.96 m forward.
  - `2026-11-09_E2_none_empty_run99`, `2026-11-09_E3_amcl_empty_run98`, `2026-11-09_E3_amcl_empty_run99`: short smoke recordings from `tools/run_cell.py`, robot mostly still.
- Key files:
  - `tools/analysis/bag_summary.py`. `read_bag(path)` (line ~49) imports `rosbag2_py`, `rclpy.serialization` and `rosidl_runtime_py` inside the function, which only exist on the Pi. `summarise(cmd, odom)` is pure maths and already tested in `tools/tests/test_bag_summary.py`. `ODOM_TOPICS` lists `/odom_rf2o` and `/odometry/filtered`.
  - `docs/run_order.md`: today's driven-session checklist. Sections `## 1. Before power-up`, `## 2. On the Pi`, ..., `## 7. Fallback if driving fails`.
  - `docs/CA3.md`: open-issues table with rows `| OI-9 |` (motor battery) and `| OI-10 |` (Nav2 shuts down under load), near line 64.
  - `docs/slam_build_path.md`: task tree.
  - `AGENTS.md`: the `| Motors |` row in "Current state".
  - `notes/notes.md`: lab notebook, append-only, newest block first.
- Conventions: tools keep ROS imports inside functions so modules import without ROS. Tests live in `tools/tests/`. Docs are edited in place; `notes/notes.md` only gets a new block at the top.

## Decisions already made (do not revisit)
- **Mac analysis runs in a virtualenv at the repo root, `.venv`** (already in `.gitignore`; confirm with `git check-ignore .venv`). Packages: `evo` (it pulls in `rosbags`, a pure-Python ROS bag reader that handles MCAP) and `pytest`. Use the Mac's `python3`.
- **`bag_summary.read_bag` gets a fallback, not a rewrite.** It tries `rosbag2_py` first, as now (the Pi). On `ImportError` it reads the same topics with `rosbags.highlevel.AnyReader`, deserialising with the reader's own typestore. It returns exactly the same `(cmd, odom)` structure, using the message receive time in seconds.
  - Rejected: replacing the Pi path. The Pi has `rosbag2_py` and no `rosbags`.
- **`evo` is used from the command line, not wrapped in code.** The pipeline:
  1. Export each odometry topic to TUM: `evo_traj bag2 <bag_dir> /odom_rf2o /odometry/filtered --save_as_tum`. Writes `odom_rf2o.tum`-style files in the current directory, so run it in a per-bag output folder.
  2. Pairwise APE between E3 loops with `evo_ape tum <a.tum> <b.tum> -a`.
  3. Write the commands into `docs/run_order.md`. No script.
- **The power finding becomes OI-11 in `docs/CA3.md`, and the root cause of OI-10.**
  - Fix: a proper 5.1 V 3 A Pi 4 supply (official USB-C or equivalent), not a power bank and not the motor pack.
  - Check: after a fresh boot, `vcgencmd get_throttled` must read `0x0`. With `navigation.launch.py bridge:=false` running, it must never show bit 0x1 or 0x4.
- **Driven-session rule while the supply is unchanged:** CP5 straights on `base.launch.py` only. No E2/E3/E1 runs under `navigation.launch.py`.

## Steps
Do these in order. Finish and verify each step before starting the next.

### Step 1: virtualenv and local tests
- Do: check the precondition and create the branch (Context). `git check-ignore .venv` must print `.venv`, otherwise stop. Then `python3 -m venv .venv && .venv/bin/pip install evo pytest`.
- Verify:
  - `.venv/bin/evo_traj --help` prints usage;
  - `.venv/bin/python -c "import rosbags; print(rosbags.__version__)"` prints a version;
  - `.venv/bin/python -m pytest tools/tests -q` passes.
  If an existing test fails before you change anything, stop and report it with its output.
- Done when: evo is installed and the existing tools tests pass on the Mac.

### Step 2: `rosbags` fallback in `bag_summary.read_bag`
- Do: in `tools/analysis/bag_summary.py`, change `read_bag(path)` to:
  1. Try the current `rosbag2_py` code.
  2. On `ImportError`, open the bag with `rosbags.highlevel.AnyReader([Path(path)])`. Iterate connections for `/cmd_vel` and the topics in `ODOM_TOPICS` that exist, deserialise with `reader.deserialize(rawdata, connection.msgtype)`, and fill `cmd` and `odom` exactly as the existing code does: `(t_seconds, v, w)` and `(t_seconds, x, y, yaw)`, the same yaw formula, timestamps as `timestamp * 1e-9`.
  3. Keep both imports inside the function.
  4. Update the module docstring: it reads with `rosbag2_py` on the Pi and with `rosbags` on the Mac (`.venv`).
- Do: in `tools/tests/test_bag_summary.py`, add one test that runs `read_bag` and `summarise` on `../delivery_bot_pi_backup/bags/2026-10-31_push_195343`, relative to the repo root (resolve it from the test file's location). Assert that `/odom_rf2o` forward displacement is between 0.85 and 1.10 m. Mark it `pytest.mark.skipif` when that directory is missing or `rosbags` is not importable, so CI (which has neither) skips it.
- Verify:
  - `.venv/bin/python -m pytest tools/tests/test_bag_summary.py -q -rs` passes, with the new test **run, not skipped**, on the Mac;
  - `.venv/bin/python tools/analysis/bag_summary.py ../delivery_bot_pi_backup/bags/2026-10-31_push_195343 ../delivery_bot_pi_backup/bags/2026-11-09_E2_none_empty_run99` prints two rows without a traceback.
- Done when: the push bag reads about 0.96 m on the Mac and the full tools suite still passes.
- Then commit: `tools: 2026-11-10 bag_summary reads bags on the Mac via rosbags`.

### Step 3: `evo` pipeline smoke test
- Do: in a scratch folder outside the repo (e.g. `mktemp -d`), run `/Users/shermanwee/Documents/MA4890/delivery_bot/.venv/bin/evo_traj bag2 <push bag dir> /odom_rf2o /odometry/filtered --save_as_tum`.
  - If `/odometry/filtered` is not in that bag, run with `/odom_rf2o` only and note it.
  - Then run `evo_ape tum <rf2o tum> <rf2o tum> -a` (the same file twice) to prove the APE command runs; it should report an APE of about 0.
- Verify: TUM files exist; `evo_ape` prints statistics without error. Record the exact commands that worked.
- Stop if `evo_traj bag2` cannot read the MCAP bags. Report the error; do not try other tools.
- Done when: you have a working export and APE command line.

### Step 4: docs
- Do:
  - (a) `docs/CA3.md`, open-issues table:
    - Add a row `| OI-11 |` after OI-10. Content: the Pi supply under-voltage (the numbers in Goal, dated 2026-11-10, "remote dry-run retry, test_log 2026-11-10"); the impact (CPU throttled, so slow start-up, the EKF misses its rate, `/scan` stalls, Nav2 heartbeat failures, likely the 2026-11-09 Pi reboots); the fix and check from Decisions.
    - In the OI-10 row, append: "Still failing with `bond_timeout` 10 s on 2026-11-10, including at idle; root cause OI-11 (Pi supply). Recheck after the supply swap."
  - (b) `AGENTS.md`, `| Motors |` row: in its **Open:** sentence, add "the Pi's own supply browns out (under-voltage in 67.5 % of samples, OI-11): replace it before Nav2 runs". Change nothing else in `AGENTS.md`.
  - (c) `docs/run_order.md`:
    - Under `## 1. Before power-up`, add first: "Pi on a proper 5.1 V 3 A supply (not a power bank, not the motor pack), OI-11."
    - Under `## 2. On the Pi`, add after the `get_throttled` line: "Start `ros2 launch delivery_bot_bringup navigation.launch.py bridge:=false` and watch `vcgencmd get_throttled` for 60 s: any 0x1 or 0x4 bit means stop and swap the supply. Until then only CP5 straights on `base.launch.py`."
    - Add a new final section `## 8. Analysis on the Mac` with the venv setup line, the `bag_summary.py` command via `.venv/bin/python`, and the working `evo_traj` / `evo_ape` commands from Step 3, each with one line on what it is for (E2 distance and heading; E3 pairwise APE between loops).
  - (d) `docs/slam_build_path.md`:
    - The line containing `Motor safety on \`feat/motors\` (R.1): PR 34 merged into \`feat/motors\`; **MT** to review and open the PR to \`main\``: replace its tail after `PR 34 merged into \`feat/motors\`` with `; on \`main\` via PR 37 (2026-11-09), \`feat/motors\` is stale`.
    - The R.1 line starting `- [~] Motors and rough gains on \`feat/motors\``: change `[~]` to `[x]` and append ` — on \`main\` via PR 37, then calibrated in PR 38`.
    - Under the 9.3 driven-session sub-list (the line with `Motor battery charged and its voltage checked`), add `    - [ ] Pi supply replaced and checked: \`get_throttled\` 0x0 after boot, no 0x1 under \`navigation.launch.py\` (OI-11)`.
    - Also add under 9.8 (the metrics line) a sub-item `  - [x] Mac analysis: \`.venv\` with evo, \`bag_summary.py\` reads bags via rosbags (docs/run_order.md §8)`.
    - If any of these exact lines is not found, stop and report rather than guessing.
  - (e) `notes/notes.md`: new top block above the current first `## ` heading: `## 2026-11-10 (Mac) · Mac analysis setup, Pi supply recorded as OI-11`, 3-5 lines (what was set up; OI-11 and its check; driven-session rule while unchanged), then `---`.
- Verify: `git diff --stat` lists only `docs/CA3.md`, `AGENTS.md`, `docs/run_order.md`, `docs/slam_build_path.md`, `notes/notes.md` (plus the Step 2 files, already committed).
- Done when: all five docs updated.
- Then commit: `docs: 2026-11-10 OI-11 Pi supply under-voltage, run order power check, Mac analysis`.

### Step 5: PR
- Do: push and open a PR to `main` with `gh pr create`:
  - Title `tools: 2026-11-10 Mac analysis (rosbags, evo) and OI-11 Pi supply`.
  - Body follows `.github/pull_request_template.md`, with the pytest output (new test run, not skipped) and the push-bag result (forward metres) under "How it was checked".
  - Ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
  - Wait for `gh pr checks <n> --watch`. Do not merge.
- Verify: all checks pass; `.venv` is not in `git ls-files`.
- Done when: the PR is open and green.

## Out of scope
- Do not change:
  - any ROS package (`delivery_bot_*/`), launch file or YAML;
  - `tools/run_cell.py`, `tools/timed_move.py`, `tools/motor_check.py`;
  - `.github/`;
  - `evidence/`;
  - the backup folder `../delivery_bot_pi_backup/` (read only).
- Do not:
  - SSH to the Pi;
  - add `evo` or `rosbags` to any package manifest;
  - write analysis scripts beyond the `read_bag` fallback;
  - commit `.venv`, the `delegate-*.md` files, `reports/` or `research_notes/`;
  - merge the PR.

## How to work
- Follow the steps as written. Do not add features, refactor unrelated code, rename things, or change dependencies unless a step says to.
- Read the files a step names before editing them. Don't explore the whole repo; look only where a step needs you to.
- If a step's instructions don't match what you find (a file or function doesn't exist, the code is structured differently, a command fails for a reason unrelated to your change), **stop**. Do not improvise a workaround. Go straight to the report and describe what you found.
- If a verification fails because of your own change, you may fix it within that step's scope (up to 2 attempts). If it still fails, stop and report.
- Trivial things a step obviously needs (an import, a missing type annotation, a typo in the instructions) you may handle; list each one under Deviations in the report.
- Commit at the points marked "Then commit", staging only the files the step names (`git add <paths>`, never `git add -A`), with the trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Report
When finished (or when you stop), reply with exactly this structure:

```
## Delegate report: Mac analysis setup and OI-11

### Status
<COMPLETE | STOPPED at step N | PARTIAL>

### Steps
- [x] Step 1: <title> — <one line on what was done>
- [ ] Step N: <title> — <why not done>

### Verification results
<each verify command you ran and its result (pass/fail, key output lines)>

### Key numbers
- Push bag /odom_rf2o forward (Mac read):
- evo commands that worked (exact):

### Files changed
- `<path>` — <what changed>

### Deviations
<anything you did that the steps didn't literally say, and why; "None" if none>

### Problems / open questions
<what blocked you, what you found that contradicts the plan, what the planner needs to decide; "None" if none>

### PR
<URL and CI status>
```

# Task tree

**The one place for open work.** Every task, checkpoint and measured finding of the
project lives here. Other files hold the detail, and each task links to it:
how-to in [`docs/slam_build_path.md`](docs/slam_build_path.md), experiment design in
[`docs/report_plan.md`](docs/report_plan.md), numbers in [`docs/test_log.md`](docs/test_log.md),
open issues in [`docs/CA3.md`](docs/CA3.md), the story in [`notes/notes.md`](notes/notes.md).
Edit in place: tick a box when it is done, with the date. Add new tasks here, not in those files.

Legend: `[x]` done · `[ ]` open · `[~]` in progress or in an open PR · **owner** in bold ·
→ link to the detail. Owners: **S** Sherman, **MT** motor teammate (Chloe), **A**, **B**
(placeholders until named).

**Pointers.** Every checkpoint and finding names where its proof lives:
- **Log** = a row in [`docs/test_log.md`](docs/test_log.md), cited as *date · first words of
  the Test column* (search for them), and the matching block in
  [`notes/notes.md`](notes/notes.md), cited as *date · block title*.
- **Evidence** = a file in [`evidence/`](evidence/) or [`results/`](results/) (raw artefacts,
  append-only), or a bag on the Pi (`~/bags/<name>`, backed up by hand to
  `../delivery_bot_pi_backup/`).
A finding with no log row is not a finding yet. When you tick a task, add its pointer.

Last compiled: 2026-11-09.

## 1. Checkpoints

A checkpoint is a state the project can be in, checked by one observable test.

| # | Checkpoint | Done when | Target | State | Evidence · log |
| --- | --- | --- | --- | --- | --- |
| CP0 | Platform up | `/scan`, `/imu/data` and TF stream on the Pi; robot built and measured into the URDF | 2026-10-31 | **done** 2026-10-31 | [`evidence/lidar/2026-10-21_composite_20revs.png`](evidence/lidar/2026-10-21_composite_20revs.png) · test_log 2026-10-30 "IMU at rest" · notes 2026-10-31 "robot built: mounting, rf2o hand tests, variances, first room map" |
| CP1 | Map and localisation | Room map saved; `slam_toolbox` localisation recovers a 30 cm / 20° wrong start | 2026-11-01 | **done** 2026-11-01 | [`results/maps/2026-10-31_room2.png`](results/maps/2026-10-31_room2.png), [`results/maps/2026-11-01_room2_home_pose.png`](results/maps/2026-11-01_room2_home_pose.png) · test_log 2026-11-01 "6.4 wrong start, 30 cm / 20 deg" · notes 2026-11-01 "base/mapping/localisation launch files, 6.2 localisation on the room graph" |
| CP2 | OI-8 explained | Cause of rf2o reading 24 % of a push found by a live test | 2026-11-03 | **done** 2026-11-03 (a person behind the robot) | [`evidence/lidar/2026-11-03_oi8_live_push.txt`](evidence/lidar/2026-11-03_oi8_live_push.txt), [`evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`](evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt) · test_log 2026-11-03 "OI-8 live push A", "OI-8 bad bags of 2026-11-01 re-read" · notes 2026-11-03 "OI-8: live push, nobody in the scan" |
| CP3 | Plan G agreed | Method × condition matrix in `docs/report_plan.md`, outlines rewritten | 2026-11-09 | [~] PR 31 open | PR 31 · notes 2026-11-09 "CA3 plan widened to a method × condition matrix" |
| CP4 | Offline matrix on existing bags | 216 replay runs with both TUM files; two CSVs in `results/matrix/` | 2026-11-10 | [ ] → `delegate-replay-matrix.md` | will be `results/matrix/2026-11-09_e2_e5_*.csv`, `evidence/lidar/<date>_matrix_runs.txt` |
| CP5 | Robot drives | Wheels raised, then a 1 m straight on the floor with the switch in reach | 2026-11-10 | [ ] motors on `feat/motors`, not merged; review findings in §5.1 | needs a test_log row (none on `feat/motors`) |
| CP6 | Driven data recorded | Driven straights/spins, 3 checkpoint loops, wrong starts, people loop, E1 runs, all bagged | 2026-11-10 | [ ] | will be `~/bags/2026-11-10_<exp>_run<N>`, one test_log row per run |
| CP7 | Results and slides | Every RQ has a figure and an Our take; no `[if ...]` text left on slides; rehearsal 1 done | 2026-11-11 | [ ] | `report/figures/`, `report/slides_outline.md` |
| CP8 | Presentation | Delivered | Thu 2026-11-12 | [ ] | — |
| CP9 | Report submitted | Report, slides, peer assessment in | end of Week 13 | [ ] | — |

## 2. CA3 deliverables

### 2.1 Presentation (Thu 2026-11-12) → [`report/slides_outline.md`](report/slides_outline.md)
- [ ] Slide skeleton on the storyline (15 slides) — **all**
- [ ] Product table, slides 2–3 — **A**
- [ ] System and demo slides 4–5 — **MT**
- [ ] Matrix and RQ1–RQ3 slides 6–9 — **S** (needs CP4, CP6)
- [ ] OI-8, people, hazards, position slides 10–13 — **B**
- [ ] Roadmap and verdict slides 14–15 — **A**
- [ ] Video clips ≤ 120 s, offline copies on two USB sticks (V1–V4) — **MT**, **B**
- [ ] Q&A answers (10 questions) drafted and drilled — **all**
- [ ] Rehearsal 1 (Wed 11), rehearsal 2 (Wed 11 evening or Thu morning), timed per presenter — **all**
- [ ] Confirm date and slot on NTULearn — **S**

### 2.2 Report (end of Week 13) → [`report/CA3_report.md`](report/CA3_report.md)
- [ ] Download the NTULearn template — **A**
- [ ] §1 Introduction and contribution table — **A**
- [ ] §2 Background, product table, published baselines — **S** (2.1–2.4), **A**/**B** (2.5–2.6)
- [ ] §3 System — **S**, **MT**
- [ ] §4 Method and "differences from the paper" table — **S**, **B**
- [ ] §5 Results, every number with provenance and command — **S**, **B**, **MT**
- [ ] §6 Discussion, one Our take per RQ — owners per RQ
- [ ] §7 Our position, §8 conclusions and costed roadmap — **all**, **A** drafts
- [ ] References checked against [`report/literature_notes.md`](report/literature_notes.md) — **A**
- [ ] Final title chosen after E2, E3, E5 — **all**
- [ ] Peer assessment submitted — **each member**

## 3. Experiments (the matrix) → [`docs/report_plan.md`](docs/report_plan.md) §3–4

### 3.1 Offline, on existing bags (CP4) — **S**
- [ ] Replay harness: EKF variants, `ekf:=false`, `scan_degrade.py`, `matrix_run.sh`, `matrix_an.py` → `delegate-replay-matrix.md` steps 0–4
- [ ] E2 odometry: 4 configs × 6 bags × 3 replays (72 runs)
- [ ] E5 lidar degradation: 2 configs × 3 bags × 8 levels × 3 replays (144 runs)
- [ ] E4 offline: person-behind vs nobody bags through E2's configs (comes out of the E2 run)
- [ ] Results CSVs, evidence log, test_log rows, notes block, PR

### 3.2 Driven session, Tue 2026-11-10 (CP5, CP6) — **MT** drives, **S** records, **B** people
- [ ] Charged battery, `vcgencmd get_throttled` = `0x0`
- [ ] Wheels raised, then one 1 m straight with the switch in reach
- [ ] Tape the checkpoints (home + seats) and measure them → build path 9.1
- [ ] E2: driven 1 m straights ×3 and 360° spins ×3, timed `cmd_vel`, nobody nearby
- [ ] E3: checkpoint loop ×3 (Nav2 waypoints or teleop); wrong starts at 10/20/30/40 cm and 10/20/30/40°, recovered by a short drive
- [ ] E4: the loop with 1–2 people walking; one person stepping in front (stop distance, contacts)
- [ ] E1: home → seat → home runs (arrival error labelled "rough gains")
- [ ] Video clips V1–V4 during the runs
- [ ] Fallback if driving fails: the same runs hand-pushed with a stick, nobody behind the robot

### 3.3 Offline, on the driven bags (after CP6) — **S**
- [ ] Phase 2: AMCL offline config; replay `slam_toolbox` localisation and AMCL on the same loop bags (E3)
- [ ] Phase 3: E2 and E5 on the driven bags; compare driven only with driven (motor vibration)
- [ ] `evo` installed somewhere (Mac Docker or Pi) for ATE/RPE → build path 9.3
- [ ] Figures with commit and bag in each caption; one Our take per RQ

### 3.4 Safety — **B**
- [ ] Hazard table, 6–8 rows: hazard, mitigation, test, pass/fail
- [ ] Stop wedge vs a person stepping in at walking pace → [`reports/MPC planners for dynamic humans.md`](reports/MPC%20planners%20for%20dynamic%20humans.md) (untracked, commit it)

## 4. SLAM build path (learning track) → [`docs/slam_build_path.md`](docs/slam_build_path.md)

Ticks here are the record; the build path holds the how-to. `⇢ E2` marks a task the
experiments also need.

- **Stage 0 Foundations:** [x] 0.1 ROS 2 picture · [ ] 0.2 frames and transforms · [x] 0.3 what SLAM is
- **Stage 1 Sensor:** [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 1.4 · [x] 1.5
- **Stage 2 Frames:** [x] 2.1 measure · [x] 2.2 URDF
- **Stage 3 rf2o:** [ ] 3.1 how rf2o works · [x] 3.2 push by hand · [ ] 3.3 break it on purpose (OI-8 covered the "person in the scan" case) · [x] 3.4 startup race
- **Stage 4 EKF:** [ ] 4.1 Kalman intuition · [ ] 4.2 zero-covariance bug · [x] 4.3 covariance relay · [x] 4.4 variances · [ ] 4.5 show that fusion helps ⇢ E2
- **Stage 5 Mapping:** [ ] 5.1 pose graphs · [ ] 5.2 lifecycle nodes · [x] 5.3 mapping.launch.py · [ ] 5.4 map the room (second tape gap left) · [x] 5.5 tune and freeze
- **Stage 6 Localisation:** [ ] 6.1 mapping vs localisation · [x] 6.2 · [x] 6.3 · [x] 6.4 wrong start ⇢ E3
- **Stage 7 Foxglove:** [x] 7.1 trajectory recorder · [ ] 7.2 layout (navigation layout merged in PR 27; SLAM layout to confirm) · [ ] 7.3 control SLAM from Foxglove (buttons run; owner steps left, §5)
- **Stage 8 Autonomous mapping:** [ ] 8.1 frontier theory · [x] 8.2 build explore_lite · [~] 8.3 explore.launch.py (PR 30) · [ ] 8.4 first supervised run (needs motors) · [ ] 8.5 compare with manual mapping
- **Stage 9 Evaluation:** [ ] 9.1 checkpoints ⇢ E3 · [ ] 9.2 evaluation runs ⇢ CP6 · [ ] 9.3 metrics script ⇢ 3.1, 3.3 · [ ] 9.4 IMU ablation ⇢ E2 · [ ] 9.5 Pi load · [ ] 9.6 SLAM section ⇢ report §5 · [ ] 9.7 people, driven ⇢ E4
- **Stage X Extensions:** [ ] X.1 deskew · [ ] X.2 people filtering · [ ] X.3 map quality without truth (future work in the report)

## 5. Robot, integration and housekeeping

### 5.1 Motors and navigation — **MT** unless marked
- [~] Motors and rough gains on `feat/motors` (3d295f7, 3fed2ff); open a PR to `main`. Review of 2026-11-09 (not yet sent to MT):
  - [ ] Dry run removed: `base.launch.py` always starts `motor_node` live, so the mapping, localisation and navigation stacks, the Foxglove stack buttons and PR 30's explore all drive the wheels whenever anything publishes `/cmd_vel`. Restore `dry_run` (default `true`) in the node; the test `test_base_declares_dry_run_true_by_default` was edited to expect `false` and should go back
  - [ ] No lidar stop (`stop_dist_m`): only the 0.5 s watchdog and Nav2's collision monitor; teleop has no obstacle stop (AGENTS rule 1)
  - [ ] `motor_node` subscribes `TwistStamped` only; `nav2_params.yaml` sets no `enable_stamped_cmd_vel`. Check `ros2 topic info /cmd_vel -v` shows one type with Nav2 up, or Nav2 and the motors will not talk
  - [ ] No tests for `_duty_for` and the wheel split (definition of done); no test_log row for the first drive
  - [ ] Gains left 3.0 vs right 1.0 ("rough"): label E1 arrival error accordingly; calibrate with a 1 m straight
- [~] Nav2 glue: navigation button, `save_goal`, `deliver`, planner check (PR 29); live test of `save_goal` and `deliver` still to do
- [~] `explore.launch.py` (PR 30) — **S**
- [ ] Calibration: dead zone, per-side gain, 1 m straight
- [ ] Save seat goals with `save_goal` once driving works

### 5.2 Foxglove and Pi — **S**
- [ ] Owner steps in the README: sudoers rule, linger, systemd unit (power buttons need the sudoers rule)
- [ ] `/imu_node/recalibrate` with the robot nudged; `/stack/localisation` live
- [ ] Confirm cockpit tiles change after re-importing `docs/foxglove/cockpit_layout.json`
- [ ] EKF late-update count at 20 Hz on a quiet Pi (camera off), against closure 0.115 m vs 0.109 m

### 5.3 Repo
- [~] Merge PR 31 (this plan) — **S**
- [ ] Commit or delete the untracked files in the Mac checkout: `delegate-navigation-phase1.md`, `delegate-oi8-live-push.md` (both done), `delegate-replay-matrix.md`, `reports/`, `research_notes/`
- [ ] Two sessions share the Mac checkout and switch its branches: use a worktree per session
- [ ] Back up `~/bags` and `~/maps` to `../delivery_bot_pi_backup/` after the driven session

### 5.4 Open issues → [`docs/CA3.md`](docs/CA3.md)
- [ ] OI-1 old `robot` box offline: confirm retired
- [ ] OI-2 `raspberrypi` key rejected: same machine reflashed?
- [ ] OI-4 echo rate 26–29 % unexplained (mitigated); optional echo-by-material test, first to drop
- [ ] OI-6 lidar start hang: wait 20 s after a stop; no fix
- [ ] OI-7 repo public: decide
- [ ] OI-8 row in `docs/CA3.md` still describes the open state: mark closed 2026-11-03

## 6. Findings (measured)

Only measured results, each with its date and source. Hypotheses live in
[`docs/report_plan.md`](docs/report_plan.md) §7 until an experiment confirms or kills them.

| Date | Finding | Number | Evidence · log | Feeds |
| --- | --- | --- | --- | --- | 
| 2026-10-21 | Lidar rate and echo rate | A1M8 7.05 Hz; 26–29 % of pings return nothing; gaps follow the room, not the lidar | [`evidence/lidar/2026-10-21_composite_20revs.png`](evidence/lidar/2026-10-21_composite_20revs.png), [`evidence/lidar/2026-10-21_scan_run1.png`](evidence/lidar/2026-10-21_scan_run1.png) · OI-4 in `docs/CA3.md` · notes 2026-10-20/21 "P1 lidar bring-up on the old Pi", 2026-10-30 "3.4 startup race, near-return ring is the room" | Report §5.1, RQ1 context |
| 2026-10-30 | IMU at rest | 100 Hz, gyro z std 0.00175 rad/s | test_log 2026-10-30 "IMU at rest" | §5.1 |
| 2026-10-31 | Gyro on a hand-turned full turn | 360.2° for 360° | `~/bags/2026-10-31_turn_194945` · test_log 2026-10-31 "3.2 spin only" | RQ2 |
| 2026-10-31 | rf2o by hand, nobody behind | turn 352.9° (−2 %); 1 m push 0.962 m (−3.8 %, window 39–50 s) | `~/bags/2026-10-31_turn_194945`, `~/bags/2026-10-31_push_195343` · test_log 2026-10-31 "3.2 spin only", "3.2 forward move"; 2026-11-02 "live push on the good bag by window" | RQ2 baseline |
| 2026-10-31 | Variances fitted | rf2o vx var 1.1e-5 / 4.7e-6, wz var 8.5e-4 / 1.8e-3, gyro var 1.7e-6 (rest) | test_log 2026-10-31 "4.4 variances" | EKF config, §4 |
| 2026-10-31 | First room map; mapping config frozen after the 5.5 sweep | map + `slam_mapping.yaml` | [`results/maps/2026-10-31_room2.png`](results/maps/2026-10-31_room2.png) · test_log 2026-10-31 "5.4 room map", "5.5 sweep" · notes 2026-10-31 "5.5 sweep done, config frozen, camera stream started" | §5.3 |
| 2026-10-31 | Camera stream and its cost | 1280x720 at 10 fps; EKF misses 20 Hz with the camera on | [`results/2026-11-02_av_stream_frame.jpg`](results/2026-11-02_av_stream_frame.jpg) · test_log 2026-10-31 "Camera quality", "Camera under SLAM load"; 2026-11-01 "EKF 20 Hz check" · notes 2026-10-31 (night) "camera quality raised" | Ops rule: camera off while mapping |
| 2026-11-01 | Wrong-start basin, `slam_toolbox` localisation | 30 cm / 20° recovers after a push; 31° does not (one case per angle) | [`results/maps/2026-11-01_room2_home_pose.png`](results/maps/2026-11-01_room2_home_pose.png) · test_log 2026-11-01 "6.4 wrong start, 30 cm / 20 deg", "6.4 wrong start, 30 cm / 31 deg" | RQ3 baseline |
| 2026-11-01 | Lidar start hang | `RPLIDAR running` with no S/N, several retries | OI-6 · `docs/system/06_troubleshooting.md` · test_log 2026-11-01 "6.4 wrong start, 30 cm / 31 deg" (first start hung) | Hazard table, Ops |
| 2026-11-02 | Pi under-voltage | `throttled=0x50005` on 2026-11-02 and 2026-11-03 | test_log 2026-11-02 "replay, control" · notes 2026-11-02 "OI-8: offline rig fixed, format still undecided; Pi is under-voltage" | Protocol: charged battery |
| 2026-11-03 | Replay is not repeatable | 3 replays of one bag: 0.679 / 0.592 / 0.531 m (~12 %); good-bag replay 71 % of live | test_log 2026-11-02 "replay, control"; 2026-11-03 "replay repeatability, good bag" · notes 2026-11-03 "OI-8: replay repeatability and rate" | ≥ 3 replays per cell |
| 2026-11-03 | **OI-8: a person behind the robot** | rf2o read 0.242 of 0.862 m and 0.307 of 1.222 m (25–28 %); nobody in the scan reads correctly; scan format cleared | [`evidence/lidar/2026-11-03_oi8_live_push.txt`](evidence/lidar/2026-11-03_oi8_live_push.txt), [`evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`](evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt), `~/bags/2026-11-01_push_225752`, `_230535`, `2026-11-03_*_push_ac*` · test_log 2026-11-03 "OI-8 live push A/B", "OI-8 bad bags of 2026-11-01 re-read" · notes 2026-11-03 "OI-8: live push, nobody in the scan" | RQ4, signature slide |
| 2026-11-08 | Nav2 planner on the room map (PR 29, unmerged) | 5/5 reachable goals planned, 1.18–2.70 m, 1–5 ms | `results/maps/2026-11-08_planner_paths.png` (on PR 29) · PR 29 test_log row | E1, system slide |

## 7. Open decisions

- [ ] Fifth member? Rebalance presenter timing if so — **all**
- [ ] OI-7: keep the repo public? — **S**
- [ ] AI-use declaration, if the module requires one — **all**

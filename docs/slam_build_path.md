# Task tree and SLAM build path

**The one document for the project's work**: checkpoints, every open task (SLAM, experiments,
robot, report), measured findings, and the step-by-step how-to for each SLAM task. Tick a
box when it is done, with the date and a pointer to its proof. Add new tasks here.

Each SLAM task below has: why it matters, what to do, how you know it's done, and an
**explain it back** question (answers go in `docs/slam_journal.md` under the task's ID;
optional since 2026-10-30).

Related: [report_plan.md](report_plan.md) (CA3 experiment design) · [slam.md](slam.md) (architecture, fixes, references) · [plan.md](plan.md) (project phases) · [test_log.md](test_log.md) (numbers) · [CA3.md](CA3.md) (decisions, open issues).

**Pointers.** Every checkpoint and finding names where its proof lives:
- **Log** = a row in [`docs/test_log.md`](test_log.md), cited as *date · first words of
  the Test column* (search for them), and the matching block in
  [`notes/notes.md`](../notes/notes.md), cited as *date · block title*.
- **Evidence** = a file in [`evidence/`](../evidence/) or [`results/`](../results/) (raw artefacts,
  append-only), or a bag on the Pi (`~/bags/<name>`, backed up by hand to
  `../delivery_bot_pi_backup/`).
A finding with no log row is not a finding yet. When you tick a task, add its pointer.

Legend: `[x]` done · `[ ]` open · `[~]` in progress or in an open PR · **owner** in bold. Owners: **S** Sherman, **MT** motor teammate (Chloe), **A**, **B** (placeholders until named). `⇢ E2` marks a learning task an experiment also needs.

Last compiled: 2026-11-09.

## Checkpoints

A checkpoint is a state the project can be in, checked by one observable test.

| # | Checkpoint | Done when | Target | State | Evidence · log |
| --- | --- | --- | --- | --- | --- |
| CP0 | Platform up | `/scan`, `/imu/data` and TF stream on the Pi; robot built and measured into the URDF | 2026-10-31 | **done** 2026-10-31 | [`evidence/lidar/2026-10-21_composite_20revs.png`](../evidence/lidar/2026-10-21_composite_20revs.png) · test_log 2026-10-30 "IMU at rest" · notes 2026-10-31 "robot built: mounting, rf2o hand tests, variances, first room map" |
| CP1 | Map and localisation | Room map saved; `slam_toolbox` localisation recovers a 30 cm / 20° wrong start | 2026-11-01 | **done** 2026-11-01 | [`results/maps/2026-10-31_room2.png`](../results/maps/2026-10-31_room2.png), [`results/maps/2026-11-01_room2_home_pose.png`](../results/maps/2026-11-01_room2_home_pose.png) · test_log 2026-11-01 "6.4 wrong start, 30 cm / 20 deg" · notes 2026-11-01 "base/mapping/localisation launch files, 6.2 localisation on the room graph" |
| CP2 | OI-8 explained | Cause of rf2o reading 24 % of a push found by a live test | 2026-11-03 | **done** 2026-11-03 (a person behind the robot) | [`evidence/lidar/2026-11-03_oi8_live_push.txt`](../evidence/lidar/2026-11-03_oi8_live_push.txt), [`evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`](../evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt) · test_log 2026-11-03 "OI-8 live push A", "OI-8 bad bags of 2026-11-01 re-read" · notes 2026-11-03 "OI-8: live push, nobody in the scan" |
| CP3 | Plan H agreed | People as the axis, every method live, empty vs people, in `docs/report_plan.md`; outlines rewritten | 2026-11-09 | [~] PR 31 open | PR 31 · notes 2026-11-09 "CA3 plan widened to a method × condition matrix" (evening addendum) |
| CP4 | Ready to drive the matrix | Motor safety fixed and merged; live switches (`ekf_params_file`, `ekf:=false`, `localizer:=amcl`) and the run sheet tested; checkpoints and people paths taped | 2026-11-09 | [ ] | test_log rows for each switch; Progress 9.2 |
| CP5 | Robot drives | Wheels raised, then a 1 m straight on the floor with the switch in reach | 2026-11-10 | [ ] motors on `feat/motors`, not merged; review findings in §5.1 | needs a test_log row (none on `feat/motors`) |
| CP6 | Driven data recorded | E2 48 runs, E3 12 loops + 16 wrong starts, E4 step-ins, E1 5 runs, all live and bagged, tape numbers written down | 2026-11-10 | [ ] | will be `~/bags/2026-11-10_<exp>_<cell>_run<N>`, one test_log row per run |
| CP7 | Results and slides | Every RQ has a figure and an Our take; no `[if ...]` text left on slides; rehearsal 1 done | 2026-11-11 | [ ] | `report/figures/`, `report/slides_outline.md` |
| CP8 | Presentation | Delivered | Thu 2026-11-12 | [ ] | — |
| CP9 | Report submitted | Report, slides, peer assessment in | end of Week 13 | [ ] | — |

## Progress

Every open task of the project, in one list. Stages 0–9 are the SLAM build path and the experiments (how-to below); D and R are the rest of the project.

- **Stage 0 Foundations:** [x] 0.1 ROS 2 picture · [ ] 0.2 frames and transforms · [x] 0.3 what SLAM is
- **Stage 1 Sensor:** [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 1.4 · [x] 1.5
- **Stage 2 Frames:** [x] 2.1 measure · [x] 2.2 URDF
- **Stage 3 rf2o:** [ ] 3.1 how rf2o works · [x] 3.2 push by hand · [ ] 3.3 break it on purpose (OI-8 covered the "person in the scan" case) · [x] 3.4 startup race
- **Stage 4 EKF:** [ ] 4.1 Kalman intuition · [ ] 4.2 zero-covariance bug · [x] 4.3 covariance relay · [x] 4.4 variances · [ ] 4.5 show that fusion helps ⇢ E2
- **Stage 5 Mapping:** [ ] 5.1 pose graphs · [ ] 5.2 lifecycle nodes · [x] 5.3 mapping.launch.py · [ ] 5.4 map the room (second tape gap left) · [x] 5.5 tune and freeze
- **Stage 6 Localisation:** [ ] 6.1 mapping vs localisation · [x] 6.2 · [x] 6.3 · [x] 6.4 wrong start ⇢ E3
- **Stage 7 Foxglove:** [x] 7.1 trajectory recorder · [ ] 7.2 layout (navigation layout merged in PR 27; SLAM layout to confirm) · [ ] 7.3 control SLAM from Foxglove (buttons run; owner steps left, §5)
- **Stage 8 Autonomous mapping:** [ ] 8.1 frontier theory · [x] 8.2 build explore_lite · [~] 8.3 explore.launch.py (PR 30) · [ ] 8.4 first supervised run (needs motors) · [ ] 8.5 compare with manual mapping
- **Stage 9 Experiments (plan H)** — the how-to is Stage 9 below; design in [`report_plan.md`](report_plan.md) §3–4
  - [ ] 9.1 Survey floor checkpoints and tape the two people paths — **S**, **B**
  - [ ] 9.2 Live switches and run sheet (CP4) — **S** → `delegate-live-switches.md` (worker running 2026-11-09)
    - [ ] EKF variants (`ekf_variants/`), `ekf_params_file`, `ekf:=false` in `base.launch.py`
    - [ ] `localizer:=slam|amcl` in `navigation.launch.py` (AMCL + `map_server`, `amcl.yaml`)
    - [ ] `tools/timed_move.py` (publishes on `cmd_vel_smoothed`, through the collision monitor)
    - [ ] `tools/run_cell.py` (starts a cell, records the bag, prints the test_log row)
    - [ ] Motor safety on `feat/motors` (R.1) — **MT** review → `delegate-motor-safety.md`
  - [ ] 9.3 Driven session, Tue 2026-11-10 (CP5, CP6) — **MT** drives, **S** runs the sheet, **B** people
    - [ ] Charged battery and a spare, `vcgencmd get_throttled` = `0x0`; robot still for 3 s at every start (IMU calibration)
    - [ ] Wheels raised, then one 1 m straight with the switch in reach (CP5)
    - [ ] Freeze config; record the commit
    - [ ] 9.4 runs (48), 9.5 loops (12) and wrong starts (16), 9.7 step-ins (3–5), E1 delivery runs (5)
    - [ ] On every run: failure onset (drift, jump, lost), recovery after people leave, failure position
    - [ ] Video clips V1–V4
    - [ ] Fallback if driving fails: stick-pushing for 9.4 (nobody behind the robot except in people runs); 9.5 and E1 partial
  - [ ] 9.4 Odometry configs, empty vs people (E2, RQ2) ⇢ 4.5
  - [ ] 9.5 Localiser: `slam_toolbox` vs AMCL (E3, RQ3) ⇢ 6.4
  - [ ] 9.6 What people do (RQ1): empty-vs-people table and room figure
  - [ ] 9.7 Step-in safety (E4, RQ4) — **B**
  - [ ] 9.8 Metrics: tape tables, `evo` on the bags, figures, one Our take per RQ
  - [ ] 9.9 Measure the Pi's load (full stack, Nav2 included)
  - [ ] 9.10 Write the SLAM section ⇢ report §5
  - [ ] Back up the bags to `../delivery_bot_pi_backup/`
  - Dropped to future work: lidar degradation (simulated, expensive, tied to nothing we discovered); the offline replay matrix on the 10-31 to 11-03 bags (`delegate-replay-matrix.md`, shelved)
- **Stage X Extensions:** [ ] X.1 deskew · [ ] X.2 people filtering · [ ] X.3 map quality without truth (future work in the report)

### D. CA3 deliverables

#### D.1 Presentation (Thu 2026-11-12) → [`report/slides_outline.md`](../report/slides_outline.md)
- [ ] Slide skeleton on the storyline (15 slides) — **all**
- [ ] Product table, slides 2–3 — **A**
- [ ] System and demo slides 4–5 — **MT**
- [ ] OI-8, design, RQ1–RQ3 slides 6–10 — **S** (needs CP6)
- [ ] Step-in, hazards, position slides 11–13 — **B**
- [ ] Roadmap and verdict slides 14–15 — **A**
- [ ] Video clips ≤ 120 s, offline copies on two USB sticks (V1–V4) — **MT**, **B**
- [ ] Q&A answers (10 questions) drafted and drilled — **all**
- [ ] Rehearsal 1 (Wed 11), rehearsal 2 (Wed 11 evening or Thu morning), timed per presenter — **all**
- [ ] Confirm date and slot on NTULearn — **S**

#### D.2 Report (end of Week 13) → [`report/CA3_report.md`](../report/CA3_report.md)
- [ ] Download the NTULearn template — **A**
- [ ] §1 Introduction and contribution table — **A**
- [ ] §2 Background, product table, published baselines — **S** (2.1–2.4), **A**/**B** (2.5–2.6)
- [ ] §3 System — **S**, **MT**
- [ ] §4 Method and "differences from the paper" table — **S**, **B**
- [ ] §5 Results, every number with provenance and command — **S**, **B**, **MT**
- [ ] §6 Discussion, one Our take per RQ — owners per RQ
- [ ] §7 Our position, §8 conclusions and costed roadmap — **all**, **A** drafts
- [ ] References checked against [`report/literature_notes.md`](../report/literature_notes.md) — **A**
- [ ] Final title chosen after E2, E3 — **all**
- [ ] Peer assessment submitted — **each member**

### R. Robot, integration and housekeeping

#### R.1 Motors and navigation — **MT** unless marked
- [~] Motors and rough gains on `feat/motors` (3d295f7, 3fed2ff); open a PR to `main`. Review of 2026-11-09 (not yet sent to MT):
  - [ ] Fixes for the items below are a worker prompt, `delegate-motor-safety.md` (PR into `feat/motors` for MT to review)
  - [ ] Dry run removed: `base.launch.py` always starts `motor_node` live, so the mapping, localisation and navigation stacks, the Foxglove stack buttons and PR 30's explore all drive the wheels whenever anything publishes `/cmd_vel`. Restore `dry_run` (default `true`) in the node; the test `test_base_declares_dry_run_true_by_default` was edited to expect `false` and should go back
  - [ ] No lidar stop (`stop_dist_m`): only the 0.5 s watchdog and Nav2's collision monitor; teleop has no obstacle stop (AGENTS rule 1)
  - [~] `/cmd_vel` type: Nav2 Jazzy defaulted to plain `Twist`, `motor_node` takes `TwistStamped` only. Fixed in PR 32 (`enable_stamped_cmd_vel: true` on 5 Nav2 nodes), checked on the Pi 2026-11-09: all `/cmd_vel*` endpoints TwistStamped · test_log 2026-11-09 "Nav2 `/cmd_vel` message type" · notes 2026-11-09 "Nav2 now publishes TwistStamped". Merge PR 32
  - [ ] No tests for `_duty_for` and the wheel split (definition of done); no test_log row for the first drive
  - [ ] Gains left 3.0 vs right 1.0 ("rough"): label E1 arrival error accordingly; calibrate with a 1 m straight
- [~] Nav2 glue: navigation button, `save_goal`, `deliver`, planner check (PR 29); live test of `save_goal` and `deliver` still to do
- [~] `explore.launch.py` (PR 30) — **S**
- [ ] Calibration: dead zone, per-side gain, 1 m straight
- [ ] Save seat goals with `save_goal` once driving works

#### R.2 Foxglove and Pi — **S**
- [ ] Owner steps in the README: sudoers rule, linger, systemd unit (power buttons need the sudoers rule)
- [ ] `/imu_node/recalibrate` with the robot nudged; `/stack/localisation` live
- [ ] Confirm cockpit tiles change after re-importing `docs/foxglove/cockpit_layout.json`
- [ ] EKF late-update count at 20 Hz on a quiet Pi (camera off), against closure 0.115 m vs 0.109 m

#### R.3 Repo
- [~] Merge PR 31 (this plan) — **S**
- [ ] Commit or delete the untracked files in the Mac checkout: `delegate-navigation-phase1.md`, `delegate-oi8-live-push.md` (both done), `delegate-replay-matrix.md` (shelved by plan H), `reports/`, `research_notes/`
- [ ] Two sessions share the Mac checkout and switch its branches: use a worktree per session
- [ ] Back up `~/bags` and `~/maps` to `../delivery_bot_pi_backup/` after the driven session

#### R.4 Open issues → [`docs/CA3.md`](CA3.md)
- [ ] OI-1 old `robot` box offline: confirm retired
- [ ] OI-2 `raspberrypi` key rejected: same machine reflashed?
- [ ] OI-4 echo rate 26–29 % unexplained (mitigated); optional echo-by-material test, first to drop
- [ ] OI-6 lidar start hang: wait 20 s after a stop; no fix
- [ ] OI-7 repo public: decide
- [ ] OI-8 row in `docs/CA3.md` still describes the open state: mark closed 2026-11-03

## Findings (measured)

Only measured results, each with its date and source. Hypotheses live in
[`report_plan.md`](report_plan.md) §7 until an experiment confirms or kills them.

| Date | Finding | Number | Evidence · log | Feeds |
| --- | --- | --- | --- | --- | 
| 2026-10-21 | Lidar rate and echo rate | A1M8 7.05 Hz; 26–29 % of pings return nothing; gaps follow the room, not the lidar | [`evidence/lidar/2026-10-21_composite_20revs.png`](../evidence/lidar/2026-10-21_composite_20revs.png), [`evidence/lidar/2026-10-21_scan_run1.png`](../evidence/lidar/2026-10-21_scan_run1.png) · OI-4 in `docs/CA3.md` · notes 2026-10-20/21 "P1 lidar bring-up on the old Pi", 2026-10-30 "3.4 startup race, near-return ring is the room" | Report §5.1 |
| 2026-10-30 | IMU at rest | 100 Hz, gyro z std 0.00175 rad/s | test_log 2026-10-30 "IMU at rest" | §5.1 |
| 2026-10-31 | Gyro on a hand-turned full turn | 360.2° for 360° | `~/bags/2026-10-31_turn_194945` · test_log 2026-10-31 "3.2 spin only" | RQ2 |
| 2026-10-31 | rf2o by hand, nobody behind | turn 352.9° (−2 %); 1 m push 0.962 m (−3.8 %, window 39–50 s) | `~/bags/2026-10-31_turn_194945`, `~/bags/2026-10-31_push_195343` · test_log 2026-10-31 "3.2 spin only", "3.2 forward move"; 2026-11-02 "live push on the good bag by window" | RQ2 baseline |
| 2026-10-31 | Variances fitted | rf2o vx var 1.1e-5 / 4.7e-6, wz var 8.5e-4 / 1.8e-3, gyro var 1.7e-6 (rest) | test_log 2026-10-31 "4.4 variances" | EKF config, §4 |
| 2026-10-31 | First room map; mapping config frozen after the 5.5 sweep | map + `slam_mapping.yaml` | [`results/maps/2026-10-31_room2.png`](../results/maps/2026-10-31_room2.png) · test_log 2026-10-31 "5.4 room map", "5.5 sweep" · notes 2026-10-31 "5.5 sweep done, config frozen, camera stream started" | §5.3 |
| 2026-10-31 | Camera stream and its cost | 1280x720 at 10 fps; EKF misses 20 Hz with the camera on | [`results/2026-11-02_av_stream_frame.jpg`](../results/2026-11-02_av_stream_frame.jpg) · test_log 2026-10-31 "Camera quality", "Camera under SLAM load"; 2026-11-01 "EKF 20 Hz check" · notes 2026-10-31 (night) "camera quality raised" | Ops rule: camera off while mapping |
| 2026-11-01 | Wrong-start basin, `slam_toolbox` localisation | 30 cm / 20° recovers after a push; 31° does not (one case per angle) | [`results/maps/2026-11-01_room2_home_pose.png`](../results/maps/2026-11-01_room2_home_pose.png) · test_log 2026-11-01 "6.4 wrong start, 30 cm / 20 deg", "6.4 wrong start, 30 cm / 31 deg" | RQ3 baseline |
| 2026-11-01 | Lidar start hang | `RPLIDAR running` with no S/N, several retries | OI-6 · `docs/system/06_troubleshooting.md` · test_log 2026-11-01 "6.4 wrong start, 30 cm / 31 deg" (first start hung) | Hazard table, Ops |
| 2026-11-02 | Pi under-voltage | `throttled=0x50005` on 2026-11-02 and 2026-11-03 | test_log 2026-11-02 "replay, control" · notes 2026-11-02 "OI-8: offline rig fixed, format still undecided; Pi is under-voltage" | Protocol: charged battery |
| 2026-11-03 | Replay is not repeatable | 3 replays of one bag: 0.679 / 0.592 / 0.531 m (~12 %); good-bag replay 71 % of live | test_log 2026-11-02 "replay, control"; 2026-11-03 "replay repeatability, good bag" · notes 2026-11-03 "OI-8: replay repeatability and rate" | Why plan H uses live runs, not replays |
| 2026-11-03 | **OI-8: a person behind the robot** | rf2o read 0.242 of 0.862 m and 0.307 of 1.222 m (25–28 %); nobody in the scan reads correctly; scan format cleared | [`evidence/lidar/2026-11-03_oi8_live_push.txt`](../evidence/lidar/2026-11-03_oi8_live_push.txt), [`evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`](../evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt), `~/bags/2026-11-01_push_225752`, `_230535`, `2026-11-03_*_push_ac*` · test_log 2026-11-03 "OI-8 live push A/B", "OI-8 bad bags of 2026-11-01 re-read" · notes 2026-11-03 "OI-8: live push, nobody in the scan" | RQ1, RQ2; the discovery slide |
| 2026-11-09 | Nav2 Jazzy sends plain `Twist` unless `enable_stamped_cmd_vel: true`; with it, every `/cmd_vel*` endpoint is TwistStamped | 5 nodes set, all endpoints TwistStamped (PR 32) | `/opt/ros/jazzy/include/nav2_util/nav2_util/twist_subscriber.hpp:93` · test_log 2026-11-09 "Nav2 `/cmd_vel` message type" | E1, E3, system slide |
| 2026-11-09 | IMU start calibration can fail if the robot is not still | gyro z std 0.0257 rad/s vs limit 0.01; `imu_node` exits | `/tmp/stamped_nav.log` on the Pi · test_log 2026-11-09 "Nav2 `/cmd_vel` message type" (Notes) | Run sheet: keep the robot still for 3 s at start |
| 2026-11-08 | Nav2 planner on the room map (PR 29, unmerged) | 5/5 reachable goals planned, 1.18–2.70 m, 1–5 ms | `results/maps/2026-11-08_planner_paths.png` (on PR 29) · PR 29 test_log row | E1, system slide |

## Open decisions

- [ ] Fifth member? Rebalance presenter timing if so — **all**
- [ ] OI-7: keep the repo public? — **S**
- [ ] AI-use declaration, if the module requires one — **all**

---

## Rules that hold throughout

1. Push the robot by hand for stages 1–6. You don't need working motors to learn odometry and mapping, so you never wait on the driving section.
2. Record a bag of every test drive. Tuning happens on replays, never by redriving.
3. When you replay, play `/scan`, `/imu/data` and `/tf_static` only. Never the recorded `/tf`.
4. One change at a time, written in `docs/test_log.md` with the commit hash.
5. Freeze SLAM parameters before evaluation runs (stage 9).

**Tags:** *learn* = read or think, no robot · *bag* = works from a recorded bag · *robot* = needs the robot powered · *build* = you write code or config · *needs Nav2* = waits on the navigation section.

---

## Stage 0: Foundations

**Goal:** By the end you can explain how ROS 2 nodes, topics and transforms fit together, and what kind of SLAM you're building and why.

### 0.1 ROS 2 in one picture: nodes, topics, QoS

*Tags:* learn, robot

**Why it matters.** Every part of SLAM is a node talking over topics. If you can inspect a topic, you can debug anything that follows.

**Do:**

1. Start only the lidar on the Pi (the lidar launch from the bringup package).
2. Run `ros2 node list`, `ros2 topic list`, `ros2 topic info /scan -v`, `ros2 topic hz /scan` and `ros2 topic echo /scan --once`.
3. Write down the message type, publisher, rate and QoS of `/scan`.

**Done when:** You can state `/scan`'s type, publisher node, rate and reliability setting without looking.

**Explain it back:** *What does QoS 'durability: transient local' mean, and why is `/map` published that way? (Hint: Foxglove may connect long after the map was last published.)*

### 0.2 Frames and transforms

*Tags:* learn

**Why it matters.** SLAM is mostly about keeping frames consistent. Most SLAM bugs are frame bugs.

**Do:**

1. Read REP 105 (the short section on map, odom and base_link).
2. Draw by hand: `map → odom → base_footprint → base_link → laser, imu_link`. Next to each arrow write which node publishes it: slam_toolbox, the EKF, or the URDF via robot_state_publisher.
3. Later, once things run, compare with `ros2 run tf2_tools view_frames`.

**Done when:** Your drawing matches `view_frames` when the full stack runs.

**Explain it back:** *Why are `map → odom` and `odom → base_footprint` two separate transforms instead of one? Which one is smooth, and which one can jump?*

**Read:** [REP 105, coordinate frames for mobile robots](https://www.ros.org/reps/rep-0105.html)

### 0.3 What SLAM is, and which kind you're using

*Tags:* learn

**Why it matters.** Your report needs to justify the choice, and you need the mental model to read the pose graph later.

**Do:**

1. Read the review's sections on filter-based, scan-matching and graph-based SLAM.
2. Skim the SLAM Toolbox paper (it's two pages).

**Done when:** You can place rf2o, the EKF and slam_toolbox each in one of the review's categories.

**Explain it back:** *Why does a particle-filter SLAM like GMapping struggle without wheel encoders, and what does loop closure do in a pose graph that a filter can't?*

**Read:** [Ran et al. 2025, 2D Lidar SLAM review](https://doi.org/10.3390/rs17071214) · [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783)

---

## Stage 1: The sensor: /scan

**Goal:** By the end you understand exactly what the lidar gives you, where its gaps are, and which way it faces.

### 1.1 Read a LaserScan by hand

*Tags:* robot

**Why it matters.** Every later algorithm consumes this message. Knowing its fields makes rf2o and slam_toolbox far less magical.

**Do:**

1. `ros2 topic echo /scan --once` and find `angle_min`, `angle_max`, `angle_increment`, `range_min`, `range_max`.
2. Count the entries in `ranges` and how many are `inf`.
3. Work out the angle of `ranges[i]`: `angle_min + i * angle_increment`.

**Done when:** You can point at an object in the room and predict roughly which index in `ranges` sees it.

**Explain it back:** *What does `inf` mean in `ranges`, and why is it different from a short real reading?*

### 1.2 See the scan in Foxglove

*Tags:* robot

**Why it matters.** Foxglove is your eyes for the whole section. Get comfortable with it on the simplest data.

**Do:**

1. Connect Foxglove on your Mac to `ws://sherm-raspi.local:8765`.
2. Open a 3D panel, set the display frame to `laser`, and enable `/scan`.
3. Walk around the robot and watch yourself appear.

**Done when:** Walls show as straight lines of points and you can see your own legs.

**Explain it back:** *Why does one person show up as two small arcs?*

### 1.3 Diagnose the missing points

*Tags:* bag, build

**Why it matters.** About a third of points were missing in earlier tests. Mapping and rf2o both get worse with sparse scans, so find out why now, not in stage 5.

**Do:**

1. Record 30 s of `/scan` with the robot still: `ros2 bag record -s mcap /scan -o bags/still`.
2. Write a short Python script (or node) that reads the bag and reports the fraction of `inf` ranges and a histogram of where they fall by angle (30° bins).
3. Compare with what's around the robot: glass, black or shiny surfaces, open doorways, things beyond 8 m.

**Done when:** You can say whether the gaps come from the surfaces (normal) or from the driver (fixable), with the histogram as evidence.

**Explain it back:** *If gaps cluster at one angle range regardless of where the robot points, what does that suggest?*

### 1.4 Find which way the lidar faces

*Tags:* robot

**Why it matters.** The earlier Python test used raw RPLidar angles; the ROS driver uses its own convention. A wrong yaw makes rf2o think forward is backward.

**Do:**

1. Put a box 50 cm directly in front of the robot.
2. In Foxglove (display frame `laser`), note which axis the box lands on.
3. Box on +x: yaw 0. On +y: −90°. On −y: +90°. On −x: 180°. Write it down for 2.2.

**Done when:** After the URDF is in (2.2), the box appears on +x with the display frame set to `base_link`.

**Explain it back:** *If yaw were off by 180°, what would rf2o report when you push the robot forward?*

### 1.5 Record and replay your first bag

*Tags:* bag

**Why it matters.** Replays let you rerun the same data with different settings. Every tuning step from stage 3 on depends on this habit.

**Do:**

1. `ros2 bag record -s mcap /scan /tf_static -o bags/first` while you walk around the robot.
2. Copy the bag to your Mac and open the `.mcap` file in Foxglove.
3. Play it back on the Pi too: `ros2 bag play bags/first`.

**Done when:** The bag replays in Foxglove with the same scans you saw live.

**Explain it back:** *Why is tuning on a replayed bag more trustworthy than tuning by redriving the robot?*

---

## Stage 2: The robot's frames

**Goal:** By the end the TF tree is complete and correct, so every later node can find the lidar and IMU relative to the robot.

### 2.1 Measure the robot

*Tags:* robot

**Why it matters.** Every `# MEASURE` value is a placeholder. Wrong offsets show up as maps that smear when the robot turns.

**Do:**

1. With a tape measure, find the lidar's centre relative to the midpoint between the wheels: x forward, y left, scan-plane height z.
2. Same for the IMU, plus wheel radius and the robot's outer radius.
3. Record them in `docs/test_log.md`.

**Done when:** Every `# MEASURE` value for the laser and IMU has a measured number next to it.

**Explain it back:** *Why does a lidar mounted off-centre cause smearing only when the robot turns, not when it drives straight?*

### 2.2 Write the URDF

*Tags:* build

**Why it matters.** rf2o and slam_toolbox need `base_footprint → laser`. Without it, nothing downstream starts properly.

**Do:**

1. Define links `base_footprint`, `base_link`, `laser`, `imu_link`.
2. Joints: `base_footprint → base_link` (up by the wheel radius), `base_link → laser` (your offsets plus the yaw from 1.4), `base_link → imu_link`.
3. Validate: `xacro delivery_bot.urdf.xacro > /tmp/r.urdf && check_urdf /tmp/r.urdf`.
4. Run robot_state_publisher and check `view_frames` and the robot model in Foxglove.

**Done when:** `view_frames` shows the full chain and the box from 1.4 sits on +x in `base_link`.

**Explain it back:** *The EKF publishes `odom → base_footprint`. Why must `base_footprint` still appear in the URDF? (The skeleton comment says otherwise. It's wrong.)*

**Read:** [docs/slam.md](slam.md)

---

## Stage 3: Odometry from scans: rf2o

**Goal:** By the end you know how rf2o estimates motion from two scans, how well it does on your robot, and where it breaks.

### 3.1 How rf2o works

*Tags:* learn

**Why it matters.** rf2o replaces the wheel encoders you don't have. Its weaknesses become your robot's weaknesses.

**Do:**

1. Read the rf2o paper's abstract and method overview: range flow, dense alignment, no point matching.
2. Note the reported runtime (about 1 ms per scan) and which situations the authors call hard.

**Done when:** You can explain range flow in two sentences.

**Explain it back:** *If the robot drives along a long, smooth wall, what does rf2o see change in the ranges, and what can't it measure?*

**Read:** [Jaimez et al. 2016, rf2o](https://doi.org/10.1109/ICRA.2016.7487647)

### 3.2 Run rf2o alone and push the robot by hand

*Tags:* robot, bag

**Why it matters.** Seeing raw rf2o output before fusing anything gives you a baseline to compare every later step against.

**Do:**

1. For this experiment only, run the lidar, robot_state_publisher and rf2o with `publish_tf: true`, and no EKF.
2. Record a bag. Push the robot 1 m along a taped line, then spin it 360° by hand.
3. Read the final pose from `/odom_rf2o` and compare with the tape.

**Done when:** Distance and heading error for both moves recorded in `docs/test_log.md`.

**Explain it back:** *rf2o publishes both a pose and a velocity. Why do we fuse only its velocity in the EKF?*

**Read:** [Jaimez et al. 2016, rf2o](https://doi.org/10.1109/ICRA.2016.7487647)

### 3.3 Break it on purpose

*Tags:* bag

**Why it matters.** Knowing failure modes lets you design routes and explain bad results in the report.

**Do:**

1. Try a fast hand spin, a push along a bare wall, and someone walking past.
2. In a Foxglove Plot panel, graph `/odom_rf2o.twist.twist.angular.z` during each.

**Done when:** You've ranked the three by how badly rf2o did, with plots saved.

**Explain it back:** *Why would a 5.5 Hz lidar struggle more with fast spins than a 40 Hz one?*

**Read:** [Salem et al. 2023, lidar de-skewing](https://arxiv.org/abs/2303.07312)

### 3.4 Understand the startup race

*Tags:* learn, robot

**Why it matters.** rf2o reads the laser's position only once, on its first scan. If the URDF transform isn't there yet, rf2o runs wrong for the whole session.

**Do:**

1. Start everything at once and search rf2o's startup log for a `lookupTransform` error.
2. Ask the bringup owner to delay rf2o by about 2 s (an interface request, listed in docs/slam.md).

**Done when:** Ten consecutive launches with no transform error from rf2o.

**Explain it back:** *Why would this bug matter much more if `laser_yaw` were 180° than if it were 0°?*

**Read:** [docs/slam.md](slam.md)

---

## Stage 4: Fusing the gyro: the EKF

**Goal:** By the end you understand how the EKF weighs two sensors, you've found and fixed the bug that made it ignore the gyro, and you've shown fusion helps.

### 4.1 Kalman filter intuition

*Tags:* learn

**Why it matters.** Covariance is how the filter decides whom to trust. The bug in 4.2 only makes sense once this clicks.

**Do:**

1. Read 'How a Kalman filter works, in pictures'.
2. Read the comments in `ekf.yaml` and robot_localization's README on 2D mode and sensor configuration.

**Done when:** You can describe predict and update, and what a measurement's covariance does in the update.

**Explain it back:** *Two sensors measure yaw rate. One reports variance 0.0004, the other 0.000000001. What does the filter's output follow, and why?*

**Read:** [How a Kalman filter works, in pictures](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/) · [robot_localization source and docs](https://github.com/cra-ros-pkg/robot_localization)

### 4.2 See the zero-covariance bug

*Tags:* bag

**Why it matters.** rf2o publishes zero covariance, so the EKF treats it as perfect and ignores the gyro. Seeing it yourself is better than reading about it.

**Do:**

1. Run the EKF with `odom0: /odom_rf2o` on a spin bag.
2. `ros2 topic echo /diagnostics` and find the 'covariance … was zero' warning.
3. Plot yaw rate from `/odom_rf2o`, `/imu/data` and `/odometry/filtered` together in Foxglove.

**Done when:** Screenshot showing the filtered line sitting exactly on rf2o's line, saved for the report.

**Explain it back:** *Why does robot_localization replace a zero variance with a tiny number instead of refusing the message?*

**Read:** [robot_localization source and docs](https://github.com/cra-ros-pkg/robot_localization)

### 4.3 Write the covariance relay

*Tags:* build

**Why it matters.** A small node that copies rf2o's message and fills in realistic covariance fixes the bug without changing rf2o.

**Do:**

1. In `delivery_bot_slam`, implement `odom_covariance_relay`: subscribe `/odom_rf2o`, copy, set the twist covariance, publish `/odom_rf2o_cov`.
2. The twist covariance is a 6×6 matrix stored row by row: index 0 is vx, index 35 is yaw rate. Set the others to 1e3.
3. Point `odom0` in `ekf.yaml` at `/odom_rf2o_cov`.

**Done when:** `ros2 topic echo /odom_rf2o_cov --field twist.covariance` shows your values and the diagnostics warning is gone.

**Explain it back:** *Why is a relay node a better fix here than editing rf2o's source?*

**Read:** [docs/slam.md](slam.md)

### 4.4 Calibrate the variances

*Tags:* robot, bag

**Why it matters.** Guessed variances decide the outcome of every fusion experiment. Measure them, on data you won't evaluate on.

**Do:**

1. Robot still for 30 s: compute the standard deviation of gyro yaw rate and of rf2o's vx and yaw rate.
2. Do a separate calibration push and spin run. Compare rf2o's yaw rate with the gyro's to estimate rf2o's error.
3. Set the relay's variances; note the method in `docs/test_log.md`.

**Done when:** The variance values in `odom_covariance.yaml` have a measured source written next to them.

**Explain it back:** *Why must calibration data be kept separate from the runs you evaluate? (Merrick & Nandikolla name this as a limitation of their own study.)*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

### 4.5 Show that fusion helps

*Tags:* bag

**Why it matters.** This is your first real result: does the gyro improve heading?

**Do:**

1. Record 3 full hand spins ending where you started.
2. Replay the same bag twice: EKF with rf2o only, and with rf2o plus gyro.
3. Compare final heading errors and the yaw-rate plots.

**Done when:** A small table in `docs/test_log.md`: heading error for each configuration.

**Explain it back:** *If fusion barely changes the result on straight pushes but helps on spins, what does that tell you about where rf2o is weakest?*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468) · [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264)

---

## Stage 5: Mapping with slam_toolbox

**Goal:** By the end you have a saved map of the room, you can read the pose graph, and you've tuned the few parameters that matter, then frozen them.

### 5.1 Pose graphs and loop closure

*Tags:* learn

**Why it matters.** When the map suddenly snaps straight, that's loop closure. Understanding it turns that moment from magic into something you can debug.

**Do:**

1. Re-read the SLAM Toolbox paper and the slam_toolbox README's description of modes.
2. Look at `slam_mapping.yaml` and find the loop-closure parameters and `ceres_loss_function`.

**Done when:** You can say what a node, an edge and a loop closure are, in your robot's terms.

**Explain it back:** *What could go wrong with a loop closure in a room with two similar-looking walls, and why does Huber loss help?*

**Read:** [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783) · [Huang et al. 2022, robust 2D lidar SLAM](https://doi.org/10.1007/s13320-022-0657-6) · [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

### 5.2 Lifecycle nodes, learned by breaking them

*Tags:* robot, learn

**Why it matters.** slam_toolbox 2.8 waits to be configured and activated. Launched as a plain node it sits idle with no error, and the reference launch file has exactly this bug.

**Do:**

1. Start `async_slam_toolbox_node` as a plain node with your params.
2. `ros2 lifecycle get /slam_toolbox` shows `unconfigured`, and there's no `/map`.
3. Then: `ros2 lifecycle set /slam_toolbox configure` and `ros2 lifecycle set /slam_toolbox activate`. The map appears.

**Done when:** You've seen the node go unconfigured → inactive → active and the map appear only at the end.

**Explain it back:** *Why would a robotics framework want nodes that start idle and wait to be activated?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

### 5.3 Write mapping.launch.py

*Tags:* build

**Why it matters.** Make the lifecycle steps automatic so mapping starts with one command.

**Do:**

1. Include the base launch. Start slam_toolbox as a `LifecycleNode`.
2. Emit a configure event, then on reaching `inactive`, emit activate (the same pattern as slam_toolbox's own `online_async_launch.py`).
3. Forward `use_sim_time` so the same launch works on bags.

**Done when:** One command gives you `/map` with no manual lifecycle steps, live and on a replayed bag.

**Explain it back:** *Why does the activate step need to wait for the `inactive` state rather than firing straight after configure?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox) · [docs/slam.md](slam.md)

### 5.4 Map the room

*Tags:* robot, bag

**Why it matters.** Your first real map, and the bag you'll tune on.

**Do:**

1. Start on the taped home mark. Push slowly (or use teleop), loop the room, return to home. Record a bag.
2. Watch `/slam_toolbox/graph_visualization` in Foxglove grow, and catch the loop-closure snap.
3. Save: `map_saver_cli` for the image, and the `serialize_map` service for localisation.

**Done when:** Walls are straight, and two wall-to-wall distances on the map match the tape measure within 5 cm.

**Explain it back:** *Where in the room did the map look worst before loop closure, and why there?*

**Read:** [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783)

### 5.5 Tune on replays, then freeze

*Tags:* bag, build

**Why it matters.** Evaluation is only fair if parameters stay fixed. Do your tuning now, deliberately.

**Do:**

1. Write `slam_replay.launch.py`: robot_state_publisher, rf2o, relay, EKF, slam_toolbox, all with `use_sim_time`, no drivers.
2. Replay the 5.4 bag (only `/scan`, `/imu/data` and `/tf_static`) varying one parameter at a time: `min_laser_range` 0 vs 0.15, loop closure on vs off, `minimum_travel_distance`.
3. Pick values, commit them, and write 'frozen on <date>, commit <hash>' at the top of the config.

**Done when:** A short table of what each change did, and a frozen config commit.

**Explain it back:** *Why must you never replay the recorded `/tf` when rerunning SLAM on a bag?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [docs/slam.md](slam.md)

---

## Stage 6: Localisation on the saved map

**Goal:** By the end the robot knows where it is on the map at every start, and you know how much error it can recover from.

### 6.1 Mapping versus localisation

*Tags:* learn

**Why it matters.** In localisation the map is frozen and only `map → odom` changes. That's what navigation relies on.

**Do:**

1. Compare `slam_mapping.yaml` with `slam_localization.yaml` and list every difference.
2. Read why the plan uses slam_toolbox localisation and not AMCL fed back into the EKF.

**Done when:** You can explain each difference between the two configs.

**Explain it back:** *Kudriashov et al. found that feeding map-based corrections back into odometry hurt in repetitive spaces. Why might that happen?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783)

### 6.2 Run localisation

*Tags:* robot, build

**Why it matters.** Write the SLAM part of the navigation launch and check it on its own before Nav2 is added.

**Do:**

1. Start `localization_slam_toolbox_node` as a `LifecycleNode` with `map_file_name` pointing at your serialised map.
2. Place the robot on the home mark and start.

**Done when:** In Foxglove, live `/scan` points sit on the map's walls.

**Explain it back:** *Why does the robot need to start on the home mark (or be told where it is)?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

### 6.3 Set the start pose from Foxglove

*Tags:* robot

**Why it matters.** Lets you start anywhere, and is the tool for the next test.

**Do:**

1. In the 3D panel, use 'Publish pose estimate', which publishes to `/initialpose`.
2. Place the robot away from home, click its position and heading on the map.

**Done when:** Scan points snap onto the walls after you publish the pose.

**Explain it back:** *What would happen if you clicked the right position but the wrong heading?*

### 6.4 Wrong-start test

*Tags:* robot

**Why it matters.** Measures how forgiving localisation is: a direct answer to 'what if the robot isn't exactly on the tape?'.

**Do:**

1. Start the robot 10, 20, 30 cm and 5°, 10°, 15° off the home mark without telling it.
2. Push it around a little and see whether it converges.

**Done when:** A table of offsets that converged and ones that didn't.

**Explain it back:** *Why does a symmetric room make this harder?*

---

## Stage 7: Your Foxglove SLAM workspace

**Goal:** By the end you can watch and control the whole SLAM section from one saved Foxglove layout the team can open.

### 7.1 Write the trajectory recorder

*Tags:* build

**Why it matters.** slam_toolbox doesn't publish a path. Seeing the SLAM path and the odometry path side by side shows drift live, and the same node exports data for evaluation.

**Do:**

1. Implement `trajectory_recorder`: publish `/slam/path` from TF `map → base_footprint` and `/odom/path` from `/odometry/filtered`, adding a pose every 2 cm or 2°.
2. On shutdown, write both as TUM files when `tum_output_dir` is set.

**Done when:** Both paths show in Foxglove, and `evo_traj tum slam.txt odom.txt --plot` reads the files.

**Explain it back:** *When the two paths separate during a run, which one is wrong, and how do you know?*

**Read:** [evo trajectory evaluation](https://github.com/MichaelGrupp/evo)

### 7.2 Build and commit the layout

*Tags:* build

**Why it matters.** One shared layout means everyone sees the same thing and screenshots are consistent for the report.

**Do:**

1. 3D panel (frame `map`): `/map`, `/scan`, TF, robot model, `/slam_toolbox/graph_visualization`, both paths.
2. Plot panel: the three yaw rates from 4.2.
3. Export the layout to `docs/foxglove/slam_layout.json` and commit it.

**Done when:** A teammate can open the layout file and see the same view.

**Explain it back:** *Which panel would you look at first if the map started smearing, and why?*

### 7.3 Control SLAM from Foxglove

*Tags:* robot

**Why it matters.** Saving maps and pausing mapping without typing service calls over SSH.

**Do:**

1. Call Service panel: `/slam_toolbox/serialize_map`, `/slam_toolbox/save_map`, `/slam_toolbox/pause_new_measurements`.
2. Save a map from Foxglove and check the files appear on the Pi.

**Done when:** Map saved and serialised entirely from Foxglove.

**Explain it back:** *When would you pause new measurements during mapping?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

---

## Stage 8: Autonomous mapping

**Goal:** By the end the robot maps the room by itself and drives home, and you can compare that with mapping by hand.

> Starts once Nav2 reaches goals reliably (navigation section).

### 8.1 How frontier exploration works

*Tags:* learn

**Why it matters.** A frontier is the border between mapped free space and unknown space. The robot keeps driving to the best one until none are left.

**Do:**

1. Read the explore_lite README and its parameter list.
2. Find in `config/explore.yaml` what `min_frontier_size`, `progress_timeout` and `return_to_init` do.

**Done when:** You can predict what the robot will do first in your room.

**Explain it back:** *Why use Nav2's global costmap for frontiers rather than the raw `/map`?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.2 Build explore_lite

*Tags:* build, needs Nav2

**Why it matters.** It isn't in apt for Jazzy; it builds from the pinned source in `deps.repos`.

**Do:**

1. `vcs import` the pinned repo, then `colcon build --packages-select explore_lite_msgs explore_lite`.
2. Skip `multirobot_map_merge`; you don't need it.

**Done when:** `ros2 pkg executables explore_lite` lists `explore`.

**Explain it back:** *Why pin an exact commit rather than following the branch?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.3 Write explore.launch.py

*Tags:* build, needs Nav2

**Why it matters.** Combines mapping, Nav2 and the explorer in one supervised launch.

**Do:**

1. Base launch + slam_toolbox mapping (lifecycle, `map_update_interval: 2.0`) + Nav2 `navigation_launch.py` + the `explore` node with `explore.yaml`.
2. Keep `dry_run` defaulting to true like the other launches.

**Done when:** With `dry_run` on, frontiers appear on `/explore/frontiers` in Foxglove and Nav2 receives goals.

**Explain it back:** *explore_lite starts driving the moment it launches. How does your workflow keep that safe?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.4 First supervised run

*Tags:* robot, needs Nav2

**Why it matters.** The moment the robot maps on its own. Do it watched, with a hand near the kill switch.

**Do:**

1. Robot on home, someone at the motor switch. Launch, watch frontiers and the map grow.
2. Practise pausing: publish `false` to `/explore/resume` from Foxglove, then `true`.
3. Record a bag of the whole run.

**Done when:** Exploration completes, the robot returns home, and the map is saved.

**Explain it back:** *Where did the robot hesitate or turn back, and what was the frontier doing at that moment?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.5 Compare with manual mapping

*Tags:* bag, needs Nav2

**Why it matters.** Turns the demo into a result for the report.

**Do:**

1. Compare against your 5.4 map: time to finish, room dimensions vs tape, wall straightness.
2. Return-to-start error: the final pose against the home mark.

**Done when:** A comparison table in `docs/test_log.md`.

**Explain it back:** *Is the autonomous map better or worse, and is that because of the path the robot chose or because of SLAM?*

**Read:** [Filatov et al. 2017, 2D SLAM quality metrics](https://arxiv.org/abs/1708.02354)

---

## Stage 9: Experiments (plan H)

**Goal:** honest numbers for the CA3 questions, from the robot itself: what people do to a
cheap delivery robot, which part breaks, which localiser holds up, and whether it stops in
time. Every method runs **live**, once in an empty room and once with 1–2 people walking.
Design and the reasons for it: [`report_plan.md`](report_plan.md) §2–4 (decision D8b).

> Later: only after parameters are frozen (5.5) and the motors pass the safety review (R.1).
> Replay of the old bags (10-31 to 11-03) is background only: it reads about 71 % of live.

### 9.1 Survey floor checkpoints

*Tags:* robot

**Why it matters.** Your ground truth, with no camera needed: known positions measured with a tape.

**Do:**

1. Mark 5 crosses with heading lines around the room, including home and each seat.
2. Measure each from two walls; store them in `checkpoints.yaml`.
3. Tape the two people paths: one crossing the route, one behind the robot's start. The people walk these every people run, so "people" is one condition.

**Done when:** Each checkpoint measured twice, agreeing within 1 cm; both paths taped and photographed.

**Explain it back:** *Why measure from two walls rather than one?*

### 9.2 Live switches and run sheet

*Tags:* build, robot

**Why it matters.** 50+ live runs only compare if each method starts the same way every time, by one command, with its bag and log row.

**Do:**

1. EKF variants in `delivery_bot_bringup/config/ekf_variants/` (rf2o + IMU, rf2o only, IMU only) and `ekf:=false` (no EKF, identity `odom → base_footprint`), selectable from `navigation.launch.py`.
2. `localizer:=slam|amcl` in `navigation.launch.py`: AMCL with `map_server` on the same room map, Nav2 started after localisation is up.
3. `tools/timed_move.py`: open-loop 1 m straight and 360° spin, published on the collision monitor's input so its obstacle stop still applies.
4. `tools/run_cell.py`: one cell → launch, bag `~/bags/<date>_<exp>_<cell>_run<N>`, printed test_log row.

All four are in the worker prompt `delegate-live-switches.md`.

**Done when:** each switch starts on the Pi with no motion, and its test_log row exists.

**Explain it back:** *Why is the timed move open loop, when everything else on the robot is closed loop?*

### 9.3 Driven session

*Tags:* robot, bag

**Why it matters.** Several physical runs per cell, not one bag replayed, so the results show real variation, on the robot as a customer would meet it.

**Do:**

1. Charged battery and a spare; `vcgencmd get_throttled` = `0x0`; keep the robot still for 3 s at every start (the IMU calibrates then).
2. Wheels raised first, then one 1 m straight with the motor switch in reach.
3. Freeze the config; note the commit. Then run the cells of 9.4, 9.5 and 9.7 and the E1 delivery runs from the run sheet, each empty and with people, 3 runs per cell.
4. On every run note: how a failure starts (drift, jump, lost), whether it recovers once people leave, where in the room it happened.
5. Fallback if driving fails: 9.4 by pushing with a stick (nobody behind the robot except in people runs); 9.5 and E1 reported as partial.

**Done when:** every cell has its bags and tape numbers, each with a test_log row.

**Explain it back:** *Why does replaying one bag five times measure something different from five physical runs?*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

### 9.4 Odometry configs, empty vs people

*Tags:* robot, bag

**Why it matters.** Report RQ2 (experiment E2): which part breaks when people walk past. OI-8 says scan odometry does; does the gyro rescue it, or does SLAM hide it? An analogue of [M26] (they ablate the IMU on top of wheel odometry; we have none).

**Do:**

1. Per config (rf2o + IMU, rf2o only, IMU only, none) and condition: `timed_move.py straight` ×3 and `spin` ×3.
2. Measure distance and heading error against the tape and floor marks, before SLAM (`/odometry/filtered`) and after SLAM (map pose).

**Done when:** a table of 4 configs × 2 conditions, before and after SLAM.

**Explain it back:** *Merrick & Nandikolla found better odometry barely changed the SLAM result. Did yours, and did people change that?*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

### 9.5 Localiser: slam_toolbox vs AMCL

*Tags:* robot, bag, needs Nav2

**Why it matters.** Report RQ3 (experiment E3): which localiser a cheap delivery robot should ship. A particle filter and a scan graph should fail differently around moving bodies. [K26] compared AMCL on and off by replay, without ground truth; you have tape.

**Do:**

1. Nav2 drives the same checkpoint loop, 3 loops per localiser per condition, each localiser steering its own runs.
2. Wrong starts at 10/20/30/40 cm and 10/20/30/40° per localiser, empty room (your `slam_toolbox` baseline: 30 cm / 20° recovers, 31° does not, 6.4).
3. Stop error at each checkpoint by tape; pairwise trajectory error between loops with `evo` (9.8).

**Done when:** checkpoint error and pairwise ATE per localiser × condition, plus the wrong-start grid.

**Explain it back:** *What does low repeatability error tell you, and what doesn't it tell you?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [Filatov et al. 2017, 2D SLAM quality metrics](https://arxiv.org/abs/1708.02354)

### 9.6 What people do

*Tags:* bag

**Why it matters.** Report RQ1, the headline: how much people cost the robot. A delivery robot's customers are the obstacles. Extends [Y21] from mapping to localisation.

**Do:**

1. Pull the empty-vs-people difference out of 9.4 and 9.5 into one table: method, error empty, error with people, change, failures.
2. Room figure: where failures happened, against the people paths (from the bags).

**Done when:** the table and the figure, with every number traceable to a test_log row.

**Explain it back:** *Did the people hurt the pose estimate more through the scan matching (rf2o) or through the map matching (slam_toolbox or AMCL)? How would you tell from the bag?*

**Read:** [Ye et al. 2021, mapping with a person tracker](https://doi.org/10.1109/ROBIO54168.2021.9739394)

### 9.7 Step-in safety

*Tags:* robot

**Why it matters.** Report RQ4 (experiment E4): does it stop in time when someone steps in front? The stop zone (0.20 m, ±35°) may be too small at walking pace (`reports/MPC planners for dynamic humans.md`, inference).

**Do:**

1. A person steps in front of the moving robot at walking pace, 3–5 times, collision monitor active.
2. Record stop distance by tape and any contact. The motor and safety behaviour belong to the teammate; here you need the bag and the distance.

**Done when:** a table of stop distance and contacts against the 0.20 m zone.

**Explain it back:** *Which delay matters most between the person appearing and the wheels stopping: scan rate, costmap, collision monitor or motor watchdog?*

### 9.8 Metrics and figures

*Tags:* build, bag

**Why it matters.** Turns tape numbers and bags into the report's tables and figures.

**Do:**

1. Tape numbers first: checkpoint error, distance and heading error per run.
2. `evo` (Mac Docker or the Pi) for pairwise ATE and RPE from the bags, where it fits.
3. One figure per RQ with commit and bag in the caption; one "Our take" per RQ.

**Done when:** one command prints every table; figures are in `report/figures/`.

**Read:** [evo trajectory evaluation](https://github.com/MichaelGrupp/evo)

### 9.9 Measure the Pi's load

*Tags:* robot

**Why it matters.** Running onboard a Pi 4 is a gap in the published work, so it's worth a number; the full stack now includes Nav2.

**Do:**

1. Log CPU and memory per node during localisation with Nav2 (for example with a small `psutil` logger), once per localiser.

**Done when:** Average and peak CPU and RAM recorded for each mode.

**Explain it back:** *Which node uses the most CPU, and does it matter at your speeds?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264)

### 9.10 Write the SLAM section

*Tags:* learn

**Why it matters.** Bring it together: what you built, why, what the numbers say, and what you'd do next.

**Do:**

1. Background (the review), design choices (cited), results tables from 9.4–9.7, limitations.
2. Future work: people filtering, a larger or predictive stop zone, deskewing, lidar degradation.

**Done when:** Every design decision in the write-up cites its source or says it's your own design.

**Explain it back:** *If you had one more week, which extension would you pick and why?*

**Read:** [Ran et al. 2025, 2D Lidar SLAM review](https://doi.org/10.3390/rs17071214) · [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

---

## Stage X: Extensions

**Goal:** Optional. Each one builds on a finished core and adds a distinctive result.

> Pick at most one.

### X.1 Gyro-based scan deskewing

*Tags:* build, bag

**Why it matters.** At 5.5 Hz the robot rotates during a scan, which warps it. Correcting each point with the gyro should sharpen maps on turn-heavy routes.

**Do:**

1. Write a node that re-projects each point using the gyro's rotation at that point's time; feed the corrected scan to rf2o and slam_toolbox.
2. Compare no deskew vs gyro deskew on spin-heavy bags.

**Done when:** Before/after figure of a scan during a spin, and the heading error for each.

**Explain it back:** *Why is this effect worse on a slow lidar than a fast one?*

**Read:** [Salem et al. 2023, lidar de-skewing](https://arxiv.org/abs/2303.07312)

### X.2 People in the room

*Tags:* build, bag

**Why it matters.** A delivery robot works around people, who leave smears in maps.

**Do:**

1. Map with 0, 1 and 2 people walking; compare each map with the empty-room map.
2. Optionally filter detected legs out of the scan used by slam_toolbox only.

**Done when:** Map difference against the empty-room map for each condition.

**Explain it back:** *Why should the obstacle stop still use the raw scan, even if mapping uses the filtered one?*

**Read:** [Ye et al. 2021, mapping with a person tracker](https://doi.org/10.1109/ROBIO54168.2021.9739394)

### X.3 Map quality without ground truth

*Tags:* build

**Why it matters.** Adds objective map scores to the comparison tables.

**Do:**

1. Implement occupied-cell proportion, corner count and enclosed-area count on saved maps.

**Done when:** Scores computed for every saved map.

**Explain it back:** *Which metric best caught the bad maps you've seen?*

**Read:** [Filatov et al. 2017, 2D SLAM quality metrics](https://arxiv.org/abs/1708.02354)

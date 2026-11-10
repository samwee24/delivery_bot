# SLAM challenges and how we overcame them (evidence log)

For slides 9-11 and the report's Challenges section. Each challenge goes along the SLAM pipeline:
**lidar → odometry → fusion → mapping → localisation → SLAM inside the navigation loop**. Each one gives
the symptom as it appeared (exact log text), what we tried, the numbers, the fix, how we verified it, and where
the proof lives. Sources: `docs/test_log.md` (cited as *test_log date "first words"*), `notes/notes.md`
(*notes date "block title"*), `docs/CA3.md` OI list, `evidence/`, `results/`, commits.

Summary:

| # | Stage | Challenge | Dates | Fix | Verified by |
| --- | --- | --- | --- | --- | --- |
| S1 | Lidar | Only a third of pings return | 10-21 to 10-30 | Accepted: the room, not the lidar | Map made; scale within 3.5 cm of tape |
| S2 | Lidar → mapping | slam_toolbox rejected scans: fan-shaped map | 10-31 | `angle_compensate` on (720 beams) | 317 x 233 map, 0 rejections |
| S3 | Mapping | Which slam_toolbox settings? No ground truth | 10-31 | Loop-closure gap as the metric; froze the base set | 0.109 m gap over 42 m vs 0.658 m without loop closure |
| S4 | Mapping | slam_toolbox stuck "unconfigured" | 11-01 | Delay the configure step 5 s | Active with no manual steps |
| S5 | Localisation | Localisation never started | 11-01 | `map_start_pose` instead of `map_start_at_dock` | `map → odom` published |
| S6 | Localisation | Wrong start beyond 20° never recovers | 11-01 | Taped home mark; start on it | 2.6 cm scan-to-map on the mark |
| S7 | Odometry | Lidar odometry read 24 % of a push | 11-01 to 11-03 | Cause found: a person behind the robot; 0.6 m range cut | 99.5 % offline; 96-101 % with nobody behind |
| S8 | Method | Replays of one recording disagree | 11-02 to 11-03 | Test live; recordings are evidence only | 3 replays 0.53-0.68 m vs 0.96 m live |
| S9 | Fusion | rf2o reports zero uncertainty; EKF weights unknown | 10-30 to 10-31 | Covariance relay; variances fitted from two bags | Turn: gyro 360.2°, rf2o 352.9° |
| S10 | SLAM in the loop | Navigation aborts: map → odom "too old" | 11-10 | `restamp_tf`, transform tolerance 0.5 s | `Goal succeeded` |
| S11 | Map use | Home pose 0.21 m from an obstacle | 11-10 | Moved home to 0.67 m clearance | On-mark pose within 1 cm and 2° |

---

## S1 · Lidar: only a third of pings return (2026-10-20/21, OI-4)

- **Symptom.** First bring-up of the A1M8: 95-105 returns with a distance per revolution against ~350
  expected; echo rate **33-35 %, stable over 3 runs** (expected > 90 %). Health `('Good', 0)`, model 24 = A1M8.
  *(notes 2026-10-20/21 "P1 lidar bring-up on the old Pi")*
- **Investigation.**
  1. Per-15° sector the echo rate depends strongly on angle, so not a dead unit.
  2. The serial link was clean and the returns that did arrive were strong (quality 15 of 15), so the loss is optical, not the driver.
  3. Near-return bins (< 0.30 m) moved between three recordings (0-60°, then 30-120°, then 90-180°): the gaps follow the
     scene, not the sensor. *(notes 2026-10-30 "3.4 startup race, near-return ring is the room")*
  4. On the robot Pi: 26-29 % no-echo, 7.05 Hz.
- **Impact on SLAM.** Fewer points per scan; glass and dark surfaces vanish. Once a wall 0.46 m behind the
  robot was missing from both scan and map. *(test_log 2026-10-31 "5.4 scale check")*
- **Decision.** Accept it, no angle mask; map anyway.
- **Verified.** Raw scan scale against tape: 1.085 m vs 1.05 m (+3.5 cm), 1.494 m vs 1.48 m (+1.4 cm); map
  reading 1.00 m vs 1.05 m (-5 cm, one 5 cm cell). *(test_log 2026-10-31 "5.4 scale check")*
- **Evidence.** `evidence/lidar/2026-10-21_composite_20revs.png`, `evidence/lidar/2026-10-21_scan_run1.png`.
- **Lesson.** A cheap lidar's dropouts are mostly the room. Measure which before blaming the sensor.

## S2 · slam_toolbox rejected scans, the first map came out as a fan (2026-10-31)

- **Symptom.** The first room map (`~/maps/2026-10-31_room`) was a 184 x 112 fan, not a room. slam_toolbox
  rejected 223 scans, repeating:
  `LaserRangeScan contains 1041 range readings, expected 931`
  *(test_log 2026-10-31 "5.4 room map"; docs/system/06_troubleshooting.md)*
- **Cause.** With `angle_compensate` off, rplidar_ros sends a different number of beams every revolution.
  slam_toolbox fixes the expected count from the first scan and drops every scan that differs.
- **Fix.** `angle_compensate: true` in `lidar.launch.py`: a fixed 720 beams at 0.5°.
- **Verified.** Second map `2026-10-31_room2`: 317 x 233 cells at 0.05 m, 65.5 m² free, 4375 occupied cells;
  0 scans rejected in every later sweep run. `results/maps/2026-10-31_room2.png`.
- **Twist.** Two days later this fix was the prime suspect for S7 (good odometry bags had 1046 beams, bad
  ones 720). Live pushes with it on and off read 1.008 and 0.961 of the tape, so it was cleared.

## S3 · Choosing slam_toolbox settings without ground truth (2026-10-31, task 5.5)

- **Problem.** Package defaults are tuned for other lidars. We had no motion capture, only a taped start mark.
- **Method.** The map lap starts and ends on the same mark, so the gap between the first and last SLAM pose
  is an error measure. One parameter changed per run, same recording replayed each time.
  Command: `bash /tmp/sweep.sh` (replay of `~/bags/2026-10-31_map_200956` through `slam_replay.launch.py
  slam_params_file:=<variant>.yaml`), `python3 /tmp/sweep_an.py`.

  | Variant | Map cells | Occupied | Start-end gap over 42 m |
  | --- | --- | --- | --- |
  | base (`min_laser_range` 0.15, loop closing on, `minimum_travel_distance` 0.1) | 313 x 132 | 4087 | **0.109 m** |
  | `min_laser_range` 0 | 299 x 131 | 3721 | 0.123 m |
  | loop closing off | 304 x 135 | 4285 | **0.658 m** |
  | `minimum_travel_distance` 0.05 | 297 x 132 | 4169 | 0.186 m |
  | `minimum_travel_distance` 0.2 | 296 x 131 | 3468 | 0.113 m |

  *(test_log 2026-10-31 "5.5 sweep")*
- **Decision.** Freeze the base set (`slam_mapping.yaml`). Loop closure cuts the gap six-fold; it is the part
  of SLAM that makes the map usable.
- **Check.** Repeat of the base run: 0.115 m vs 0.109 m, run-to-run noise about 1 cm. *(test_log 2026-11-01 "EKF 20 Hz check")*
- **Lesson.** With no ground truth, design one: a closed loop on a taped mark.

## S4 · slam_toolbox stuck "unconfigured" (2026-11-01, task 5.3)

- **Symptom.** `Failed to make transition 'TRANSITION_CONFIGURE' for LifecycleNode '/slam_toolbox'`; node
  stays unconfigured. Worse, a leftover slam_toolbox from an earlier run made `ros2 lifecycle get` read
  `active`, a false pass. *(test_log 2026-11-01 "5.3 bag half")*
- **Cause.** slam_toolbox is a lifecycle node; when it was the only process, the configure request was sent
  before its lifecycle services existed.
- **Fix.** Send configure from a 5 s `TimerAction`; check for stale processes before every run.
- **Verified.** Second run: configured and activated by itself, 0 range-count rejections.
- **Lesson.** A test that can pass on a leftover process is not a test. *(docs/system/06_troubleshooting.md)*

## S5 · Localisation never started (2026-11-01, task 6.2)

- **Symptom.** `Starting localization at first node (dock) is correctly not supported`; no `map → odom`.
- **Cause.** `map_start_at_dock: true` is rejected in localisation mode in slam_toolbox 2.8.5.
- **Fix.** `map_start_pose: [0, 0, 0]` (the map origin was the home mark).
- **Verified.** Loaded `2026-10-31_room2_graph.posegraph`; `map → odom` 0.008, 0.070 m, 1.1°; live scan
  points sit on the map walls (Foxglove). *(test_log 2026-11-01 "6.2 headless", "6.2 live")*

## S6 · How wrong can the start be? (2026-11-01, task 6.4)

- **Question.** Localisation is told the robot starts on the home mark. What if it does not?
- **Tests** (robot placed off the mark by ruler, `navigation.launch.py` restarted, `tf2_echo map base_footprint`):

  | Placed offset | Result | Numbers |
  | --- | --- | --- |
  | 30 cm, 20° | **recovers after a short push** | `map → odom` 0.352 m, -18.2°, close to the placed offset; scan on the walls |
  | 30 cm, 31° | **does not recover** | position right (0.36 m), heading about 37° wrong; scan rotated about 30° |
  | 60 cm, 30° | does not recover | heading about 37° off |

  *(test_log 2026-11-01 "6.4 wrong start" rows)*
- **Why.** The scan matcher only searches ±20° (`coarse_search_angle_offset` 0.349 rad), and it only matches
  after the robot has moved 0.1 m (`minimum_travel_distance`), so a standing robot never corrects.
- **What we did.** Taped a home mark and start every run on it. When the mark moved on 2026-11-10 the
  localiser read (-1.302, -0.307, 149.1°) against (-1.3, -0.3, 151°); scan-to-map median 2.6 cm, 77-80 % of
  points within 10 cm. *(notes 2026-11-10 "home mark moved")*
- **Lesson.** Localisation on a known map is reliable only inside the matcher's search window: a procedure
  (a taped mark) is part of the system.

## S7 · Lidar odometry read a quarter of the distance: a person behind the robot (2026-11-01 to 11-03, OI-8)

The longest SLAM bug: three days, five hypotheses.

| Step | Date | What we did | Result | Conclusion |
| --- | --- | --- | --- | --- |
| 1 | 11-01 | Push 1.00 m by hand, rf2o alone, bag `2026-11-01_push_225752` | rf2o 0.243 m (24 %) | Odometry broken? |
| 2 | 11-01 | Redo, 1.20 m, new spot, bag `..._push_230535` | rf2o 0.289 m (24 %) | Same ratio in two places: looks like a scale bug |
| 3 | 11-01 | Compare scan format across 5 bags (`scanfmt.py`) | good bags 1044-1046 beams, bad bags 720 (S2's fix) | Suspect: beam count |
| 4 | 11-02 | Replay the bad bag offline, rates 1.0 and 0.25 (`rf2o_fmt.sh`) | 0.291 m and 0.289 m every time | Not CPU, not timing |
| 5 | 11-03 | Live stick pushes, nobody near, `angle_compensate` on / off | 1.008 and 0.961 of tape | Beam count cleared |
| 6 | 11-03 | Count scan points < 1.2 m behind the robot (`pushwall.py`) | bad bags: median 127 and 152 points 0.35-0.9 m behind, gone after the push; stick runs: 16-18 | **A person walked behind the robot** |
| 7 | 11-03 | Replay bad bags with returns < 0.6 m removed (`scan_minrange.py`) | 1.216 of 1.222 m (99.5 %) | Fix shown offline |

- **Why it happens.** rf2o estimates motion from how the whole scan shifts and assumes the world is still. A
  body walking along behind the robot keeps a constant distance, so that part of the scan says "not moving".
- **Evidence.** `evidence/lidar/2026-11-03_oi8_live_push.txt`, `evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`;
  test_log 2026-11-03 "OI-8 live push A/B", "bad bags re-read", "offline fix test"; figure
  `report/figures/2026-11-10_oi8_person_behind.gif`.
- **Status.** Explained; the live fix (`laser_filters` range filter) is future work. Cost of the cut: no odometry
  from anything nearer than 0.6 m.
- **Lesson.** Without wheel encoders, the lidar is the odometry, and anything moving with the robot fools it.
  Literature link: [Y21] measured people raising 2D-lidar map error from 5.9 to 80 cm; we saw the same effect one
  stage earlier, in odometry.

## S8 · Replays of the same recording disagree (2026-11-02/03)

- **Symptom.** During S7, the good bag (live 0.962 m) replayed through rf2o three times in a row gave
  **0.679 / 0.592 / 0.531 m** (spread -12 %, about 71 % of live).
- **Tests.** Playback rate 0.5: 0.689 m; rate 0.25: 0.681 m. Slowing down did not bring it back.
  *(test_log 2026-11-03 "replay repeatability" and rate rows)*
- **Conclusion.** On a loaded Pi 4 a replay is not the robot. From then on every result was measured live;
  recordings are kept as evidence.
- **Literature link.** [K26] produced all its SLAM results by replaying recordings on a desktop (Ryzen 7,
  32 GB) and did not evaluate on-board performance. On our hardware that method would not have been repeatable.

## S9 · Sensor fusion: zero uncertainty from rf2o, unknown weights (2026-10-30/31, tasks 4.2-4.4)

- **Problem.** rf2o publishes its velocity with an all-zero covariance, which tells the EKF "perfectly
  certain". robot_localization then trusts it absolutely, or ignores the IMU.
- **Fix 1: covariance relay.** A small node copies rf2o's output with `idx0` 1e-3, `idx35` 4e-3 and 1e3 on unused
  axes; checked at 7.06 Hz = the rf2o rate. *(test_log 2026-10-30 "4.3 relay")*
- **Fix 2: fitted variances** from two hand-moved bags (turn and push), `var_an.py`: at rest rf2o vx variance
  1.1e-5, wz 8.5e-4, gyro 1.7e-6; moving, rf2o under-reads fast rotation by 9-15 %. Set `vx_variance` 1e-4,
  `vyaw_variance` 5e-3, `gyro_var` 1e-4. *(test_log 2026-10-31 "4.4 variances")*
- **Rule.** `odom → base_footprint` comes from the EKF alone (rf2o `publish_tf: false`); two publishers of one
  transform make the map spin. *(AGENTS.md)*
- **Result.** One hand turn: gyro 360.2°, rf2o 352.9° (-2 %); the IMU carries heading.
  `report/figures/2026-11-10_turn_gyro_vs_rf2o.png`. Literature link: [M26] found fusing the IMU cut
  odometry error 60-75 % before SLAM.

## S10 · SLAM inside the navigation loop: "transform too old" (2026-11-10)

- **Symptom.** A goal aborted 2.5 s in:
  `Transform data too old when converting from map to odom` (data 0.37 s old), then
  `Failed to transform end pose to global frame`; earlier `error_code: 102` (TF_ERROR) and
  `Lookup would require extrapolation into the future`. *(test_log 2026-11-10 rows; handover 2026-11-10)*
- **Cause.** slam_toolbox stamps `map → odom` with the time of the last scan it processed. At Pi load 13-22
  it processes a scan only every ≥ 0.5 s, so Nav2's 0.1-0.3 s tolerances fail mid-goal.
- **Fix.** `restamp_tf: true` in `slam_localization.yaml` (commit 42f0f83: `map → odom` re-stamped every
  20 ms); `transform_tolerance` 0.5 s on costmaps, behaviour server, controller and collision monitor
  (cd44057, ebfe113). Each guarded by a test in `delivery_bot_slam/test/test_config_consistency.py`.
- **Verified.** `bt_navigator`: `Goal succeeded` after 93 s, (-1.35, -0.29) → (-2.67, 0.42), 2026-11-10.
- **Lesson.** SLAM's timing, not its accuracy, broke navigation. Tolerances in the papers' stacks assume a
  faster computer.

## S11 · The map said the home mark was too close to obstacles (2026-11-10)

- **Symptom.** Goal (1, 0) from the old home crept 0.21 → 0.34 m in about 3 min, then
  `Failed to make progress`.
- **Analysis.** Distance transform of the saved map: the old home was 0.21 m and goal (1, 0) 0.16 m from the
  nearest obstacle, both inside Nav2's 0.25 m inflation and slow-down zone.
  `results/maps/2026-11-10_home_clearance.png`.
- **Fix.** New home (-1.3, -0.3) with 0.67 m clearance, yaw 151° fitted parallel to the walls; set in three
  configs, which a test keeps in agreement. `results/maps/2026-11-10_new_home.png`.
- **Verified.** Localiser on the new mark: (-1.302, -0.307, 149.1°), scan-to-map median 2.6 cm.

---

## Pattern across S1-S11 (for the analysis slide)

- **Where they sat:** lidar 2, odometry 1, fusion 1, mapping 2, localisation 2, SLAM-in-the-loop 2, method 1.
- **Algorithm limits:** two (S6 the matcher's ±20° window, S7 rf2o's still-world assumption). The rest were
  configuration, launch order, data format, timing and method.
- **How we debugged:** state a hypothesis → measure on a recording → isolate offline → confirm live. Two
  hypotheses that looked right were wrong (S7 scale bug, S7 beam count); the live test settled both.
- **What it cost:** S7 and S8 together took three days (11-01 to 11-03), the longest single stretch.

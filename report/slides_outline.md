# CA3 presentation: slide outline (low-cost SLAM robot)

Status: **rewritten 2026-11-10 (night), v3**, structured on the group's section list: sensors → literature → the robot → pipeline → components → challenges overcome → why (analysis) → unexpected challenges → future work and learnings. Only work that ran on the robot goes on a slide. The delivery mission is dropped (not achieved).

Brief (NTULearn): 10-15 min + 5 min Q&A, Thu Week 13 9:30-12:30; overview, state of the art, product/paper comparison, brief technical information, future trends; **most importantly our insights**; videos/animations ≤ 2 min in total; slides and report due end of Week 13; peer assessment confidential.

Presenters: **A**, **B**, **MT** (motor teammate), **S** (Sherman). Names to fill in.

Rules (AGENTS.md): every number is *measured*, *fitted* or *brief default* and points to its test_log row or notes block; papers only from [`literature_notes.md`](literature_notes.md) (verified), products only with a source ("to check"); no live demo.

**Title:** *A Low-Cost Autonomous SLAM Robot: What It Took to Map a Room and Navigate It*
**Main claim:** the SLAM and navigation software came as packages and worked. Almost every lost day was integration: cheap sensors, a loaded computer, power, motors, and a person standing behind the robot.

## 1. Slide table

| # | Section | Time | Who | Headline (the claim) | Visual | Speaker notes (numbers with source) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Intro | 0:00-0:40 | A | We built a low-cost robot that maps a room and then drives itself around a box | Clip V1 (20 s) | - Pi 4B, RPLidar A1M8, MPU6050 IMU, two DC motors, **no wheel encoders**<br>- Roadmap of the talk in one line |
| 2 | Intro | 0:40-1:30 | A | SLAM: build a map and know where you are on it, at the same time | `map_build.gif` (8 s) then `odom_vs_slam.png` | - Odometry (how far did I move) drifts; scan matching against the map corrects it [R25], [MJ21]<br>- Left panel: odometry alone doubles walls where it drifts; right: slam_toolbox keeps them single<br>- Same loop as any autonomous vehicle: sense → localise → plan → act |
| 3 | Sensors | 1:30-2:20 | A | Two sensors: a spinning 2D lidar sees the room, an IMU feels the turns | Two cards: how each works, strengths, weaknesses | - Lidar: one plane, 360°, distance per ping; sees walls and legs, not tables above the plane; misses glass and dark surfaces<br>- IMU (gyro + accelerometer): fast (100 Hz) and good at turns, drifts over time; no position on its own<br>- Why both: lidar odometry is accurate but slow and fooled by moving things; gyro is fast and immune to the scene |
| 4 | Sensors vs literature | 2:20-3:20 | S | Our sensors are an order of magnitude cheaper and slower than the ones in the papers | Table: K26 / M26 / Y21 / ours: lidar, scan rate, IMU, wheel encoders, computer | - K26: Ouster OS-1 (3D, cut to 2D), Jetson on board but all results replayed on a desktop; **no wheel encoders**, rf2o + robot_localization + SLAM Toolbox: the same stack as ours<br>- M26: Hokuyo UTM-30LX, MicroStrain IMU, wheel encoders, PR2 dataset<br>- Y21: Hokuyo UTM-30LX at 40 Hz<br>- Ours (measured): A1M8 7.05 Hz, 26-29 % no-echo (C1); MPU6050 100 Hz, gyro z std 0.00175 rad/s at rest; Pi 4 at load 13-22 |
| 5 | Literature | 3:20-4:30 | S | What the papers found, and what our robot showed | Three rows, paper → our result; small `turn_gyro_vs_rf2o.png` | - M26: fusing the IMU cut odometry error 60-75 % before SLAM, ≈0 after. Ours: gyro reads a hand turn as 360.2°, lidar odometry 352.9° (2 % short), so the IMU carries the heading<br>- K26: SLAM Toolbox runs repeat within 0.20-0.23 m, measured by offline replay. Ours: replaying one recording three times gave 0.68 / 0.59 / 0.53 m on the Pi (C7), so we tested live<br>- Y21: people in the scan raise map error from 5.9 to 80 cm. Ours: a person behind the robot cut odometry to 25 % (C6)<br>- **Our take:** published numbers come from good sensors and desktop replays; a cheap robot has to be measured live |
| 6 | The robot | 4:30-5:15 | MT | The robot: off-the-shelf parts on a two-wheel base | Robot photo, labelled | - Pi 4B, A1M8 on top (2 cm ahead of centre, in the URDF), MPU6050, motor driver + 2 DC motors, motor battery, Pi power bank, USB camera (Foxglove only), motor switch = kill switch<br>- Cost: sum the BOM (to check) |
| 7 | Pipeline | 5:15-6:30 | MT | The pipeline: laser pings in, wheel commands out, and a watchdog in between | Block diagram with rates | - rplidar 7 Hz → rf2o lidar odometry → EKF (robot_localization, 20 Hz, + IMU 100 Hz) → slam_toolbox (map → odom) → Nav2 (planner, RPP controller, velocity smoother, collision monitor) → motor_node → PWM 100 Hz<br>- We wrote only motor node, IMU node, URDF, launch files and tools (D5)<br>- Safety: 0.5 s watchdog, lidar stop 0.20 m (tested at 0.155 m), stale-scan stop, motor switch<br>- Foxglove to watch, rosbag2 to record |
| 8 | Challenges | 6:30-6:55 | S | Three weeks, nine checkpoints, and the challenges that blocked them | `challenge_timeline.png` | - Left to right in one breath; the next three slides zoom into SLAM, then one into the robot<br>- Full evidence for every SLAM challenge: [`slam_challenges.md`](slam_challenges.md) |
| 9 | SLAM challenges I: a usable map | 6:55-7:55 | S | Our first map was a fan; loop closure is what made the second one usable | Left: `results/maps/2026-10-31_room2.png`; right: sweep table | - S1: one third of pings returned; the gaps follow glass and dark surfaces, so we mapped anyway; scan scale within 3.5 cm of tape<br>- S2: `LaserRangeScan contains 1041 range readings, expected 931`, 223 scans rejected, a 184 x 112 fan; `angle_compensate` on → 720 fixed beams → 317 x 233 room map, 0 rejections<br>- S3: no ground truth, so the gap between start and end of the lap on the taped mark became the metric: 0.109 m over 42 m with loop closure, **0.658 m without** (6x); froze that set<br>- S4: slam_toolbox stuck unconfigured (launch order), and a leftover process faked a pass: configure delayed 5 s, stale processes checked first |
| 10 | SLAM challenges II: odometry fooled | 7:55-9:10 | S | A person walking behind the robot made its odometry read a quarter of the distance | `oi8_person_behind.gif` (15 s); the 7-step table from `slam_challenges.md` S7 | - S7, three days, five hypotheses: broken odometry? scale bug (24 % in two places)? beam count (720 vs 1046)? CPU (replay at 0.25x reads the same)? Then counted points behind the robot: 127-152 at 0.35-0.9 m in bad bags vs 16-18 with a stick<br>- Fix shown offline: drop returns < 0.6 m → 99.5 %<br>- S8 on the way: three replays of one recording gave 0.68 / 0.59 / 0.53 m vs 0.96 m live → from then on, live tests only<br>- **Our take:** without encoders the lidar is the odometry, and anything moving with the robot fools it |
| 11 | SLAM challenges III: localisation in the loop | 9:10-10:00 | S | Localisation holds within 20° of the truth, and SLAM's timing, not its accuracy, broke navigation | Wrong-start table; small `turn_gyro_vs_rf2o.png` | - S5: `Starting localization at first node (dock) is correctly not supported` → `map_start_pose`<br>- S6: wrong start 30 cm / 20° recovers after a push, 31° never (matcher searches ±20°, matches only after 0.1 m of travel) → taped home mark; on the mark 2.6 cm scan-to-map<br>- S9: rf2o reports zero uncertainty → covariance relay and fitted variances; turn: gyro 360.2°, rf2o 352.9°<br>- S10: `Transform data too old when converting from map to odom` (0.37 s): slam_toolbox stamps by last scan, ≥ 0.5 s apart at Pi load 13-22 → `restamp_tf`, tolerance 0.5 s → `Goal succeeded`<br>- S11: home 0.21 m from an obstacle on the map → moved to 0.67 m clearance |
| 12 | Robot challenges | 10:00-11:00 | MT | Off the SLAM side: the wheels stall below 0.10 m/s, the battery lasts one run, and Nav2 failed until both were respected | `motor_curve.png` + `straights.png` | - C9: fit speed = 2.46 x (duty - 0.078); duty 0.10 stalls; kick 0.30 for 0.35 s; 1 kHz software PWM ran 2-3x fast under load → 100 Hz<br>- C13: 0.74 then 0.38 m on a fading battery; good runs 1.06 and 1.16 m<br>- C11: Pi under-voltage 67.5 % of samples → power bank 0 %<br>- C14 (non-SLAM rungs): server timeout 20 → 1000 ms; slowdown 0.045 m/s below the stall floor removed; turn and approach ≥ 0.10 m/s; reversing off |
| 13 | Why + unexpected | 11:00-11:50 | B | Why it was hard: almost every challenge was integration, and most were surprises | Root-cause bar (sections 7 and S-table) | - SLAM side (S1-S11): 2 algorithm limits (matcher window, rf2o still-world), the rest configuration, launch order, data format, timing, method<br>- Robot side (C8-C14): cheap hardware, a loaded Pi, silent mismatches (`Twist` vs `TwistStamped`, `dry_run` never passed on)<br>- Unexpected: the person (S7), the replays (S8), the silent failures, PWM under CPU load<br>- **Our take:** package defaults assume better hardware (K26 replayed on a desktop, M26 on a PR2), so every default had to be re-earned |
| 14 | Result | 11:50-12:50 | MT | It works: a goal 1.5 m away reached on its own, and a box driven around | Clip V2 (45 s, 2x) | - `Goal succeeded` after 93 s, (-1.35, -0.29) → (-2.67, 0.42) (`bt_navigator` log)<br>- Box about 1 m ahead, path about 3.0 m (**by eye, tape TBD**)<br>- 1 success of 6 goals that evening; the others cancelled by hand<br>- **Our take:** one success proves the loop closes, not that it is reliable |
| 15 | Future work + learnings | 12:50-13:50 | A | What we would do next, and what we learned | Two columns | **Future:** wheel encoders; a live range filter for people (`laser_filters`); hardware PWM; offload Nav2 or a faster computer; repeat runs, slam_toolbox vs AMCL; tests with people walking; camera + lidar fusion (trends: sourced only)<br>**Learnings:** design a ground truth when you have none (the taped loop); test live, not on replays; a test that can pass on a leftover process is not a test; measure physical limits (stall floor, power, CPU) on day one; make silent failures loud |
| 16 | Verdict | 13:50-14:15 | A | A low-cost robot can map a room with SLAM and navigate it on its own, once every physical limit is measured and designed around | One sentence, large type | Close on the claim; thank you; questions |
| B1 | Backup | Q&A | all | Stack, TF tree, frozen config | TF tree, key YAML values | If asked |
| B2 | Backup | Q&A | all | Every number with its command | Table from test_log | If asked |
| B3 | Backup | Q&A | S | OI-8 and replay in numbers | `oi8_and_replay_bars.png` | If asked |
| B4 | Backup | Q&A | S | Planner paths on the saved map | `results/maps/2026-11-08_planner_paths.png` | If asked |

Timing: 16 slides end at 14:15 (45 s slack). Per presenter: A 0:00-2:20 + 12:50-14:15 (3 min 45 s); S 2:20-4:30 + 6:30-10:00 (5 min 40 s); MT 4:30-6:30 + 10:00-11:00 + 11:50-12:50 (4 min); B 11:00-11:50 (50 s). S is heavy and B light: B can take slide 11 or 12 if B worked on it.

## 2. Video and animation budget (≤ 120 s)

| Clip | Slide | Seconds | Source |
| --- | --- | --- | --- |
| V1 around the box, best 20 s | 1 | 20 | 2026-11-10 box video |
| `map_build.gif` | 2 | 8 | `tools/analysis/slide_figs.py` |
| `oi8_person_behind.gif` | 10 | 15 | same |
| V2 full box run at 2x | 14 | 45 | box video |
| **Total** | | **88** | 32 s spare |

Local files, muted, captioned. No live demo.

## 3. Our take lines (≤ 20 words, fixed box at the bottom)

| Slide | Our take |
| --- | --- |
| 5 | Published numbers come from good sensors and desktop replays; a cheap robot has to be measured live. |
| 10 | Without encoders the lidar is the odometry, and anything moving with the robot fools it. |
| 13 | Package defaults assume better hardware, so every default had to be re-earned. |
| 14 | One success proves the loop closes, not that it is reliable. |

## 4. Gaps to close before rehearsal 1 (Wed 2026-11-11)

- [ ] Tape numbers for the box run (distance, sideways drift, box position and size); which launch it was
- [ ] Add the 2026-11-10 evening Nav2 runs to `docs/test_log.md` and a notes entry (slides 11, 14 cite them)
- [ ] Robot photo, labelled (slide 6); BOM cost (slide 6)
- [ ] Pipeline diagram (slide 7); base: [`../docs/img/pipeline-flow.png`](../docs/img/pipeline-flow.png)
- [ ] Root-cause bar for slide 13 (section 7 and `slam_challenges.md`)
- [ ] Sweep table and S7 step table as slide graphics (slides 9, 10)
- [ ] Sensor specs from datasheets (A1M8, MPU6050) if slide 3 quotes any; else measured values only
- [ ] Presenter names

## 5. Q&A prep

| # | Question | Draft answer |
| --- | --- | --- |
| 1 | Why only one successful goal? | The evening went on finding and fixing faults (slides 11, 12); once the loop closed we had a video and the battery gave about one run per charge. We claim the loop works, not a success rate. |
| 2 | Why no wheel encoders? | The kit did not have them; lidar odometry plus the IMU stood in, as in [K26]. OI-8 shows the cost, and encoders are first on the roadmap. |
| 3 | Why packages, not your own code? | D5: the brief allows them, and the hard part turned out to be integration anyway. Our own EKF and planner stay a documented fallback (`docs/system/07_ros_stack.md`). |
| 4 | Is a 2D lidar safe around people? | Not on its own: one plane only, 26-29 % no-echo on this unit. Mitigations: 0.15 m/s cap, 0.20 m lidar stop (tested), watchdog, physical kill switch. |
| 5 | How does this compare to a road AV? | Same SLAM loop, far smaller world: a mapped room at 0.15 m/s, 2D instead of 3D lidar. What transfers is the structure and the integration lessons. |
| 6 | What would you do differently? | Measure the motors' stall floor and the power supply on day one, and keep people out of the scan in odometry tests. Both cost days later. |
| 7 | Why did replay differ from live? | The Pi is CPU-bound; rf2o's work lands at different times on each replay (spread -12 %, about 71 % of live); slowing playback did not fix it. |
| 8 | Wasn't this meant to be a delivery robot? | It started as one. A delivery loop needs repeated goals and we reached one goal on the last evening, so we report what works: mapping, localisation and one navigation goal around an obstacle. |
| 9 | Did you replicate the papers? | No: our hardware and setup differ too much (slide 4). We compare directions: M26's IMU gain, K26's replay method, Y21's people effect, each against something we measured. |

## 6. Design notes

- One idea per slide; the headline is the claim, the figure its evidence, notes the rest.
- Figures carry no titles or source lines: the slide headline is the title, the source goes in one small footer line on the slide.
- Every number carries a provenance tag (*measured*, *fitted*, *brief default*, *by eye*).
- Fixed "Our take" box, same place on every slide that has one. Colour-blind-safe palette; captions on clips.

## 7. Key challenges and checkpoints

From `notes/notes.md`, `docs/test_log.md`, `docs/CA3.md` (OI-n) and `docs/system/06_troubleshooting.md`.

### Checkpoints reached

| Date | Checkpoint | Proof |
| --- | --- | --- |
| 2026-10-21 | Lidar bring-up on the first Pi | notes 2026-10-20/21 |
| 2026-10-22 | Stack decided: ROS 2 packages, not our own maths (D5); stack installed on the new Pi | notes 2026-10-22 "D5" |
| 2026-10-31 | CP0 platform up: robot built, lidar and IMU measured into the URDF | test_log 2026-10-30/31 |
| 2026-10-31 | First room map saved, SLAM settings frozen | `results/maps/2026-10-31_room2.png` |
| 2026-11-01 | CP1 localisation on the map, wrong start 30 cm / 20° recovers | test_log 2026-11-01 "6.4" |
| 2026-11-03 | CP2 OI-8 explained (person behind the robot) | `evidence/lidar/2026-11-03_oi8_*.txt` |
| 2026-11-09 | Motors live, lidar stop tested, first 1 m straight (0.96 m) | test_log 2026-11-09 |
| 2026-11-10 | CP5 robot drives: 2 of 3 straights; Pi power stable | test_log 2026-11-10 CP5 rows |
| 2026-11-10 | Nav2 goal succeeded (1.5 m, 93 s); robot drives around a box | `bt_navigator` log, video (test_log row to add) |

### Challenges

Root cause groups (slide 11): **HW** cheap hardware, **CPU** loaded computer, **IF** silent interface mismatch, **ENV** environment/algorithm assumption, **PL** platform/process. Expected = we planned for something like it; unexpected = slide 12.

| # | Date | Symptom | Root cause | How we found it | Fix / status | Group | Expected? | Slide |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | 10-21 | Lidar returns a distance for only a third of pings | Room surfaces (glass, dark): gaps move with the scene | White box test; near-return bins move between bags (OI-4) | Accepted; mapped anyway (26-29 % no-echo) | HW | yes | 4 |
| C2 | 10-22 | Brief's Pi offline; new Pi stopped answering SSH | Old box gone; new one set up from scratch | `tailscale status`, `nc -z` | Moved to `sherm-raspi` over Tailscale | PL | no | 8 |
| C3 | 10-22 | Plan said write our own EKF, A*, pure pursuit | Too much maths for the time | Decision review | D5: ROS 2 packages, our code is glue | PL | yes | 7 |
| C4 | 10-30 | slam_toolbox dropped every scan: `LaserRangeScan contains 1041 range readings, expected 931` | Varying beam count with `angle_compensate` off | Error text, beam counts per bag | `angle_compensate` true (720 beams) | IF | no | 11 |
| C5 | 11-01 | Launch looks up but no `/scan` | Lidar restarted too soon, or two launches overlapped | Repeated starts; process list | Wait 20 s, one launch at a time (OI-6) | HW | no | 8 |
| C6 | 11-01 to 11-03 | Odometry read 24-28 % of a hand push | A person behind the robot moved with it; rf2o assumes a still scene | Ruled out format, rate, CPU; counted points behind the robot | Explained; 0.6 m range cut fixes it offline (99.5 %) | ENV | no | 12 |
| C7 | 11-02 to 11-03 | Three replays of one recording: 0.679 / 0.592 / 0.531 m | Replay timing on a loaded Pi varies | Repeat replays at rates 1.0, 0.5, 0.25 | Test live; bags as evidence only | CPU | no | 5, 12 |
| C8 | 11-09 | Wheels would never move under Nav2, no error | Nav2 sent `Twist`, motor node expects `TwistStamped` | Nav2 source (`twist_subscriber.hpp`), `ros2 topic info -v` | `enable_stamped_cmd_vel: true` | IF | no | 12 |
| C9 | 11-09 | Curved 35-40°, would not start slowly, overshot 2-3x under load | Per-wheel gains; static friction; 1 kHz software PWM late under CPU load | Duty sweeps with the stack off, then loaded | PWM 100 Hz, refit, kick-start | HW, CPU | partly (PWM part no) | 9, 12 |
| C10 | 11-09 | Pi rebooted twice mid-run; wheels dead | Loose motor wire; battery sag | Uptime 1 min after each fault | Wire fixed; battery cycled (OI-9) | HW | yes | 9 |
| C11 | 11-09 to 11-10 | Nav2 shut down (`IS DOWN after not receiving a heartbeat`) | Pi under-voltage 67.5 % of samples, CPU throttled | `vcgencmd get_throttled` every 2 s | Power bank: 60 of 60 `0x0` (OI-10, OI-11) | HW, CPU | no | 9 |
| C12 | 11-10 | "Live" Nav2 runs drove nothing | `dry_run` not passed on; YAML default won | `ros2 param get /motor_node dry_run` = True | PR 42 | IF | no | 12 |
| C13 | 11-10 | Same command drove 0.84, 0.74, 0.38 m | Motor battery fades after one run | Successive runs | Cycle the battery each run | HW | yes | 9 |
| C14 | 11-10 | Nav2 goals aborted or crept, seven ways | Timeouts too short for the Pi, stale transforms, home near obstacles, speeds below the stall floor, reversing | Nav2 logs per goal, clearance map | Seven config fixes, then `Goal succeeded` | CPU, HW | partly | 10 |

Pattern: 1 of 14 is an algorithm assumption (C6); 13 are hardware, computer load, interfaces or process. 9 of 14 were unexpected. The SLAM challenges in full detail, with logs and step-by-step investigations: [`slam_challenges.md`](slam_challenges.md) (S1-S11).

## 8. Figures (no robot needed)

`.venv/bin/python tools/analysis/slide_figs.py` (bags in `../delivery_bot_pi_backup/bags`). Figures have no titles or source lines; sources below go in the slide footer. Bag-derived values match test_log: turn 360.2° / 352.9°, OI-8 wall 1.222 m vs rf2o 0.290 m, straights rf2o 0.741 / 0.386 / 1.088 / 1.175 m.

| Slide | File (`figures/2026-11-10_…`) | Footer source |
| --- | --- | --- |
| 2 | `map_build.gif`, `odom_vs_slam.png` | bag 2026-10-31_map_200956 |
| 5, 11 | `turn_gyro_vs_rf2o.png` | bag 2026-10-31_turn_194945; test_log 2026-10-31 "3.2 spin only" |
| 8 | `challenge_timeline.png` | notes, test_log, CA3.md OI list |
| 12 | `motor_curve.png`, `straights.png`, `power.png` | notes 2026-11-09 (late), PR 38; test_log 2026-11-10 CP5 rows, power sampler and gate |
| 10 | `oi8_person_behind.gif` (still `_last.png`) | bag 2026-11-01_push_230535; test_log 2026-11-03 |
| B3 | `oi8_and_replay_bars.png` | test_log 2026-11-03 OI-8 and replay rows |

Existing, reuse: `results/maps/2026-11-10_home_clearance.png` (slide 11), `results/maps/2026-10-31_room2.png` (slide 9), `results/maps/2026-11-08_planner_paths.png` (B4), `evidence/lidar/2026-10-21_composite_20revs.png` (slide 3 or 4).

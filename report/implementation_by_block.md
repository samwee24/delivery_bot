# Implementation, results and logs, block by block

Source for slides 2.1 and 3.1-3.7 (v5, pipeline order) and the report's Implementation and Results chapters. The robot is described along
its pipeline (`report/figures/pipeline.mmd`):

**0 Infrastructure → 1 Sense → 2 Odometry + fusion → 3 Map → 4 Localise → 5 Navigate → 6 Act**

Every block has the same parts: **purpose · what we built (files, nodes, topics, parameters with
provenance) · how we checked it (command → result) · results · logs as they appeared · challenges and fixes ·
tests that guard it · what we would change**. Numbers come with their source: *test_log date "first words"*
(`docs/test_log.md`), *notes date "block"* (`notes/notes.md`), a config file and line comment, or a commit.
Provenance tags: **measured** (on this robot), **fitted** (from measurements), **brief default**
(unmeasured), **by eye**. SLAM challenges S1-S11 are in full in [`slam_challenges.md`](slam_challenges.md);
robot challenges C1-C14 in [`slides_outline.md`](slides_outline.md) section 7.

---

## System at a glance

| | |
| --- | --- |
| Computer | Raspberry Pi 4B, Ubuntu 24.04.5, ROS 2 Jazzy; headless, reached over Tailscale |
| Sensors | RPLidar A1M8 (USB, `/dev/rplidar`), MPU6050 IMU (I2C bus 1, 0x68), USB camera (viewing only) |
| Actuators | 4 DC gear motors (four-wheel skid steer) through an L298N driver, left pair and right pair each wired to one channel, motor battery separate from the Pi's supply |
| No wheel encoders | Lidar odometry (rf2o) + gyro replace them |
| Packages (ours) | `delivery_bot_bringup` (launch, config), `delivery_bot_description` (URDF), `delivery_bot_drivers` (`imu_node`, `motor_node`), `delivery_bot_slam` (covariance relay, run/save, trajectory recorder), `delivery_bot_mission` (named goals, deliver script) |
| Packages (used as is, D5) | `rplidar_ros`, `rf2o_laser_odometry`, `robot_localization`, `slam_toolbox`, Nav2, `foxglove_bridge`, rosbag2 (MCAP) |
| Code we wrote | `imu_node.py` 154 lines, `motor_node.py` 298 (teammate's, safety fixes ours), `odom_covariance_relay.py`, `robot_control.py` 405, `run_cell.py` 163, `timed_move.py` 96, `motor_check.py` 105, plus launch files, URDF and ~20 analysis scripts in `tools/analysis/` (`wc -l`) |
| Tests | 188 test functions: drivers 32, mission 10, slam 60, tools 86 (`grep -c "^def test_"` per test folder); CI runs them on every PR with flake8 and pep257 |
| Dates | Built and measured 2026-10-21 to 2026-11-10 |

---

## Block 0 · Infrastructure: how we worked on a headless robot

**Purpose.** A headless Pi, a shared repo, and a safety rule that only the motor node moves the wheels.

**What we built.**
- **Repo and CI.** `main` is protected: every change is a PR titled `type: YYYY-MM-DD what`, squash-merged. CI
  job `repo-rules` enforces that `notes/notes.md` is append-only, `evidence/` is never edited, and no added line
  contains `dry_run:=false` outside markdown; `build-and-test` builds the packages in a ROS 2 Jazzy container
  and runs all tests plus flake8 and pep257. Rules in `AGENTS.md`; settings in `docs/system/08_github.md`.
- **Foxglove instead of a GUI.** `foxglove_bridge` on port 8765; layouts in `docs/foxglove/`
  (cockpit layout with a status strip).
- **`tools/robot_control.py`** (Foxglove buttons, runs at boot via `robot-control.service`): services
  `/stack/base|mapping|localisation|navigation|stop`, `/bag/start|stop` (with `bag_label`, `bag_topics`
  parameters), `/camera/*`, `/stream/*`, `/pi/shutdown|reboot`; publishes `/robot/status/*` at 1 Hz (stack,
  video, bag, `throttled`, under-voltage, CPU temperature, load). Every stack runs in its own process group and is
  stopped SIGINT → SIGTERM → SIGKILL, so the MCAP file closes and PWM is zeroed. It never passes
  `dry_run:=false` and never touches `/cmd_vel`.
- **`tools/run_cell.py`**: starts one experiment cell, records the bag, prints the test_log row; refuses to
  overwrite an existing bag. **`tools/timed_move.py`**: a timed straight or spin through the collision monitor.
  **`tools/motor_check.py`**: a direct duty test before a block of runs. **`tools/demo_tmux.sh`**: three tmux
  panes (stack, robot-frame goal, live map pose) typed but not run.
- **Recording.** rosbag2 MCAP; bags `~/bags/YYYY-MM-DD_<what>`; backed up to the Mac with
  `rsync -a robot@100.83.14.99:bags/ ../delivery_bot_pi_backup/bags/` (test_log 2026-11-10 "rsync").

**Results.**
| Check | Result | Source |
| --- | --- | --- |
| `/stack/mapping` twice | `pass after 15 s`, `pass after 16 s`; one lidar, EKF, bridge and slam_toolbox each | test_log 2026-11-02 "/stack/mapping called twice" |
| `/stack/stop` | `stack stopped; killed strays []`; 0 lidar/EKF/slam_toolbox left | test_log 2026-11-02 "/stack/stop" |
| Bag with markers | `2026-11-02_121451_push5`, 21.48 s, 2753 messages, 2 markers | test_log 2026-11-02 "bag_label push5" |
| `run_cell.py` refusal | exit 1, `refusing: .../2026-11-09_E3_amcl_empty_run99 exists`, 0 processes started | test_log 2026-11-09 "live 5" |
| Camera | 1280x720 at 10 fps to Foxglove (MJPEG decode on one core caps 1080p30 at 4.5 Hz) | notes 2026-10-31 (night); troubleshooting |

**Challenges → fixes.**
- A launch backgrounded with `nohup ... &` ignores SIGINT, leaves the lidar spinning and the next start gets no
  `/scan` → rule: start in the foreground, stop with SIGINT (AGENTS.md conventions).
- `pkill -f <pattern>` over ssh matched the ssh command itself and killed the session (`exit 255`) → put
  `pkill` in a script file (troubleshooting).
- The first `/stack/*` check used a fixed 8 s wait and reported FAIL on a stack that was still starting (needs
  9-16 s) → poll until the processes exist (test_log 2026-11-02).
- Two launches overlapping stopped the lidar motor (rf2o `Waiting for laser_scans....`) → one launch at a time,
  wait 20 s; recovery `ros2 service call /start_motor std_srvs/srv/Empty "{}"` (handover 2026-11-10).

---

## Block 1 · Sense: lidar and IMU

**Purpose.** Turn the room into distances (lidar) and the robot's turning into a rate (gyro), at known
positions on the robot.

**What we built.**
- **Lidar** (`delivery_bot_bringup/launch/lidar.launch.py`): `rplidar_ros` `rplidar_composition`,
  `serial_port` `/dev/rplidar` (udev symlink), 115200 baud, `frame_id` `laser`, **`angle_compensate: true`** (720
  fixed beams; see S2). Model 24 = A1M8, firmware 1.29, health `Good` (notes 2026-10-20/21).
- **IMU** (`delivery_bot_drivers/imu_node.py`, ours, 154 lines): reads the MPU6050 over I2C (bus 1, 0x68) at
  100 Hz; DLPF ~44 Hz, ±250°/s (131 LSB per °/s), ±2 g. At start it averages the gyro for 3 s and **refuses
  to start** if gyro z std exceeds 0.01 rad/s (robot moving); service `~/recalibrate` repeats it.
  Publishes `/imu/data` with bias removed, `gyro_scale_z` applied, `orientation_covariance[0] = -1` (no
  orientation estimate: the EKF must not fuse an integrated yaw).
- **Mounting in the URDF** (`delivery_bot_description/urdf/delivery_bot.urdf.xacro`), all measured 2026-10-31
  with a tape: laser x 0.02, y 0, z 0.12 m, yaw 0; IMU x 0.023, y -0.055, z 0.07 m; wheel base 0.156 m (measured);
  wheel radius 0.0325 m (brief default).

| Parameter | Value | Provenance |
| --- | --- | --- |
| `angle_compensate` | true | fixed after S2 (2026-10-31) |
| `rate_hz` (IMU) | 100 | brief default; measured 100.04 Hz |
| `calib_seconds`, `calib_max_std` | 3.0 s, 0.01 rad/s | brief default; measured trips at 0.0211-0.0278 when moved |
| `gyro_scale_z` | 1.0 | **measured**: hand turn 360.2° for 360° (0.06 %) |
| `gyro_var` | 1e-4 (rad/s)² | **fitted** 1.7e-6 at rest, x60 margin for motor vibration |
| `laser_yaw` | 0 | box test: face at +2.6° and +6° by eye, inside placement error |

**How we checked it.**
| Test | Command | Result | Source |
| --- | --- | --- | --- |
| Lidar first light | `get_info()`, `get_health()`, `test_lidar.py`, `probe_echo_rate.py` | A1M8, 4.9-6.9 Hz, 95-105 returns per revolution, echo rate 33-35 % over 3 runs, max range 8.5-8.7 m | notes 2026-10-20/21 |
| Lidar on the robot Pi | rates and no-echo count | 7.05 Hz, 26-29 % no-echo | docs/CA3.md OI-4, AGENTS.md |
| Gaps follow the room | near-return (< 0.30 m) bins per 30° over 3 bags | bins move 0-60°, 30-120°, 90-180° with the scene | notes 2026-10-30 "near-return ring is the room" |
| Lidar orientation | box test (task 1.4), `/scan` ±40° | box on +x, centred +2.6° / +6°: `laser_yaw` 0 holds | notes 2026-10-30 "1.4 box test"; URDF comment |
| Scale vs tape | 3 × `ros2 topic echo /scan --once`, median ±3° (`lr.sh`) | 1.085 m vs tape 1.05 m (+3.5 cm); 1.494 m vs 1.48 m (+1.4 cm) | test_log 2026-10-31 "5.4 scale check" |
| IMU at rest | `ros2 topic hz /imu/data --window 200`; 15 s echo | **100.04 Hz**; gyro bias x -0.0260, y -0.0053, z -0.0279 rad/s; z std 0.00175 rad/s | test_log 2026-10-30 "IMU at rest" |
| IMU recalibrate | `/imu_node/recalibrate`, robot still | `gyro bias rad/s x=-0.02706 y=-0.00610 z=-0.02585` | test_log 2026-11-02 |
| Whole base stack | `base.launch.py`, `ros2 topic hz` each | `/scan` 6.92 Hz, `/imu/data` 99.1 Hz, `/odom_rf2o_cov` 7.33 Hz, `/odometry/filtered` 19.93 Hz | test_log 2026-11-01 "base.launch.py on the Pi" |

**Ping level vs published scan.** The 26-29 % no-echo is counted per ping. The `/scan` message the driver publishes (720 beams with `angle_compensate`) shows only 5.8-11 % empty beams, because 20-31 % of its beams are copies of a neighbouring range (test_log 2026-11-03 "OI-8 beam-format stats, 720-beam bags"; `tools/analysis/beamstats.py`). Figure `2026-11-11_scan_gaps.png` shows one mid-lap scan on the room map at its SLAM pose: 9.3 % of directions return nothing, and the returns land on the map's walls.

**Results.** The lidar spins at 7 Hz and returns a distance for about three quarters of its pings in this room;
its scale is right within 3.5 cm; the gyro is quiet at rest (std 0.00175 rad/s) and accurate on a full turn
(0.06 %). Figure: `evidence/lidar/2026-10-21_composite_20revs.png`.

**Logs.**
```
Permission denied opening /dev/ttyUSB0                       -> user not in dialout (fixed P0)
RPLIDAR running on ROS 2 package   (no "RPLIDAR S/N" after)  -> restarted too soon (OI-6)
imu_node: gyro z std 0.0211 rad/s during calibration exceeds calib_max_std; keep the robot still and restart
Foxglove: '57 Infinity invalid values detected' on /scan     -> no-echo beams, harmless
```

**Challenges → fixes.** S1 one third of pings (accepted: the room) · S2 varying beam count (`angle_compensate`)
· C5 start hang (wait 20 s; one launch at a time) · the lidar keeps spinning after the driver stops (the USB
adapter's DTR line drives the motor) → `tools/streams/lidar_off.py` or `/stop_motor` · IMU calibration trips
when the robot is touched → hold still 3 s at every start.

**Tests.** `delivery_bot_drivers/test/` (IMU node maths and parameters); `tools/tests/test_beamstats.py`,
`test_scanchk.py`, `test_scan_minrange.py` (scan analysis).

**What we would change.** A lidar with a higher scan rate and fewer dropouts; a datasheet check of the
A1M8's quoted range and rate (not yet in the repo).

---

## Block 2 · Odometry + fusion: rf2o, covariance relay, EKF

**Purpose.** Without wheel encoders, estimate how the robot moved between scans (lidar odometry), fuse it
with the gyro, and publish the single `odom → base_footprint` transform.

**What we built** (`delivery_bot_bringup/launch/base.launch.py`).
- **rf2o** [J16] (`rf2o_laser_odometry`, pinned b38c68e): `/scan` → `/odom_rf2o`, `freq` 20, `publish_tf:
  false`, base frame `base_footprint`. Started **2 s after** the rest (`TimerAction`), because rf2o reads the
  `base_footprint → laser` transform once, on its first scan (startup race, task 3.4: 10 of 10 clean starts with
  the delay, test `tools/startup_race.sh 10 2.0`).
- **`odom_covariance_relay`** (ours, `delivery_bot_slam`): rf2o leaves `twist.covariance` all zero;
  robot_localization turns zero into 1e-9, so rf2o would look perfect and drown the gyro. The relay rewrites
  only the covariance: `vx_variance` 1e-4, `vyaw_variance` 5e-3, everything else 1e3 ("do not fuse"), and
  republishes on `/odom_rf2o_cov` (`delivery_bot_slam/config/odom_covariance.yaml`).
- **EKF** (`robot_localization` `ekf_node`, `config/ekf.yaml`): 20 Hz (was 30, missed its rate under camera
  load), `two_d_mode`, `world_frame` odom; fuses **rf2o vx and vyaw** (`odom0_config` index 6 and 11) and **gyro
  yaw rate** (`imu0_config` index 11). The EKF alone publishes `odom → base_footprint` (two publishers of one
  transform make the map spin; AGENTS.md).
- **Switchable variants** for the planned odometry comparison: `config/ekf_variants/rf2o_imu.yaml`,
  `rf2o_only.yaml`, `imu_only.yaml`, and `ekf:=false` (identity transform), selected with
  `ekf_params_file:=` (PR 33; smoke-tested, test_log 2026-11-09 "smoke 2", "smoke 3").

| Parameter | Value | Provenance |
| --- | --- | --- |
| rf2o `vx_variance` | 1e-4 (m/s)² | **fitted**: 1.1e-5 / 4.7e-6 at rest + 3.8 % push under-read at 0.15 m/s, rounded up |
| rf2o `vyaw_variance` | 5e-3 (rad/s)² | **fitted**: 8.5e-4 / 1.8e-3 at rest + 9-15 % under-read scaled to 0.4 rad/s; ~3000x the gyro's, so the gyro leads |
| gyro variance | 1e-4 (rad/s)² | **fitted**: 1.7e-6 at rest, x60 for vibration |
| EKF `frequency` | 20 Hz | measured: 19.93 Hz delivered |
| rf2o start delay | 2.0 s | measured: startup race 10/10 clean |

**How we checked it.**
| Test | Command | Result | Source |
| --- | --- | --- | --- |
| Relay | `ros2 topic echo /odom_rf2o_cov --once --field twist.covariance` | idx0 1e-3, idx35 4e-3 (placeholders then), others 1e3; 7.06 Hz = rf2o rate | test_log 2026-10-30 "4.3 relay" |
| Hand turn, 360° | `rf2o_alone.launch.py` + `imu_node`, bag `2026-10-31_turn_194945`, `turn_an.py` | **rf2o -352.9°, gyro -360.2°**; rf2o -2.0 %, gyro 0.06 %; rf2o within 1° for 90 s at rest | test_log 2026-10-31 "3.2 spin only" |
| 1 m push, nobody behind | `push_an.py ~/bags/2026-10-31_push_195343 39 50` | **0.962 m**, yaw -1.3° | test_log 2026-11-02 "same window by bag receive time" |
| Variances | `var_an.py` on the turn and push bags | rest: rf2o vx 1.1e-5 / 4.7e-6, wz 8.5e-4 / 1.8e-3, gyro 1.7e-6; moving: rf2o/gyro slope 0.91 / 0.85 | test_log 2026-10-31 "4.4 variances" |
| Stick pushes, live | `pushwall.py` on `2026-11-03_135611_push_actrue`, `..._140352_push_acfalse` | rf2o **1.008** of 1.00 m and **0.961** of 1.01 m | test_log 2026-11-03 "OI-8 live push A/B" |
| Person behind | `pushwall.py` on `2026-11-01_push_225752` and `_230535` | rf2o **0.242 of 0.862 m (28 %)** and **0.307 of 1.222 m (25 %)**; 127 and 152 rear points vs 16-18 | test_log 2026-11-03 "bad bags re-read" |
| Fix, offline | `MINR=0.6 rf2o_fmt.sh ... minrange` | 0.291 → **1.216 m of 1.222 (99.5 %)** | test_log 2026-11-03 "offline fix test" |
| Replay repeatability | `rf2o_rate.sh <good bag> orig 39 50 1.0` ×3 | **0.679 / 0.592 / 0.531 m** vs 0.962 live; rate 0.5: 0.689; 0.25: 0.681 | test_log 2026-11-03 "replay repeatability" |
| Driven straights | `timed_move.py straight --speed 0.15`, bags `2026-11-10_CP5_straight_run2-5` | rf2o 0.741 / 0.386 / 1.088 / 1.175 m vs tape 0.74 / 0.38 / 1.06 / 1.16 m: **within 3 cm of tape** forward | test_log 2026-11-10 CP5 rows; `slide_figs.py` |

**Results.** With nobody near, lidar odometry reads 96-101 % of a straight push and 98 % of a full turn; the
gyro reads a turn to 0.06 %. Driven, rf2o's forward distance agrees with the tape within 3 cm (its sideways
number does not, so we use the tape for drift). A person walking behind the robot cuts the reading to a quarter.
Figures: `turn_gyro_vs_rf2o.png`, `oi8_person_behind.gif`, `oi8_and_replay_bars.png`, `straights.png`.

**Logs.**
```
rf2o: Waiting for laser_scans....                         -> lidar motor stopped by an overlapping launch
EKF: Failed to meet update rate                           -> 30 Hz under camera load; set 20 Hz
EKF: Failed to get parameters: parameter 'imu1' is not initialized   (every 15 s, benign)
rf2o: Publisher already registered                         -> a second rf2o still running
```

**Challenges → fixes.** S7 person behind (explained; range cut works offline) · S8 replays disagree (test live)
· S9 zero covariance (relay, fitted variances) · startup race (2 s delay) · fast turns read 9-15 % low ([S23]
scan skew a likely part; hypothesis).

**Tests.** `delivery_bot_slam/test/test_odom_covariance_relay.py` (relay behaviour), `test_config_consistency.py` (config consistency: EKF inputs, rf2o `publish_tf`
false); `tools/tests/test_push_an.py`, `test_turn_an.py`, `test_var_an.py`, `test_bag_summary.py`.

**What we would change.** Wheel encoders; a live `laser_filters` range filter (0.6 m) or people tracking
[Y21] before rf2o; de-skew the scan [S23].

---

## Block 3 · Map: slam_toolbox mapping mode

**Purpose.** Build the room map once, to reuse on every run.

**What we built.**
- **`mapping.launch.py`**: base stack + `async_slam_toolbox_node` with `slam_mapping.yaml`; lifecycle driven by
  the launch file itself (`use_lifecycle_manager: false`): configure after a 5 s `TimerAction`, then activate
  (fix for S4).
- **`slam_mapping.yaml`** (frozen after the sweep, S3): Ceres solver, `resolution` 0.05 m (matches the Nav2
  costmaps), `min_laser_range` 0.15, `max_laser_range` 8.0 (A1M8 useful range ~8.5 m), `minimum_travel_distance`
  0.1 m, `minimum_travel_heading` 0.1 rad, `do_loop_closing` true, `loop_search_maximum_distance` 3.0 m,
  `loop_match_minimum_chain_size` 10, `correlation_search_space_dimension` 0.5 m at 0.01 m,
  `transform_publish_period` 0.02 s.
- **Procedure.** Robot pushed by hand (motors not ready then) round the room from a taped start mark and back;
  bag `~/bags/2026-10-31_map_200956` (473 s); saved with `ros2 run nav2_map_server map_saver_cli -f
  ~/maps/2026-10-31_room2` (image for Nav2) and slam_toolbox `serialize_map` to `~/maps/2026-10-31_room2_graph`
  (pose graph for localisation).
- **`delivery_bot_slam/run_save.py`** and the Foxglove `/run/save` service save both forms in one call;
  `trajectory_recorder.py` writes TUM trajectories (`/slam/path`, `/odom/path`) for evo.

**How we checked it.**
| Test | Command | Result | Source |
| --- | --- | --- | --- |
| First map | `slam_replay.launch.py` live, bag `..._map_200956`, `map_saver_cli` | `~/maps/2026-10-31_room` a **184 x 112 fan**, 223 scans rejected (S2) | test_log 2026-10-31 "5.4 room map" |
| Second map | same, `angle_compensate` on | **317 x 233 cells** at 0.05 m, **65.5 m² free**, 4375 occupied | same row; `results/maps/2026-10-31_room2.png` |
| Scale | tape vs scan vs map | map 1.00 m vs tape 1.05 m (one 5 cm cell) | test_log 2026-10-31 "5.4 scale check" |
| Parameter sweep | `sweep.sh` replay, one change per variant, `sweep_an.py` | start-end gap over 42 m: base **0.109 m**, `min_laser_range` 0 0.123, **loop closing off 0.658**, travel 0.05 0.186, travel 0.2 0.113; 0 scans rejected | test_log 2026-10-31 "5.5 sweep" |
| Repeat | `ekf20.sh`, same replay | 0.115 m over 41.0 m, 943 poses; ~1 cm run-to-run noise | test_log 2026-11-01 "EKF 20 Hz check" |
| Live mapping launch | `mapping.launch.py`, 80 s, `lifecycle get`, `map_saver_cli` | slam_toolbox active with no manual steps | test_log 2026-11-01 "5.3 live, clean rerun" |
| Odometry only vs SLAM | `slide_figs.py`: scans placed by `odom → base` vs `map → odom → base` | odometry alone doubles walls at the bottom; SLAM keeps them single | `report/figures/2026-11-10_odom_vs_slam.png` |

**Results.** One 7-minute pushed lap gave a 317 x 233-cell (15.9 x 11.7 m bounding box) map with 65.5 m² of free
space. Loop closure cut the start-end gap from 0.658 m to 0.109 m over a 42 m lap (0.26 % of distance).
Figures: `map_build.gif`, `odom_vs_slam.png`, `results/maps/2026-10-31_room2.png`.

**Logs.**
```
LaserRangeScan contains 1041 range readings, expected 931                       (S2, 223 times)
Failed to make transition 'TRANSITION_CONFIGURE' for LifecycleNode '/slam_toolbox'   (S4)
Message Filter dropping message: frame 'laser' ... queue is full                (replay under load)
```

**Challenges → fixes.** S2 fan map (`angle_compensate`) · S3 no ground truth (start-end gap on a taped mark) ·
S4 lifecycle race and a faked pass (5 s configure delay; check stale processes) · replay with
`--start-offset` skipped `/tf_static` and every scan was dropped → always play from the start
(troubleshooting).

**Tests.** `delivery_bot_slam/test/test_launch_files.py`, `test_trajectory_recorder.py`,
`test_config_consistency.py` (resolution matches the costmaps, frames); `tools/tests/test_sweep_an.py`,
`test_gap.py`.

**What we would change.** Map with the motors at a steady speed rather than by hand; a second pass to fill the
tape gap (task 5.4 left open); score maps with a published metric [F17].

---

## Block 4 · Localise: slam_toolbox localisation mode

**Purpose.** On every run, find the robot on the saved map and publish `map → odom`.

**What we built.**
- **`navigation.launch.py`** with `localizer:=slam` (default): `localization_slam_toolbox_node` with
  `slam_localization.yaml`, `map_file_name` = the saved pose graph (`~/maps/2026-10-31_room2_graph`, no
  extension), **`map_start_pose: [-1.3, -0.3, 2.635]`** (the taped home mark; S5, S11).
- **`slam_localization.yaml`**: `mode: localization`, **`restamp_tf: true`** (S10), `scan_buffer_size` 3,
  `loop_match_minimum_chain_size` 3, `loop_search_space_dimension` 8.0 m, other matching settings as mapping.
- **Alternative localiser** `localizer:=amcl`: `nav2_amcl` + `map_server` on the same map (`config/amcl.yaml`,
  initial pose = the home mark); built and smoke-tested for a comparison we did not get to run.
- **Home pose kept in one place by test**: `navigation.launch.py` `map_start_pose`, `amcl.yaml` `initial_pose`
  and `delivery_bot_mission/config/goals.yaml` `home` must agree
  (`test_amcl_frames_and_initial_pose`).
- **Foxglove pose estimate**: `/initialpose` from the 3D panel re-seats the robot (task 6.3).

**How we checked it.**
| Test | Command | Result | Source |
| --- | --- | --- | --- |
| Starts and loads the graph | `navigation.launch.py`, `tf2_echo map odom`, `map_saver_cli` | `Load From File .../2026-10-31_room2_graph.posegraph`; `map → odom` 0.008, 0.070 m, 1.1°; 317 x 233 saved | test_log 2026-11-01 "6.2 headless" |
| Live scan on map | Foxglove, display frame `map` | scan points on the map walls; pose stable to 1 mm and 0.002 rad over three reads | test_log 2026-11-01 "6.2 live" |
| Pose estimate | Foxglove `Publish pose estimate` | robot re-seated after being carried | test_log 2026-11-01 "6.3 pose estimate" |
| Wrong start 30 cm / 20° | `t64.sh` restart off the mark, push 0.5-1 m | **recovers**: `map → odom` 0.352 m, -18.2° | test_log 2026-11-01 "6.4 ... 30 cm / 20 deg" |
| Wrong start 30 cm / 31° | same | **does not**: heading ~37° wrong, position right | test_log 2026-11-01 "6.4 ... 31 deg" |
| Wrong start 60 cm / 30° | same | does not (heading ~37° off) | test_log 2026-11-01 "6.4 wrong start, one case" |
| On the mark, two localisers | `pose.sh slam 1`, `amcl 1`, ... | slam_toolbox 0.049 and 0.087 m from (0, 0) (yaw 8.2°, 4.7°); AMCL sits on its initial pose | AGENTS.md "Live switches"; test_log 2026-11-09 "live 1" |
| New home mark | localisation-only run, `/tmp/loc_check.py` 25 s | **(-1.302, -0.307, 149.1°)** vs (-1.3, -0.3, 151°); scan-to-map median **2.6 cm**, 77-80 % of points within 10 cm | notes 2026-11-10 "home mark moved"; handover |

**Results.** Started on the taped mark, the robot localises to about 1 cm and 2° and its scan sits 2.6 cm
(median) from the map. It recovers a wrong start up to 30 cm / 20° after a short push, not 31°. Figures:
`results/maps/2026-11-01_room2_home_pose.png`, `results/maps/2026-11-10_new_home.png`.

**Logs.**
```
Starting localization at first node (dock) is correctly not supported           (S5)
Transform data too old when converting from map to odom                         (S10)
```

**Challenges → fixes.** S5 dock start rejected (`map_start_pose`) · S6 the matcher's ±20° window (taped home
mark) · S11 old home 0.21 m from an obstacle (new home with 0.67 m clearance, three configs kept equal by test)
· S10 `map → odom` stale under load (`restamp_tf`).

**Tests.** `delivery_bot_slam/test/test_config_consistency.py`: `test_amcl_frames_and_initial_pose`,
`test_localization_restamps_map_to_odom`.

**What we would change.** Measure heading on the mark with a protractor (not yet done); run the slam_toolbox vs
AMCL comparison the switches were built for.

---

## Block 5 · Navigate: Nav2

**Purpose.** Plan a path on the map to a goal and follow it at a safe speed, stopping for obstacles.

**What we built** (`navigation.launch.py`, `config/nav2_params.yaml`).
- **Planner**: `NavfnPlanner` (Dijkstra, `use_astar` false), tolerance 0.5 m, on the global costmap (static map
  + obstacle layer + inflation 0.25 m, robot radius 0.12 m measured approx).
- **Controller**: Regulated Pure Pursuit at 10 Hz: `desired_linear_vel` **0.15** (the motor cap),
  lookahead 0.2-0.4 m, `min_approach_linear_velocity` **0.10**, `regulated_linear_scaling_min_speed` **0.10**,
  rotate to heading at **1.6 rad/s** (0.125 m/s per wheel) for errors over 60°, `allow_reversing` false,
  `transform_tolerance` **0.5**.
- **Checkers**: progress 0.5 m in 10 s; goal xy tolerance 0.10 m, yaw tolerance 3.14 (any final heading).
- **Velocity smoother** 20 Hz, open loop: max [0.15, 0, 1.6], min [-0.12, 0, -1.6].
- **Collision monitor** between smoother and motors (`cmd_vel_smoothed → cmd_vel`): **stop** triangle 0.20 m
  ahead ±35°, **approach** circle 0.12 m with 1.5 s to collision; slowdown zone removed (below the stall floor);
  `transform_tolerance` **0.5**.
- **Timing for the Pi**: `default_server_timeout` **1000 ms** (was 20), costmap and behaviour-server
  `transform_tolerance` 0.5, `bond_timeout` 10 s.
- **`enable_stamped_cmd_vel: true`** on every node that sends or takes velocity (C8).
- **Mission layer**: `delivery_bot_mission` (`goals.yaml` named poses in the map frame, `save_goal.py`,
  `deliver.py` visits goals then returns home; not run live).
- **Every fix is guarded by a config test** in `delivery_bot_slam/test/test_config_consistency.py`
  (e.g. `test_nav2_commands_clear_wheel_stall_floor`, `test_nav2_reverse_clears_wheel_stall_floor`,
  `test_nav2_goal_accepts_any_heading`, `test_nav2_transform_tolerances_cover_slam_lag`).

**How we checked it: the goal history.**
| Date / commit | Goal | What happened | Cause → fix | Source |
| --- | --- | --- | --- | --- |
| 11-08 f329b4c | planner only, saved map, no controller | paths drawn on the map | planner works offline | test_log 2026-11-08; `results/maps/2026-11-08_planner_paths.png` |
| 11-09 917f9eb | `/cmd_vel` type | Nav2 sent `Twist`, motor node takes `TwistStamped` | `enable_stamped_cmd_vel` (C8) | notes 2026-11-09 "TwistStamped" |
| 11-10 34519a4 | live run | `dry_run` True, `dry run: no GPIO`, nothing moved | `dry_run` not forwarded (C12, PR 42) | test_log 2026-11-10 "blocked" |
| 11-10 d501f84 | (1, 0) from (0.06, -0.08) | `ABORTED` after 8 s, not moved: `Timed out while waiting for action server to acknowledge goal request for compute_path_to_pose` 32 ms after start; load 18 | `default_server_timeout` 20 → 1000 ms | test_log 2026-11-10 "Nav2 goal" |
| 11-10 dd93406 | (1, 0) | moved x 0.07 → 0.37, `ABORTED`, `error_code: 102`, `Lookup would require extrapolation into the future` | `FollowPath` `transform_tolerance` 0.1 → 0.5 | test_log 2026-11-10 "live goal to (1, 0)" |
| 11-10 d36ee58 | (1, 0) | `Failed to make progress`; collision monitor `Robot to stop due to invalid source` | home 0.21 m from an obstacle; slowdown 0.045 m/s below stall | test_log 2026-11-10; notes "home mark moved" |
| 11-10 cd44057 | (-2.175, 0.185) from new home | aborted 2.5 s in: `Transform data too old when converting from map to odom` (0.37 s) | costmap/behaviour tolerance 0.5; `restamp_tf` (42f0f83) | handover 2026-11-10 |
| 11-10 f9bf16e, 56765eb | — | slowdown zone removed; turn and approach ≥ 0.10 m/s | stall floor | commits |
| 11-10 e146e98 → b6598b5 | — | with reversing allowed it drove backwards to goals; reverted | `allow_reversing` false | commits |
| 11-10 c657b1e | — | the final turn to heading stalled and aborted goals | any final heading | commit |
| 11-10 evening | (-2.67, 0.42) from (-1.35, -0.29) | **`Goal succeeded` after 93 s** (1.50 m) | — | `~/.ros/log/bt_navigator_7359_*.log` |
| 11-10 evening | box ~1 m ahead | drove around it (video); path ~3.0 m by eye | — | video; tape TBD |
| 11-10 evening | five more goals, 2.0-2.5 m | cancelled by hand after 22-104 s, still re-planning each second | not analysed | `bt_navigator_{1638,2673,3115,3503,7930}` logs |

**Results.** From the home mark the robot planned and drove a 1.5 m goal on its own in 93 s and drove around a
box placed about 1 m ahead. One success of six goals that evening; the other five were cancelled by hand.

**Logs** (in order of appearance on 2026-11-10).
```
[bt_navigator]: Timed out while waiting for action server to acknowledge goal request for compute_path_to_pose
[controller_server]: Exception in transformPose: Lookup would require extrapolation into the future.
[controller_server]: Failed to make progress
[collision_monitor]: Failed to get "laser"->"base_footprint" frame transform: Lookup would require extrapolation into the future
[collision_monitor]: Robot to stop due to invalid source
[tf_help]: Transform data too old when converting from map to odom
[controller_server]: Unable to transform robot pose into global plan's frame
CRITICAL FAILURE: SERVER bt_navigator IS DOWN after not receiving a heartbeat for 10000 ms   (heavy monitoring)
[bt_navigator]: Goal succeeded
```

**Challenges → fixes.** C8 message type · C12 `dry_run` · C14 the seven-step ladder above · S10 SLAM timing ·
OI-10 Nav2 shutting down on its heartbeat at load 20-30 (power supply, then `bond_timeout` 10 s; keep monitoring
light: five `ros2 topic echo` processes at load 16 took Nav2 down).

**Tests.** `test_config_consistency.py` (stamped velocity everywhere, tolerances, stall floor, reversing, goal
heading, home pose), `tools/tests/test_launch_dry_run.py` (`dry_run` reaches the motor node),
`delivery_bot_mission/test/`.

**What we would change.** Repeat runs to get a success rate; read why the five later goals did not finish;
offload Nav2 or use a faster computer (load 13-22 on the Pi).

---

## Block 6 · Act: motor node, motors and power

**Purpose.** Turn velocity commands into wheel PWM, and be the only thing that can move the robot.

**What we built.**
- **`motor_node.py`** (written by the motor teammate; safety fixes by us in PR 34, calibration in PR 38):
  subscribes `/cmd_vel` (`TwistStamped`); 20 Hz loop splits v and w into wheel speeds
  (`v ∓ w × wheel_base / 2`, wheel base 0.156 m), duty = `min_duty + gain × |speed|`, clamped to `max_duty`
  0.85; L298N pins ENA 12 / IN1 5 / IN2 6, ENB 13 / IN3 26 / IN4 16 via gpiozero + lgpio.
- **Kick-start**: a wheel starting from rest gets duty 0.30 for 0.35 s (static friction).
- **Safety contract** (AGENTS.md rule 1): `dry_run` true by default (no GPIO opened); command older than 0.5 s →
  stop; **lidar stop** zeroes forward speed if a return under 0.20 m lies within ±35° of travel (turning still
  allowed); no `/scan` for 0.5 s → stop; Ctrl+C or any exception → `stop_all()` zeroes PWM. The physical motor
  switch is the kill switch.
- **Power**: Pi on a power bank (wall supply under-voltage, C11); motor battery separate, power-cycled between
  runs (C13).

| Parameter | Value | Provenance |
| --- | --- | --- |
| `pwm_hz` | 100 | **measured**: 1 kHz software PWM 0.85 m idle vs 1.46 m at 33 runnable threads; 100 Hz 0.90 m both |
| `min_duty`, `gain` | 0.08, 0.41 (both wheels) | **fitted**: speed = 2.46 x (duty - 0.078) at 100 Hz |
| rolling floor | duty 0.12 ≈ 0.094 m/s; 0.10 stalls | **measured** staircase |
| `kick_duty`, `kick_s` | 0.30, 0.35 s | measured: 0.15 s did not break away |
| `watchdog_s`, `stop_dist_m`, ±angle | 0.5 s, 0.20 m, 35° | brief default; lidar stop tested |
| speed cap | 0.15 m/s | brief default (never raised) |

**How we checked it.**
| Test | Command | Result | Source |
| --- | --- | --- | --- |
| Lidar stop, wheels raised | `ros2 topic pub -r 20 /cmd_vel ... x: 0.10`, box 0.155 m ahead | `lidar stop: obstacle within 0.2 m, linear zeroed`, duties `(0.0, -1)`; same behind at 0.151 m | test_log 2026-11-09 "lidar stop front/rear" |
| Lidar stop on the floor | same, box ~0.17 m | stopped; watchdog stopped 0.5 s after each command | notes 2026-11-09 "first live full-stack run" |
| First direct sweep | `/tmp/duty_run.py`, 2 s per duty | 0.15, 0.18 no motion; 0.20 unreliable; 0.25 0.63 m; 0.30 0.85 m twice; first gains 3.0/1.0 curved 35-40° | notes 2026-11-09 "first live full-stack run" |
| Overshoot root cause | duty 0.30, 2 s, idle vs 32 CPU burners | 1 kHz: 0.85 vs **1.46 m**; 100 Hz: 0.90 m both | notes 2026-11-09 (night); `drivers.yaml` |
| Duty staircase | direct script at 100 Hz, rf2o measuring | 0.293 m/s at 0.20, 0.213 at 0.16, 0.156 at 0.14, 0.094 at 0.12, **stall at 0.10** | notes 2026-11-09 (late) |
| 1 m straights | `timed_move.py straight --speed 0.15` | 0.96 m / 3 cm left (11-09); 1.06 m / 1 cm left; 1.16 m / 6 cm left: **2 of 3 within ±10 cm** | test_log 2026-11-09, 2026-11-10 CP5 |
| Battery fade | same command, successive runs | 0.84, 0.74, 0.38 m | test_log 2026-11-10 CP5 run 2-3 |
| First Nav2-driven straight | `navigation.launch.py dry_run:=false`, `timed_move.py` | 1.06 m, 8 cm left; rf2o 1.089 m | test_log 2026-11-10 "attempt 2" |
| Power, wall supply | `vcgencmd get_throttled` every 2 s, 286 samples | under-voltage in **193 (67.5 %)**, peak load 32 | test_log 2026-11-10 "power sampler" |
| Power, power bank | 60 samples under Nav2 | **0 of 60** under-voltage, peak load 10.9 | test_log 2026-11-10 "power gate" |

**Results.** The motors respond linearly above duty 0.12 (speed = 2.46 x (duty - 0.078)) and stall below
~0.10 m/s; a 1 m straight lands within 10 cm in 2 of 3 runs; the lidar stop holds at 0.155 m front and rear.
Figures: `motor_curve.png`, `straights.png`, `power.png`.

**Logs.**
```
lidar stop: obstacle within 0.2 m, linear zeroed
watchdog: no /cmd_vel for 0.52 s, stop
dry run: no GPIO                                   (C12: a "live" run that drove nothing)
Boolean value is: True                             (ros2 param get /motor_node dry_run)
throttled=0x50005                                  (under-voltage now + throttled now)
```

**Challenges → fixes.** C9 curve, stall, PWM overshoot (100 Hz, refit, kick) · C10 loose wire rebooted the Pi
(fixed) · C11 under-voltage (power bank) · C12 `dry_run` never forwarded (PR 42) · C13 battery fade (cycle each
run, mark dead-pack runs invalid).

**Tests.** `delivery_bot_drivers/test/test_motor_node.py` (22 tests: wheel split, duty and clamp, kick-start, lidar-stop
geometry front/behind/angle/no-echo, dry run default, stale-scan stop; the 0.5 s watchdog itself has no unit test), `tools/tests/test_launch_dry_run.py`, `test_timed_move.py`, `test_motor_check.py`.

**What we would change.** Wheel encoders and a closed speed loop (the gyro loop is in the YAML but not
implemented); a hardware-PWM motor driver; a larger battery.

---

## Cross-block summary for the results slide

| Block | Headline number | Source |
| --- | --- | --- |
| 1 Sense | lidar 7.05 Hz, 26-29 % no-echo, scale +3.5 cm; gyro 0.06 % on 360° | test_log 2026-10-30/31 |
| 2 Odometry | rf2o 96-101 % of a push with nobody near; 25 % with a person behind; 99.5 % with a 0.6 m cut (offline) | test_log 2026-11-02/03 |
| 3 Map | 65.5 m², 5 cm cells; start-end gap 0.109 m over 42 m (0.658 m without loop closure) | test_log 2026-10-31 |
| 4 Localise | on the mark within ~1 cm / 2°, scan-to-map 2.6 cm; recovers 30 cm / 20°, not 31° | test_log 2026-11-01; notes 2026-11-10 |
| 5 Navigate | 1.5 m goal succeeded in 93 s; around a box; 1 of 6 goals | `bt_navigator` logs 2026-11-10 |
| 6 Act | speed = 2.46 x (duty - 0.078), stall < 0.10 m/s; 1 m straight 2 of 3 in ±10 cm; lidar stop at 0.155 m | notes and test_log 2026-11-09/10 |

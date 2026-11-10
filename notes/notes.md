# CA3 — lab notebook

Newest entry first. One block per session: date, goal, what ran, result, next.
Reference material belongs in `docs/`, raw artefacts in `evidence/`.

---

## 2026-11-10 (Pi, remote, dry run) · Nav2 heartbeat, load, run_cell smoke, backup

Dry run only, no wheel moved; Pi on `main` at be4473e. With Foxglove off Nav2 came up in about 61 s (the Foxglove-on start never finished in 150 s). It then shut itself down twice on `bond_timeout` 10 s, once at idle and once as move 1 started (`behavior_server`, `smoother_server`), so OI-10 is **not** fixed in dry run. `run_cell.py` failed on its `/odometry/filtered` check (15 s timeout), no run-0 bag. Backup done (bags 153M, maps 37M).
Power: under-voltage now (0x1) in 193 of 286 samples (67.5 %): 27 of 29 during Nav2 start-up, 21 of 21 during moves, and also at load 3.5 afterwards. The supply should be replaced before the driven session.

---

## 2026-11-09 (Mac, close) · Pi powered down, docs updated

The owner powered the Pi down after the last straight (it had stopped answering SSH while the stack was being stopped). AGENTS.md (Motors row), `docs/slam_build_path.md` (CP5, 9.3, R.1) and `docs/CA3.md` (P1, OI-9 battery, OI-10 Nav2 heartbeat) updated to the 2026-11-09 motor results. On the next boot: `git pull` on the Pi, then the direct duty test before any driven run.

---

## 2026-11-09 (Pi, live, late) · low-duty fit at 100 Hz, kick-start, first 1 m straight passes

Branch `fix/motor-gains` (49bcfb1 to 56abb59). Rows in `docs/test_log.md`.

- Duty staircase (direct script, rf2o measuring): rolling speed 0.293 m/s at 0.20, 0.213 at 0.16, 0.156 at 0.14, 0.094 at 0.12, stall at 0.10. Fit `speed = 2.46 x (duty - 0.078)`: `min_duty` 0.08, gains 0.41. Rewriting the duty every 50 ms at 100 Hz is harmless.
- Kick-start needs 0.35 s at duty 0.30: with 0.15 s the robot sat still for 1.5 s.
- 1 m straight on `base.launch.py` (no Nav2), 0.15 m/s: tape 0.96 m, 3 cm left. One pass, not three.
- rf2o forward distance is within 5 cm of the tape; its sideways number is not reliable (use the tape).
- The Pi then stopped answering SSH while the stack was being stopped (probably another reboot); state of the stack unknown.

Open: two more straights; the motor battery gives about one run per power cycle (charge it, check the voltage); Nav2 shuts down on a 4 s heartbeat timeout at load 20 to 30, so Nav2 goals need `bond_timeout` raised or less load first.

---

## 2026-11-09 (Pi, live, night) · root cause of the overshoot: software PWM under load; then the battery ran out

Branch `fix/motor-gains` (c01fb04 to fd7a1d9). Rows in `docs/test_log.md`.

- Overshoot reproduced under the launched stack at load 22 to 30 (0.30 m/s pulse: 1.29 m, rf2o peak 0.74 m/s). Direct script at duty 0.30: 0.85 m idle, 1.46 m with 32 burners (33 runnable threads). The 8-burner test in the block below was too light. At 100 Hz: 0.90 m idle and loaded. `pwm_hz` is now 100, gains 0.44/0.44.
- At the speed cap (0.15 m/s, duty 0.176) the robot does not start. Added a kick-start to `motor_node` (`kick_duty` 0.30 for `kick_s` 0.15 s from rest), 5 pytests.
- Nav2 shuts itself down under load: `CRITICAL FAILURE: SERVER smoother_server IS DOWN after not receiving a heartbeat for 4000 ms` (also `route_server`), twice, both during a `timed_move` run. The collision monitor goes with it, so commands stop mid-run.
- The motor battery then died within minutes of each power cycle, so the kick-start runs are invalid.

Next: charge the motor battery (check the pack voltage), then direct test, then the 3 straights with kick-start, and the 100 Hz rewrite case (untested). Raise Nav2 `bond_timeout` or cut load (camera, Foxglove) before the Nav2 goals.

---

## 2026-11-09 (Pi, live, evening) · speed overshoot not reproduced; gains 0.44/0.44 work

Code 8153ab6, Pi rebooted (uptime 0 min at the start), motor battery restarted, `drivers.yaml` on the Pi restored to main. Rows in `docs/test_log.md`.

Both hypotheses from the block below are refuted. Direct script at duty 0.30 for 2 s gave 0.85 m idle, 0.85 m with 8 CPU burners, 0.85 m rewriting the duty every 50 ms, and 0.85 m with the full stack running. The command path is clean (`/cmd_vel` holds 0.13 for 3.31 s for a 66-message pub). Live `motor_node` with `min_duty` 0.11 and gains 0.44/0.44 gave 0.75 m at 0.30 m/s (fit predicts 0.78 m) and 0.59 m at 0.15 m/s (about 0.17 m/s): speed follows the command and holds the `v_max` cap open loop. Drift 3 to 8 cm left per run.

Most likely the earlier overshoot runs were invalid (sagging battery or loose wire, see below) or ran with params from before a YAML edit: params load only at node start. Not proven, the earlier node output was not logged (screen output is not in `launch.log`; set `PYTHONUNBUFFERED=1` and `tee`).

Next: teammate approves gains 0.44/0.44 in `drivers.yaml`; then the 1 m straight three times with `tools/timed_move.py straight` under `navigation.launch.py`, then Nav2 goals to (1, 0) and back. Lateral clearance (lidar cone) still open.

---

## 2026-11-09 (Pi, live) · first live full-stack run: lidar stop, wheel power, 1 m straight

Code 8153ab6. Mac and Pi on main; power under load passed (18/18 samples, low bits 0, 59.9 to 70.1 C).

What passed: lidar stop front and rear on the floor with a box about 0.17 m from the lidar (a box at 10 cm gives no echo on the A1M8, which counts as free), and the watchdog 0.5 s after each command.

What failed: every 1 m straight. Causes found, in order:
- A loose motor wire rebooted the Pi twice (uptime 1 min each time) and killed the wheels once. The motor battery also sagged: both wheels were dead until it was restarted. Runs taken then are invalid.
- Gains 3.0/1.0 give 0.41 vs 0.21 duty at 0.10 m/s, so the left wheel runs far faster and the robot curved hard (35 to 40 deg clockwise).
- With the stack stopped, a direct GPIO sweep (`/tmp/duty_run.py`, 2 s, both wheels) gave: 0.15 and 0.18 no movement, 0.20 unreliable (0.40 m once, then 0), 0.25 0.63 m, 0.30 0.85 m twice. Fit `speed = 2.25 x (duty - 0.11)` m/s; wheels matched (3 cm drift in 0.85 m). Below about 0.20 the wheels stall, so 0.10 m/s cannot be held open loop.
- Under the stack the same duties ran about 2x faster and did not follow the command: 0.30 m/s for 3.3 s gave 2.37 m, 0.13 m/s gave 3.1 m. Hypothesis (not measured): CPU load (average 27 to 32) and the node rewriting the duty every 50 ms disturb the software PWM.
- The lidar stop only watches the direction of travel, so a swerve into a wall beside the robot was not caught; the robot hit a table and a wall.

Not done: Nav2 goals (step 5); the 1 m straight never met the bar (1.00 m +- 0.10 m, 10 cm sideways). No gains were committed: `drivers.yaml` is unchanged on this branch. Values tried and `stop_dist_m` 0.50 (requested for safety) are in `docs/test_log.md`.

Next: the teammate decides how to get a slow, controllable speed (pulse the motors, only write the duty when it changes, or the gyro/odom loop) and re-checks PWM with the stack running; keep the motor battery charged and the wiring reseated before every session.

---

## 2026-11-09 (Mac + Pi, dry run) · motor safety fixes on `fix/motor-safety`

Owner-approved one-off fix to the teammate's `motor_node` (branch off `feat/motors`, PR back into it). Code 6b87c15. Dry run back (default true, no gpiozero import), pure `wheel_speeds`/`duty_for`/`blocked` with tests, lidar stop (0.20 m, ±35°, linear only) and stale-scan stop inside `motor_node`, `enable_stamped_cmd_vel: true` in `nav2_params.yaml`. Her duty formula, `min_duty` 0.11, gains and pins unchanged. `laser_forward_rad` is 0.0 (URDF `laser_yaw` 0).

Pi dry-run smoke (rows in `docs/test_log.md`): dry run reads True; front and rear lidar stop trip at 0.155 and 0.151 m; watchdog stops 0.50 s after the publisher; stale scan stops. Not done: Nav2 topic types and `enable_stamped_cmd_vel` on a running node (no Nav2 on `feat/motors`'s launch), stale-scan 0.5 s timing. `imu_node` died once at launch (`gyro z std 0.0257`, robot moved). Residual hazard: no echo counts as free (`docs/system/06_troubleshooting.md`).

Next: the teammate reviews; wheels-raised live test is hers; Nav2 type check on the merged branch.

---

## 2026-11-09 (Mac + Pi) · PR 33 verified live: slam vs AMCL on the mark, `run_cell.py` runs

Robot on the taped home mark, motor switch OFF, no motor node, `bridge:=false`, stacks started under `set -m` and stopped with `kill -INT`, PR head 6138265 (Pi 66 colcon tests 0 failures 1 skipped, 94 pytest passed). Before starting, two orphan processes from the teammate's `motorfix_ws` (`robot_state_publisher`, `odom_covariance_relay`) were still up on domain 42 and were stopped with SIGINT on the owner's yes.

Pose on the mark (four runs, all `scan: 1`, `leftovers: 0`, rows in `docs/test_log.md`): slam_toolbox `map -> base_footprint` (0.034, -0.035) m, yaw 8.2 deg and (0.056, -0.066) m, yaw 4.7 deg, so 0.049 m and 0.087 m from (0, 0); the two runs differ by 0.038 m and 3.5 deg, inside the 0.1 m and 5 deg bar. AMCL (0.01, 0.00) m, yaw about 0, `/amcl_pose` exactly (0, 0): it is sitting on its initial pose, so this shows AMCL runs, not that it localises. slam minus AMCL 0.041 m and 0.080 m.

`run_cell.py` live: E3 `amcl_empty` (run 98, 53 s, `/odometry/filtered` 1010, `/scan` 371, `/tf` 1423) and E2 `none_empty` run 99 (56 s, `/scan` 364, `/tf` 2615, `/imu/data` 4303, `/odom_rf2o` 358, no `/odometry/filtered`) exit 0, mcap, read back, no leftovers; a repeat of an existing bag name prints `refusing:` and exits 1. A first E3 run 99 with a 45 s delay gave a 24 s bag (the delay counts from script start, launch takes about 20 s), and its printed row was lost; use a delay of 75 s or more, and redirect the output to a file. `get_throttled` reads `0x50000` after the runs (under-voltage and throttling have happened since boot).

CI on PR 33 green: `repo-rules`, `secrets`, `build-and-test`, GitGuardian.

Open: slam yaw is 5-9 deg off the mark's 0 deg and the robot's heading on the mark was not measured; AMCL comparison needs the robot moved (the E3 `wrongstart` and `people` cells); smoke bags `E3_amcl_empty_run99`, `E3_amcl_empty_run98`, `E2_none_empty_run99` are left on the Pi in `~/bags`.

---

## 2026-11-09 (Mac + Pi) · Live config switches built (plan H); smoke run passes

Branch `nav/live-switches` (code 3ed4bee): E2 EKF variants (`config/ekf_variants/`), `ekf:=false` (identity odom -> base_footprint), `localizer:=slam|amcl` with `config/amcl.yaml`, `tools/timed_move.py`, `tools/run_cell.py`. `colcon test` 62 tests, 0 failures; `pytest tools/tests` 93 passed. Smoke rows in `docs/test_log.md` (robot off the home mark, motor switch off, no motor node on `main`).

AMCL looked broken with Nav2 on (no `map -> odom`) in three runs and fine in two with Nav2 off. Cause was the lidar, not AMCL or Nav2: each run that followed a run whose lidar was scanning got no scan at all (`Got first Laser Scan` never logged), because my background `nohup ... &` launches ignore SIGINT, so `rplidar_node` never ran its shutdown. Stopping a launch with a foreground SIGINT (`timeout -s INT 50 ros2 launch ...`) left no processes and the next start scanned. A 20 s Nav2 delay was tried on the wrong diagnosis and reverted: 5 s works. Not tested: `run_cell.py` itself on the Pi.

After rebasing onto #32 the Nav2 velocity topics are `TwistStamped`, so `timed_move.py` defaults to stamped (checked live: 1.000 m of commands, collision monitor passed 0.03 m/s on). A stack started under `set -m` and stopped with `kill -INT` leaves nothing behind.

Open: slam-vs-AMCL pose comparison needs the robot on the mark; the collision monitor's slowdown zone (0.3 x) will shorten timed straight moves near walls, which matters for E2.

---

## 2026-11-09 (Mac) · CA3 plan widened to a method × condition matrix

The 2026-11-03 questions each checked one paper number (yes/no answers, little insight). Widened D8 to a comparison (D8a): odometry configs × localisers × conditions (empty, people, degraded lidar), new RQ1 lidar spec, RQ2 odometry, RQ3 localiser, RQ4 people, E1 as the demo, new E5 lidar degradation. Inventoried `~/bags` on the Pi (`ls -1t ~/bags`): newest bag is 2026-11-03; only short push, turn and map bags, no driven, people-loop or checkpoint runs, so the 2026-11-03 schedule slipped. Updated `docs/report_plan.md` (§3 questions and storyline, §4 matrix and data status, §6 reset schedule, §7 two new candidate insights) and D8a in `docs/CA3.md`. No robot runs. `report/CA3_report.md` and `report/slides_outline.md` still use the old RQ numbers.
Later the same day: live runs switched to driven (motors are in, gains rough): driven straights and spins for E2, Nav2 or teleop checkpoint loops for E3 with both localisers replayed offline on the same bags, driven people loops for E4; hand-pushing with a stick is the fallback. Driven and hand-pushed IMU data are not mixed (motor vibration).
Evening: narrowed to plan H (D8b): people as the axis, every method live on the robot, empty room vs people walking; RQ1 impact of people, RQ2 odometry configs, RQ3 AMCL vs `slam_toolbox`, RQ4 step-in safety. Lidar degradation and the offline replay matrix dropped (simulated; replay reads ~71 % of live). Reviewed `feat/motors` (3d295f7, 3fed2ff): no dry run (base.launch.py always starts motor_node live), no lidar stop, `TwistStamped` only, no tests, gains 3.0/1.0; listed in `docs/slam_build_path.md` R.1, not yet sent to the motor teammate. `TASKS.md` added as the one task tree, then merged the same evening into `docs/slam_build_path.md` (task tree on top, Stage 9 rewritten for plan H), so the project has one task document.
Next: motor safety fixes, live switches (`ekf_params_file`, `ekf:=false`, `localizer:=amcl`) and the run sheet; driven session Tue 2026-11-10 (wheels raised first, then a 1 m straight with the switch in reach).

## 2026-11-09 (Pi, remote) · Nav2 now publishes TwistStamped

Nav2 Jazzy declares `enable_stamped_cmd_vel` with default `false` (`/opt/ros/jazzy/include/nav2_util/nav2_util/twist_subscriber.hpp:93`), so it sent plain `Twist` on `/cmd_vel` while the teammate's `motor_node` (`feat/motors`) subscribes `TwistStamped` only: under Nav2 the wheels would never have moved, silently. Set `enable_stamped_cmd_vel: true` on controller_server, behavior_server, velocity_smoother, collision_monitor and docking_server in `nav2_params.yaml`, with a config test. Checked on the Pi in an overlay (`~/stamped_ws`, domain 42, no motor node): every publisher and subscriber on `/cmd_vel_nav`, `/cmd_vel_smoothed` and `/cmd_vel` is TwistStamped (test_log row of today). Teleop keeps `-p stamped:=true`.
Side findings: `imu_node` failed its start calibration (gyro z std 0.0257 rad/s, limit `calib_max_std` 0.01), so the robot was moving or vibrating at start; the navigation launch needed a second stop after Ctrl+C.
Next: the motor safety PR into `feat/motors` (dry run, lidar stop) no longer needs the cmd_vel step.

---

## 2026-11-08 (Pi, offline) · Nav2 planner checked alone on the room map

Why alone: the teammate's `base.launch.py` was running live on the Pi with `motor_node` (no dry run), so a full Nav2 stack at rest could have driven the wheels. Planner only, in ROS domain 42 (`tools/analysis/planonly.sh`): `map_server` on `~/maps/2026-10-31_room2.yaml`, a static map -> base_footprint at home, `planner_server` on our `nav2_params.yaml`, then `plan_check.py`.

| Goal (map x, y) | Result |
| --- | --- |
| (1, 0) | path 1.18 m, 46 poses, 5 ms |
| (0, 1) | path 1.30 m |
| (1, 1) | path 2.70 m (detour round furniture; straight line 1.41 m) |
| (-1, 0) | path 1.43 m |
| (2, -1) | path 2.34 m |
| (-9, -3) | error 208, no valid path |
| (0, 20) | error 204, goal outside map |

Picture: `results/maps/2026-11-08_planner_paths.png`. Costmap config in use: `robot_radius` 0.12 (approx, never measured), inflation 0.25 m. Load 2.3-2.8, `get_throttled` 0x0. Paths are raw NavFn, grid-snapped by a few cm; not smoothed, since the smoother server did not run here.

Not tested: controller and `/cmd_vel`, smoother, collision monitor, slam_toolbox together with Nav2, the `/stack/navigation` button, `save_goal` and `deliver` on a live stack (branch `nav/nav2-glue`, unit tests and lint only).

Next: measure the robot (length, width, lidar position) and set the footprint; check the home mark's clearance from furniture on the map; run the full stack when the Pi is free or the motor switch is off.

---

## 2026-11-03 (Mac) · CA3 report framing chosen (tentative)

Read the MA4890 brief (presentation 40 %, CA3 report 20 %, both due end of Week 13; rubric content 40, conclusions 25, presentation 20, peer 15; the lecturer weights own insights highest). Compared six framings (survey, build report, replication, mission matrix, safety case, lidar vs camera); chose replication and extension of [K26]/[M26] on the delivery robot, extended to people [Y21] (D8). Wrote `docs/report_plan.md`, `report/slides_outline.md`, `report/literature_notes.md`, rewrote `report/CA3_report.md`, aligned `docs/plan.md` and build-path Stage 9. No robot runs. After reading the papers (K26 is replay without ground truth and tests AMCL, not the IMU; M26 ablates the IMU on wheel odometry), the framing word became *re-evaluation against published baselines* and the title *Re-evaluating EKF-Fused 2D LiDAR SLAM on a Low-Cost Indoor Delivery Robot: Repeatability, Inertial Contribution and the Effect of Dynamic Human Obstacles*.
Next: tape the checkpoints (9.1), then motors 2026-11-04 (OI-8 was closed later the same day, entry below: a person behind the robot). Replay noise of about 12 % (entry below) means offline E2 ablation needs several replays per condition, or live runs.

## 2026-11-03 (Pi, live) · OI-8: live push, nobody in the scan

Two stick pushes of a 1 m tape line on a charged battery (`get_throttled` 0x0 throughout), same start mark and heading, only `angle_compensate` changed (code 766511d, `tools/analysis/push_start.sh`; pushwall as in `docs/test_log.md`).

| Run | angle_compensate | beams | tape m | wall change m | rf2o m | ratio | rear pts median/max | throttled before/after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | true | 720 | 1.00 | 1.007 | 1.008 | 1.008 | 18 / 37 | 0x0 / 0x0 |
| B | false | 1022 | 1.01 | 1.023 | 0.971 | 0.961 | 16 / 61 | 0x0 / 0x0 |

**Verdict:** both at or above the 0.87 line, so the scan format is cleared; the 2026-11-01 failure points at the person behind the robot (suspect b). Cause identified, not fixed, and not reproduced here: no person walked behind in these runs.

Caveats. The stick end sat about 0.3 m behind the robot in both runs (rear points up to 37 and 61); it moves with the robot, which should bias rf2o low, and it still read the full metre. Run B started recording about 1 s into the push, so about 2 cm is missing from its rf2o and wall numbers. Run A's first start failed IMU calibration (robot touched) and was redone once. The battery was first read under-voltage (0x50005) and was charged before the runs.

**Cause confirmed in the old bags.** `pushwall.py` on the two bad 2026-11-01 bags (rows in `docs/test_log.md`): during the push the range straight behind stayed at 0.35-0.94 m and 105-158 rear points sat there (stick runs today: median 16-18); at push end the back range jumped to 3.4 m and 5.26 m and the rear points fell to 43 and 12. rf2o read 0.242 m of 0.862 m (0.28) and 0.307 m of 1.222 m (0.25) by the front wall. So a person walking behind the robot, in the scan the whole push, is what pulled rf2o down: it assumes a still room. Evidence `evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`. This is also a measured result for experiment E4 (people in the room).

Next: no config change made. `angle_compensate:=true` read best and `slam_mapping.yaml` was frozen with it, so it stays; the planner confirms. rf2o needs nobody near the robot on hand pushes; motor-driven runs do not have this problem.

---

## 2026-11-03 (Pi, remote) · OI-8: beam-format stats and the push3-5 bags

Two offline checks, nothing run live (code 2f62989: `tools/analysis/beamstats.py`, `pushwall.py`).

**Beam format.** The 720-beam bags do not show more non-finite slots or binning duplicates than the 1046-beam bags: bad (inf/nan/0) median 5.8-11 % against 9-13 %, equal adjacent ranges 20-31 % against 22-27 %, longest bad run median 8-21 against 18. The two bad 2026-11-01 bags are at the low end (bad 5.8 and 8.7 %). Suspect (a) gets no support from the slot statistics, though this does not rule out the gradients themselves.

**push3-5 (2026-11-02).** No push in any of them. Front wall 2.932-2.936 m and back wall 2.136-2.140 m in every second, rf2o 0.000 m over the marker window (push5) and over the whole bag (push3, push4). Real travel 0 m, so no ratio; rear points constant at about 111 (static room, nobody walking). They cannot separate the two suspects.

**Classification:** format suspect: not supported by the slot statistics, not tested by these bags. Person suspect: not tested. Overall inconclusive; a bag with a real push after `angle_compensate` is still needed (live push, no one behind, charged battery).

Rows in `docs/test_log.md`.

---

## 2026-11-03 (Pi, remote) · OI-8: replay repeatability and rate

Verdict: replay is **not repeatable** and **not rate-sensitive** (code e6792e8, rows in `docs/test_log.md`). Three identical rate-1.0 runs on the good bag read 0.679, 0.592 and 0.531 m over 39-50 s (mean 0.601 m, spread about 12 %; live is 0.962 m): `bash /tmp/rf2o_rate.sh ~/bags/2026-10-31_push_195343 orig 39 50 1.0`. Rates 0.5 and 0.25 read 0.689 and 0.681 m, and the bad bag reads max x 0.291 m at rate 1.0 and 0.289 m at 0.25 (`bash /tmp/rf2o_rate.sh ~/bags/2026-11-01_push_230535 orig 0 0 0.25`), so slowing playback does not recover the travel and CPU speed alone is not the cause. The arm clock did not track the distance either (600 MHz gave 0.679 m, 1500 MHz gave 0.592 and 0.531 m).
Run-to-run noise of 0.15 m means single replay numbers, including the earlier 0.681 and 0.786 m, cannot separate orig from resampled. Before this the live mapping stack was stopped (map saved as `~/maps/2026-11-03_0014.*`) so no live rf2o ran during the replays.
Next: nothing applied. Open points: why the replay differs run to run when the input bag is identical, and the live `angle_compensate:=false` push on a charged battery.

---

## 2026-11-02 (Pi, remote) · OI-8: replay window by sim time

`push_an.py` now has `window(P, t0, t1)` (straight-line distance and yaw change, odom frame) and `--sim`; `rf2o_fmt.sh` records with `--use-sim-time` and takes `[t0 t1]` (code ae9cef6). The old 0.429 m "live" number was a projection onto the first heading after an 83 degree turn; over the push window 39-50 s the live odom travels **0.962 m** (`python3 /tmp/push_an.py ~/bags/2026-10-31_push_195343 39 50 --sim`), the 2026-10-31 value.
Replay of the same window: orig **0.681 m** (71 % of live, 543 updates of 554 scans), resampled to 720 beams **0.786 m**. Control does not match live (29 % short), so the rig is still unvalidated and the format question stays open. Bad bag still replays to max x 0.291 m. Pi still `0x50005`.
Next: find why orig replay is short (first-scan or `--clock` handling; compare per-update steps against live), then the live `angle_compensate:=false` push on a charged battery. Bags `2026-11-02_121116_push3/4/5` exist and are not analysed.

## 2026-11-02 (Pi, remote) · OI-8: offline rig fixed, format still undecided; Pi is under-voltage

Robot not at hand, so only offline work on the Pi (code 349912e). `vcgencmd get_throttled` read `throttled=0x50005` at about 15:34: under-voltage and throttling **right now**, and both have occurred since boot. The portable battery is low or the supply is weak; the Pi has not been loaded beyond the bridge and `robot_control`. Replays below ran in `ROS_DOMAIN_ID=42`.

**Rig bug found.** `rf2o_fmt.sh` gave 0 updates because rcl rejects `-p init_pose_from_topic:=` (empty value); rf2o aborted at start. Passing `''` fixes it (3 bugs in all: that, the hard-coded `/tmp/resample_scan.py`, and a `pkill` pattern that never matched `resample_scan.py`).

**Results** (rows in `docs/test_log.md`). The 2026-11-01 bad push replays to exactly its live value (0.291 m of 1.222 m, 23.8 %). That bag is already 720 beams, so resampling is a no-op there. On the good 2026-10-31 bag (1046 beams), resampling to 720 changed the forward leg by about 4 % (0.124 to 0.119 m), not 76 %. But the control does not reproduce the live number (0.124 against 0.429 m), so the rig still cannot decide the format question.

**Next.** Find why the replay of the good bag differs from live (rf2o start 6 s before playback, `--clock`, or the `push_an.py` axis on a bag with a reversing leg). The live test with `angle_compensate:=false` and a stick or string (person out of the scan) still needs the robot and a charged battery.

---

## 2026-11-02 (Mac) · PR 3 merged, settings applied, tests-required check

PR 3 squash-merged as 26c192a after two CI fixes (the `dry_run` scan matched `ci.yml` itself; one `setup-ros` exit-22 rerun). Applied: squash-only with branches auto-deleted, ruleset `main` with no bypass (admin direct pushes are now refused), tag `v0.1-slam-mapping`. The two merged feature branches are deleted. New check: code changes need a test, a `docs/test_log.md` row, or `no-test:` in the PR body. Commands are in `docs/system/08_github.md`.

---

## 2026-11-02 (Mac) · git workflow: PR-only `main`, CI rule checks

Goal: stop pushing to `main` with an admin bypass and make the repo rules bind. Added `.github/pull_request_template.md`, a `repo-rules` CI job (PR title `type: YYYY-MM-DD what`, `notes/notes.md` and `evidence/` append-only, no added `dry_run:=false`), the AGENTS.md "Git workflow" section and `docs/system/08_github.md` with the settings commands. Repo settings and the ruleset are applied after this PR merges (dated rows in 08). Both merged feature branches (`slam/build-path`, `slam/plan-and-skeleton`) were already in `main`.

---

## 2026-11-02 (Pi) · robot_control and the new services run on the Pi

All on `sherm-raspi`, commit 679d297 and later, `colcon build --symlink-install` of drivers, slam and bringup (3 packages, 38 s). `dry_run` stayed true, motors untouched, motor battery not connected. Replies are the actual service replies.

| Check | Result |
| --- | --- |
| `/stack/mapping` twice | `pass after 15 s` then `pass after 16 s`; `pgrep` gave 1 lidar driver, 1 EKF, 1 bridge, 1 slam_toolbox each time |
| mapping started by hand over SSH, then `/stack/base` | `pass after 12 s`; one lidar driver, one EKF, no slam_toolbox, one `ros2 launch` (base) |
| `/stack/stop` | `stack stopped; killed strays []`; no rplidar, ekf_node or slam_toolbox left, bridge still up |
| strays reported | `/stack/stop` after a runner restart: `killed strays [11784, 11785, 11786, 11787, 11788, 11839]` |
| bag `push5` | `/bag/start` returned `/home/robot/bags/2026-11-02_121451_push5`; `/bag/stop` returned `Duration: 21.48 s Messages: 2753`; `ros2 bag info`: `/marker` Count 2, `/odometry/filtered` Count 388 |
| `/stream/start`, `/stream/stop`, `/camera/start` | all `success=True`; `ros2 topic hz /image_raw/compressed` 9.84 and 9.91 Hz |
| `/pi/shutdown {}` | `refused: send {data: true}` |
| `/pi/shutdown {data: true}` | `sudo: a password is required` (no sudoers rule yet); Pi stayed up |
| `/imu_node/recalibrate`, robot still | `success=True`, `gyro bias rad/s x=-0.02706 y=-0.00610 z=-0.02585` |
| `/run/save` during mapping | `/home/robot/maps/2026-11-02_1228.* and 6 config files in .../2026-11-02_1228_config/`, 25 s; `.pgm .yaml .posegraph .data` and `_config/` present |

**Bugs found and fixed here** (full text in `docs/system/06_troubleshooting.md`): stray pattern killed the ssh shell (anchored it); 8 s fixed wait too short (polls to 25 s); first marker lost because the recorder is not ready for 2.5 s (`/bag/start` waits for `Recording...`); `/run/save` never replied (blocking calls on a multi-threaded executor). `tools/analysis/marker_pub.py` is the CLI stand-in for Foxglove's Publish panel.

**Not tested.** `/imu_node/recalibrate` with the robot nudged during the call (needs a person; the unit test covers the noisy case, but that test has not run in CI either). `/stack/localisation`. The systemd unit and the sudoers rule (owner steps). `/pi/reboot`, and an actual shutdown. Test saves left in `~/maps` on the Pi: `2026-11-02_1224.pgm/.yaml` (incomplete, from the hung call), `2026-11-02_cli.*`, `2026-11-02_1228*`; delete by hand if unwanted.

**Next.** Owner steps in the README (sudoers, linger, unit), the Foxglove layout export, then the OI-8 push rerun using `/set_pose`, `/bag/start` and `/marker`.

---

## 2026-11-02 · Foxglove buttons for every routine hand-test action

**Added (Mac, not yet run on the Pi).** `tools/robot_control.py` (replaces `stream_control.py`): Call Service buttons `/stack/base`, `/stack/mapping`, `/stack/localisation`, `/stack/stop`, `/camera/start|stop`, `/stream/start|stop`, `/bag/start|stop` (parameters `bag_label`, `bag_topics`), `/control/status`, `/pi/shutdown|reboot` (SetBool, refused unless `data: true`). Each command runs in its own process group and stops with SIGINT, SIGTERM, SIGKILL; stray stack processes started by hand are killed before a stack starts. `bridge:=false` added to `base`, `mapping` and `navigation` launch files so the runner owns the one Foxglove bridge. `/imu_node/recalibrate` (`imu_node.py`) and `/run/save` (`delivery_bot_slam/run_save.py`, started by `mapping.launch.py`) written, with a unit test each. `tools/robot-control.service` starts the runner at boot.

**Moved.** `stream_control.py`, `start_streams.sh`, `audio_stream.py`, `lidar_off.py` to `tools/streams/`; `inf_histogram.py` to `tools/analysis/`. After `git pull` on the Pi, rerun `bash tools/streams/start_streams.sh`.

**Checked.** Files compile; bag-name logic and the group kill ran against a stubbed `rclpy` on the Mac. pytest and ROS were not available on the Mac, so the new unit tests have not run. Nothing was run on the Pi: no number here is a measured result.

**Next.** On the Pi: `git pull`, `colcon build`, then test `/imu_node/recalibrate` (robot still passes, nudged must fail) and `/run/save` during mapping, then the six checks in the task brief (`/stack/mapping` twice gives one lidar driver, one EKF, one bridge; hand-started processes killed as strays; `/stack/stop` leaves none; bag holds `/marker` and `/odometry/filtered`; camera returns after the stream; shutdown refused without `{data: true}`). Steps only the owner can do (sudoers rule, linger, Foxglove layout export to `docs/foxglove/control_layout.json`) are in the README.

---

## 2026-11-01 (night) · rf2o reads 24 % of a hand push

**Finding.** Two pushes (1.00 m and 1.20 m, two places) read 0.243 m and 0.289 m on rf2o (-76 % both), while the lidar's own front-wall range confirmed the real travel (0.996 m and 1.222 m). On 2026-10-31 the same stack read -3.8 % and -2 %. The two candidate causes: the scan format (those older bags have 1045 beams at 0.34 deg; every bag since `angle_compensate: True` has 720 beams at 0.50 deg) and a person's legs moving with the robot (about 150 scan points within 1.2 m behind it during the pushes). Not separated yet. The EKF has probably been fed a velocity about 4 times too small since the map run; the map itself is not affected (scan matching in slam_toolbox, loop closure 0.115 m).

**What was added.** `angle_compensate` launch argument on `lidar.launch.py` and `rf2o_alone.launch.py` (default true, mapping unchanged); scripts in `tools/analysis/` (`scanchk.py`, `scanfmt.py`, `rear_points.py`, `resample_scan.py`, `rf2o_fmt.sh`, `push_start.sh`, `push_stop.sh`). The offline rig (`rf2o_fmt.sh`) gave 0 rf2o updates on its control run and needs fixing.

**What went wrong.** The portable battery went flat in the middle of a recording; the bag directory was lost, and `/tmp` was wiped by the reboot (scripts there are gone: copies are in `tools/analysis/`). The Pi on wall power cannot be moved. The lidar hung at start on most restarts (OI-6).

**Next.** (1) Fix the offline rig so its control reproduces -3.8 %, then run `resampled`: if rf2o drops to about 24 %, the format is the cause. (2) Otherwise repeat the push with `angle_compensate:=false` on a charged battery, and once with a stick or string so the person is not in the scan. (3) If the format is the cause, rf2o needs a fixed beam count that keeps its scale (slam_toolbox needs a fixed count too). (4) 4.5 fusion and 3.3 break tests after that. Charge the portable battery first.

---

## 2026-11-01 · base/mapping/localisation launch files, 6.2 localisation on the room graph

**Launch files.** `base.launch.py` now starts the whole base stack (robot_state_publisher, lidar, rf2o with `publish_tf: false` 2 s late, covariance relay, `imu_node`, EKF, foxglove_bridge); `mapping.launch.py` ran live from one command (slam_toolbox active, `map -> odom`, a 241 x 112 map saved) and a bug turned up and was fixed: configure is now sent 5 s after start, otherwise it fails when `include_base:=false`. `navigation.launch.py` is base + `localization_slam_toolbox_node` on `~/maps/2026-10-31_room2_graph`, no Nav2 yet. The start pose is `map_start_pose: [0, 0, 0]`: `map_start_at_dock` is rejected in localisation mode.

**6.2 localisation.** With the robot placed by eye near the lost home mark, live `/scan` points sit on the walls and furniture of the saved map in Foxglove (display frame `map`). `tf2_echo map base_footprint` read x 0.01, y 0.03, yaw -0.034 rad after turning the robot by hand to about 0 deg: the old home pose (0, 0, 0 in `goals.yaml`) is still right. The original tape had been removed; a new mark is taped at that spot, so the map and `goals.yaml` do not change.

**Housekeeping.** Pi bags (115 MB) and maps (26 MB) backed up to `bags/` on the Mac. `main` protected: `build-and-test` required. EKF 20 Hz: loop closure 0.115 m against 0.109 m, late-update count confounded (log). Orphan `ros2 launch` children survive SIGINT from a non-interactive script and give double lidar/IMU nodes: stop with SIGTERM and pkill the children. The repo is public, not private as AGENTS.md says.

**Next.** 6.3 (pose estimate) and 6.4 (wrong-start test), then `base.launch.py` `dry_run` once `motor_node` exists. The 5.3 bag half was not shown on 2026-11-01 (rig failed twice), but it had already been shown on 2026-10-30 (`mapping.launch.py include_base:=false use_sim_time:=true` over the `still2` bag: `/slam_toolbox` active, `/map` 102x65; commit 25403ba, `docs/test_log.md`); I missed that row on 2026-11-01. 6.4 result: 30 cm / 20° converged, 30 cm / 31° did not, 60 cm / 30° read at rest and inconclusive. Journal drafted by Claude from the logs (`docs/slam_journal.md`), to be rewritten in the author's words.

---

## 2026-10-31 (night) · camera quality raised to 1280x720 at 10 fps

**Under SLAM load.** Same camera settings with `slam_replay` running on the room bag (commands and numbers in `docs/test_log.md`). slam_toolbox kept up in every run (0 dropped scans) but the camera falls short of its rate and the EKF starts missing its update deadline (0 late updates in 65 s without the camera, 8 to 26 with it). Delivered: 1280x720 @10 gives 8.3 Hz, 1024x768 @15 gives 9.9 Hz, 640x480 @30 gives 21 Hz, 1280x720 @5 gives its full 5.0 Hz. One run each, so the EKF counts are not a ranking. Map quality was not compared. Left at 1280x720 @10 for viewing; while mapping or replaying, either switch the camera off or use 1024x768 @15.

Swept the camera from 640x480 up to 1920x1080 (numbers and commands in `docs/test_log.md`). The Pi decodes the camera's MJPEG in software on one core and re-encodes it for the compressed topic, so the delivered rate falls as the pixel count rises: about 11.6 Mpixel/s whatever the setting. 1280x720 at 10 fps is the sharpest setting that still delivers its full rate (10.000 Hz, std dev 4.8 ms, 1.9 MB/s). 1920x1080 only reaches 4.5 to 5.7 Hz, which looks like lag. Lower JPEG quality did not help; the passthrough `raw_mjpeg` mode gave no usable topic. `camera.yaml` now 1280x720 at 10 fps (commit c6beb1b). The node takes a full core, so keep it off during a mapping run. For smoother motion at lower detail, 640x480 at 30 fps gives 28 Hz.

---

## 2026-10-31 (late) · 5.5 sweep done, config frozen, camera stream started

**5.5.** Five replays of the 5.4 bag (numbers and commands in `docs/test_log.md`). Loop closing
is the only change that matters: first-to-last pose distance 0.658 m with it off, 0.109 m on.
`min_laser_range` 0, `minimum_travel_distance` 0.05 and 0.2 land within about 1-8 cm of the
baseline on one run each, which is not a difference. `slam_mapping.yaml` kept as it was and
frozen (commit 6484678); 5.5 ticked.
**Correction.** The scattered dots on the map floor are not the person pushing the robot, as
first guessed: they sit in a regular grid and have a star shape, which fits office chair
bases and table legs. They are real, and Nav2 should treat them as obstacles.
**Camera.** UGREEN camera 2K (USB 1bcf:2284) on `/dev/video0`; `ros-jazzy-usb-cam` and
`v4l-utils` installed with sudo by the user; `robot` added to `video`. `camera.launch.py` and
`camera.yaml` in `delivery_bot_bringup`, 640x480 at 15 fps MJPEG, 15.8 Hz measured, ~20 % of
one core. Starting it with the sweep and a full Foxglove bridge pushed the Pi to load average
18.8 and a 10 s Foxglove lag (ping 250 ms); stopped until the sweep ended. The brightness
setting in the yaml did not take effect (camera still reported 50): to debug. Layout
`docs/foxglove/camera_layout.json` written, import not confirmed.
**Next.** Fix the camera brightness; stage 6 localisation; the map reading for the 5.4 distance
check; person-free repeat of the room run if the chair dots need confirming.

---

## 2026-10-31 · robot built: mounting, rf2o hand tests, variances, first room map

**Goal.** Use the built robot (pushed by hand, no motors) to close the SLAM steps that
needed hardware. Commands and every number are in `docs/test_log.md`.

**Done.**
- **Mounting (2.1)**, tape, from the midpoint of the four wheels: lidar 2 cm forward, centred, 12 cm
  up; IMU 2.3 cm forward, 5.5 cm right (`imu_y` -0.055), 7 cm up; `wheel_base` 0.156 m, front-to-back
  wheel spacing 0.113 m, `robot_radius` ~0.12 m, `wheel_radius` 0.0325 m (TT default, not
  measured). Four wheels, skid-steer: 0.156 m is a first guess for the effective track width.
- **Box test (1.4)** repeated twice: face at +6 deg, then +2.6 deg; the spread is hand placement,
  so `laser_yaw` stays 0.
- **3.2 rf2o by hand.** Full turn: rf2o -352.9 deg, gyro -360.2 deg, true 360 (clockwise). 1 m
  push: rf2o 0.962 m (-3.8 %). Both sensors agree on sign: no 180 deg mount error. rf2o holds
  within 1 deg for 90 s at rest.
- **4.4 variances** fitted from those two bags: `vx_variance` 1e-4, `vyaw_variance` 5e-3,
  `gyro_var` 1e-4 (at rest 1.7e-6, x60 margin), `gyro_scale_z` 1.0. The hand motion was far
  faster than the robot will drive (gyro rms 0.74 rad/s) and rf2o read 9-15 % low there, so
  the motion term was scaled to 0.4 rad/s rather than fitted raw. Recheck with motors running.
- **5.4 first room map.** 317 x 233 cells at 0.05 m, 65.5 m2 free. Raw `/scan` against tape:
  1.085 vs 1.05 m (+3.5 cm) and 1.494 vs 1.48 m (+1.4 cm); the map read 1.00 m on the first gap
  (-5 cm, the cell size). 5.4 not ticked: map reading for the second gap is missing.
- 3.2, 4.4, 2.1 ticked in `docs/slam_build_path.md`.

**Found.**
- **Lidar beam count.** The first live map was a 184 x 112 fan. slam_toolbox rejected 223 scans:
  `LaserRangeScan contains 1041 range readings, expected 931`. rplidar_ros sends a varying
  count with `angle_compensate` off (its default). Fix `lidar.launch.py` `angle_compensate:
  True`, 720 beams per scan, 0 rejections after (commit 4a16fe8). This is the one to remember.
- **Person behind the robot** shows as a co-moving blob (about 20 deg of beams at 1 m) and
  leaves scattered dots on the map floor. rf2o still closed a 27 m loop within 0.5 m.
- **rf2o never reports `vy`** (always exactly 0), so sideways drift cannot be read from its twist.
  The 1 m push path pointed 18 deg off rf2o's own heading; unexplained, not claimed as a mount error.
- **Lidar stalls after being killed mid-scan**: no health line, no `/scan`. Stop everything, wait
  about 6 s, relaunch the lidar alone.
- A wall 0.46 m behind the robot was absent from scan and map (nothing nearer than 5.4 m); at
  the next pose the scan matched the tape. Cause unknown, likely a measurement mix-up.

**5.5 sweep.** Five replays of `~/bags/2026-10-31_map_200956` (baseline, `min_laser_range` 0,
loop closing off, `minimum_travel_distance` 0.05 and 0.2), driver `/tmp/sweep.sh`, analysis
`/tmp/sweep_an.py`, copies in `~/sweep_partial_2026-10-31/scripts`. Aborted once for a power
switch (portable charger to cable) and restarted at 20:35; about 45 min.

**Not done / next.** 5.5 table and frozen config; stage 6 localisation (also gives the map
reading for 5.4); clean person-dots out of the map before Nav2; 3.3 failure modes; 4.5 fusion vs
no fusion; recheck `gyro_var` and fit the track width with motors running (teammate's node).

**Lessons.** `pkill -f` with a pattern that appears in the ssh command line kills the ssh
session (exit 255): put it in a script file. A backgrounded `ros2 bag record` ignores SIGINT
from a non-interactive shell: use SIGTERM, then wait for `metadata.yaml`. A Pi reboot clears
`/tmp`: keep scripts in `~/`. `imu_node` refuses to start while the robot moves.

---

## 2026-10-30 (night) · SLAM software without the robot

**Goal.** Finish everything that does not need the built robot.

**Done** (commands and numbers in `docs/test_log.md`):
- 4.3 `odom_covariance_relay`, replay-checked; 5.3 `mapping.launch.py` (lifecycle driven);
  5.5 launch half `slam_replay.launch.py`; 7.1 `trajectory_recorder` + TUM output, paths
  seen in Foxglove; 8.2 `explore_lite` built at pinned 326cf8a (11 min 54 s on the Pi).
- `imu_node` written (was a skeleton) and run at rest: 100.04 Hz, gyro bias z -0.0279
  rad/s removed at startup, z std 0.00175 rad/s, accel z reads 11.16 m/s2 (14 % high,
  unused by the EKF). `gyro_var` stays at the 4e-4 brief default until 4.4.
- `tools/startup_race.sh`, `delivery_bot_slam/launch/rf2o_alone.launch.py` for 3.4.
- Foxglove layout `docs/foxglove/slam_layout.json` hand-written, **import not yet
  confirmed**, so 7.2 is not ticked.

**Not done / needs robot.** 2.1, 3.2, 3.3, 4.2, 4.4, 4.5, 5.4, 5.5 sweep and freeze, 6.x, 7.3,
8.3-8.5, 9.x; repeat the 1.4 box test within +-2 deg once the lidar is mounted. `evo` is not
installed anywhere, so 9.3 and the `evo_traj` part of 7.1 are untested.

**Lessons.** `pkill -f` and `timeout`-less `ros2 topic echo --once` on a sim-time topic
both hang the session; use script files and `timeout`. A replayed bag stops publishing
sim-time topics when it ends.

---

## 2026-10-30 (evening) · 3.4 startup race, near-return ring is the room

**Ran.** `tools/startup_race.sh 10 2.0` on the Pi: 10/10 clean (rf2o_alone.launch.py,
rf2o delayed 2 s). Delay 0, 3 launches: also clean; first scan arrives ~13 s after
launch, so the race needs a slow URDF. Keep the delay in `base.launch.py` anyway
(request to the bringup owner).
**Near-return ring (OI-4).** Fraction of returns <0.30 m per 30 deg bin
(`/tmp/near.py` over `still_`, `still2_`, `rot90_` bags): the bins move between bags
(0..60 deg, then 30..120, then 90..180), so it follows the scene, not the lidar. No
`mask_deg` needed on this evidence; recheck once mounted on the robot.
`/dev/rplidar` symlink now exists on the Pi.

---

## 2026-10-30 (later) · 1.4 box test: on +x, coarse only

**Ran.** `bash /tmp/box_check.sh` on the Pi, then ranges within +-40 deg of the same
`/scan`. Box arc spans -13..+30 deg at 0.23-0.25 m (centre ~+9 deg, ~43 deg wide).

**Result.** Box is on +x, not +-90 or 180: the convention check passes, `laser_yaw = 0`
holds coarsely (+-10 deg). Not the spec test: box was at 0.23 m not 0.50 m and off-centre,
so the 0 +- 2 deg tolerance in `docs/slam.md` is **not** shown. Still *brief default*,
not *measured*. Returns at 0.18-0.25 m around the other directions persist (the OI-4 ring).

**Next.** Re-verify the +-2 deg after the URDF is live: box centred at 0.50 m, view in
`base_link`.

---

## 2026-10-30 · SLAM build path: stage 1 done, 1.4 redo not yet clean

**Goal.** Redo the 50 cm box test (1.4) cleanly; push on to stage 3.

**Ran.** `bash /tmp/box_check.sh` on the Pi (one `/scan`, nearest returns and close
returns per 30 deg bin). Scene still cluttered: nearest returns at 85-90 deg, 0.18 m
(something on the lidar's left side, probably the desk or the robot itself); nothing
at 0.50 m near 0 deg (min 0.318 m in -30..30). Not a valid box test.

**Result.** `laser_yaw = 0` stays *provisional* (brief default, not measured).
Earlier findings (rf2o still baseline: x -2.4 mm, y -0.6 mm, yaw +0.26 deg over ~28 s,
`bags/still2_2026-10-30`) are in the session record.

**Next.** Clear 1 m around the lidar, one box at 0.50 m on +x, rerun `box_check.sh`.
Stage 3 hardware tests (3.2, 3.3) and 2.1 need the robot built.

---

## 2026-10-23 · documentation moved into the repository; repo made private

**Goal.** Stop the plan, notes and evidence from existing only on one MacBook.

**Decided.** One repository, three copies (Mac, GitHub, Pi), GitHub as source of truth.
`delivery_bot` becomes **private** — the notebook, report draft and assessment
reasoning are not for publication. CA1/CA2 stay out of this repo.

**What moved** (from the local-only `MA4890/CA3/`, 172 KB):

| Was | Now |
| --- | --- |
| `CA3/README.md` | `docs/CA3.md` |
| `CA3/CA3_plan.md` | `docs/design-plan.md` |
| `CA3/docs/01…07` | `docs/system/01…07` |
| `CA3/notes.md` | `notes/notes.md` |
| `CA3/AGENTS.md` | `AGENTS.md` (repo root), with sync rules added |
| `CA3/evidence/lidar/` | `evidence/lidar/` |
| `CA3/report/` | `report/` |
| `CA3/scripts/` | `tools/` |

`config/` and `results/` were empty placeholders — the real configs already live in
the package `config/` directories, so only `results/.gitkeep` was kept.

**Also committed.** The six untracked pipeline diagrams (`docs/img/`, `docs/*.mmd`,
`docs/pipeline*.html`) that had been sitting on the Mac since 2026-10-22.

**Verification.** Relative links checked across every `.md` (0 dangling);
`gh api` unauthenticated → 404, so the repo is genuinely private; backup tarball at
`~/Desktop/CA3-backup-20261023.tar.gz` before any move.

**Consequence.** `docs/pi_setup.md` (from-scratch install) and
`docs/system/02_pi_setup.md` (measured state) both survive, each now pointing at the
other. The Pi pulls; it does not author prose.

**Next.** Delete the local `MA4890/CA3` once the repo copy is confirmed, so there is
no second copy to diverge. Then the OI-4 echo-rate control run.

---

## 2026-10-22 · D5 — standard ROS 2 stack adopted; own-maths v1 retired

**Goal.** Decide the estimation / mapping / navigation stack before P1 bring-up work.

**Decided.** The brief permits packages, so v1 moves from D4's own numpy stack to the
standard lidar-only robot stack, recorded as D5 in the README:

| Job | Package (Jazzy) |
| --- | --- |
| Lidar driver | `rplidar_ros` |
| Lidar odometry (in place of encoders) | `rf2o_laser_odometry` (source, `ros2` branch) |
| Odometry + gyro fusion | `robot_localization` EKF, `two_d_mode: true` |
| Mapping + localization | `slam_toolbox` |
| Planning, control, obstacle stop | Nav2 (RPP controller, Collision Monitor) |
| Keyboard driving | `teleop_twist_keyboard` |
| Viewing / logging | `foxglove_bridge`, `rosbag2` MCAP (D2/D3 unchanged) |

**Dropped.** `kiss-icp`. It is 3D point-to-point ICP tuned for dense spinning-lidar
clouds; on a sparse planar A1 scan at 5–7 Hz it solves a problem shaped nothing like
ours, and cost a source compile plus a 2 GB swapfile for the privilege. `rf2o` is
planar by construction. The own EKF / A\* / pure pursuit stay documented as the
fallback of record if a package underperforms.

**What we still write.** Motor node (L298N PWM on `lgpio`, gyro turn-rate loop,
watchdog), IMU node (MPU6050 → `sensor_msgs/Imu`, bias calibration, gyro-z only),
URDF (`base_link → laser` / `imu_link`), delivery script (Nav2 Simple Commander).
Safety rules unchanged: motor-node watchdog, Collision Monitor between controller and
motors, `v_max` 0.15 m/s.

**Corrections to the plan as received.**

| Claim | Correction |
| --- | --- |
| Foxglove at `ws://100.73.7.24:8765` | that is the **offline** box (OI-1); use `ws://100.83.14.99:8765` |
| "the C++ driver may recover the missing points" | loss is photonic (67 % of pings return distance 0, clean serial); a driver change moves no photons — the 50 cm white-box test is still the gate |
| install clock workaround (`htpdate`) / Ghostty fix | unverified claims, not needed for bring-up; check only if a symptom appears |
| bag list `/scan /imu/data /cmd_vel /tf` | add `/odom` and `/odometry/filtered` for the replay tests |

**Next.** The echo-rate verdict on `sherm-raspi` (OI-4) still gates everything: apt
install the stack, URDF + both nodes, keyboard drive, bag, rf2o+EKF tuning, map, Nav2.

**Risk.** `rf2o` is a single-file Humble-era port; expect to patch the `ros2` branch
on Jazzy. Fallback if it stalls: EKF on gyro + `slam_toolbox` pose deltas.

---

## 2026-10-22 · P0 install: ROS stack on sherm-raspi, tmux base, Ghostty terminfo

**Goal.** Put the D5 stack on the box and make SSH sessions survive drops.

**What ran (user-driven, in a `tmux` session `ca3`).**

| Step | Outcome |
| --- | --- |
| `infocmp -x xterm-ghostty \| ssh ... 'tic -x -'` from the Mac | ✅ Pi now reads `~/.terminfo/x/xterm-ghostty`; `tic` alias warning is harmless |
| first `tmux` attempts | ❌ `missing or unsuitable terminal` → server never started → `no server running on /tmp/tmux-1000/default`; fixed by the terminfo import, recorded in [docs/06_troubleshooting.md](../docs/system/06_troubleshooting.md) |
| `tmux new -s ca3` with windows `driver` / `monitor` / `view` / `shell` | ✅ persistent workspace |
| `sudo apt update` | ✅ all three sources fetched (ROS, Ubuntu ports, Tailscale) |
| `sudo apt install ros-jazzy-{rplidar-ros,slam-toolbox,robot-localization,navigation2,nav2-bringup,teleop-twist-keyboard,robot-state-publisher}` | ✅ first attempt never ran (mangled multi-line paste); retried as one line |
| `ros2 pkg prefix` loop over the six packages | ✅ all `/opt/ros/jazzy` |

**Notes.** `id` still shows no `dialout` after the 01:24 reboot — the earlier `usermod`
had not taken; re-run `sudo usermod -aG dialout robot` and use a fresh login before
the IMU step (the lidar works via `MODE="0666"`). Pip and venv apt packages are now
installed (`python3-pip-wheels`, `python3.12-venv` in the transcript).

**Next.** `rf2o_laser_odometry` from source into `~/ros2_ws`, then the venv.

---

## 2026-10-22 · Repo reduced to a rebuild skeleton (friend builds it slowly)

**Decision.** The working implementation stays as the tag `reference-v1`; `main`
becomes a skeleton so someone can learn the ROS 2 stack by writing it.

**What was blanked — 10 files, 1,530 → 342 lines.** `motor_node.py`,
`imu_node.py`, `deliver.py`, `save_goal.py`, `scan_stats.py`, the four launch
files, and the URDF body. Each is now its docstring (the contract: watchdog
rules, `publish_tf: false`, `orientation_covariance[0] = -1`, the frame tree)
plus signatures that `raise NotImplementedError`. Launch files return an empty
`LaunchDescription`; the xacro keeps a valid `<robot>` root so `xacro` still
exits 0 and CI keeps a real check to grow into.

**What was deliberately kept.** `README.md` (plus a banner explaining the
skeleton), repo `docs/`, this folder, all YAML — `ekf.yaml`,
`slam_mapping/localization`, `nav2_params` (369 lines), `drivers.yaml`,
`goals.yaml` — and the packaging: `package.xml`, `CMakeLists.txt`, `setup.py`,
`setup.cfg`, `resource/`, `deps.repos`, `.github/workflows/ci.yml`. Deleting the
YAML would turn "rebuild this robot" into "invent a Nav2 configuration", which is
a different task.

**Verification on `sherm-raspi` after `git pull` (commit `a407464`):**

```text
colcon build --symlink-install --executor sequential
  Summary: 5 packages finished [20.4s]
xacro …/delivery_bot.urdf.xacro        -> exit 0, <robot name="delivery_bot">
ros2 launch delivery_bot_bringup base.launch.py  -> clean start, zero nodes
ros2 run delivery_bot_drivers motor_node         -> NotImplementedError, exit 1
```

So the scaffold builds and launches; nothing pretends to work. That last line is
the honest signature of this commit: **green build, no behaviour.**

**Consequence for these docs.** `docs/07_ros_stack.md` and the P-status in
`README.md` describe `reference-v1`, not the current tree. Read them as the
target specification. "Builds" no longer implies "runs".

---

## 2026-10-22 · rf2o built and verified; stack on the Pi documented as it really is

**Goal.** Finish P0 and build `rf2o_laser_odometry` from source.

**Blocker first.** The Pi had fallen off SSH (`Connection timed out during banner
exchange`) — logged as the incident entry below. After the power-cycle: `up 0 min`,
`dialout` now active for `robot`, 3.2 GiB free.

**Swap, before anything else.**

```
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo "/swapfile none swap sw 0 0" >> /etc/fstab      # persisted
```

`free -h` → `Swap: 2.0Gi`. `/etc/fstab` line verified.

**Apt stack confirmed present:** `build-essential 12.10ubuntu1`, `cmake 3.28.3`,
`git 2.43.0`, `python3-pip 24.0`, `python3-venv 3.12.3`. `i2c-tools` still absent.
The D5 ROS packages were already installed: `rplidar_ros 2.1.0`, `slam_toolbox 2.8.5`,
`nav2_bringup 1.3.13`, `robot_localization 3.8.3`, `xacro 2.1.1`, `tf2_ros`.

**A stale SSH host key cost a detour.** `192.168.31.109` had two entries in
`known_hosts`; the older one (from a different device that held that IP) was being
matched, giving `Host key verification failed`. The live key matched the
`sherm-raspi.local` entry, so the stale line was removed with
`ssh-keygen -R 192.168.31.109`.

**Build.**

```
cd ~/ros2_ws && source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --executor sequential --parallel-workers 1
```

Output: `delivery_bot_description` 1.3 s, `drivers` 8.6 s, `mission` 7.7 s,
**`rf2o_laser_odometry` 3 min 17 s**, `bringup` 7.4 s — *5 packages finished in 3 min 43 s*.
Verified: `ros2 pkg prefix rf2o_laser_odometry` →
`/home/robot/ros2_ws/install/rf2o_laser_odometry`, executable `rf2o_laser_odometry_node` present.

**What was already there.** `~/ros2_ws/src/delivery_bot` is a git repo
(`9e2fd2e Initial delivery_bot stack: drivers, bringup, mission, docs`) with
`bringup` (launch: base/lidar/mapping/navigation, config: ekf, slam_mapping,
slam_localization, nav2_params), `description` (URDF/xacro), `drivers`
(`imu_node`, `motor_node`), `mission`. `rf2o` is cloned alongside, outside the repo,
branch `ros2`, HEAD `b38c68e`.

**Already handled correctly in the launch file** — worth noting because it was the
risk flagged before the build: `base.launch.py` runs rf2o with `publish_tf: False`,
`odom_topic: /odom_rf2o`, and lets `ekf_filter_node` own `odom → base_footprint`.
`motor_node` is overridden to `dry_run: true` by the launch file.

**GPIO question settled.** `motor_node` uses `gpiozero` with `LGPIOFactory`;
`lgpio` is at `/usr/lib/python3/dist-packages/lgpio.py` (`python3-lgpio`), and
`RPi.GPIO` is absent — so the plan's `python3-lgpio` route works, just through
gpiozero rather than a bare import.

**Docs updated to match reality.** `README.md` gained D5 (rf2o + robot_localization
replace KISS-ICP + our own EKF) and D6 (code lives in `~/ros2_ws/src/delivery_bot`;
this folder is documentation and evidence). `docs/07_ros_stack.md` was rewritten from
intention to inventory: real nodes, topics, `tf` ownership, gotchas. `docs/04`'s
pipeline table now names the nodes that exist, and records that **the safety node
does not exist yet** — `motor_node` takes `/cmd_vel` directly, protected only by the
watchdog.

**Next.** `/dev/rplidar` symlink, `i2c-tools`, then the echo-rate probe on this box.

---

## 2026-10-22 · INCIDENT: sherm-raspi stops answering SSH at the banner (unresolved)

**Symptom.** `ssh robot@sherm-raspi.local` hangs and dies with
`Connection timed out during banner exchange` / `Connection to <ip> port 22 timed out`.

**What still works.** `ping` replies (lossless, but RTT jumped from ~7 ms to ~74–140 ms),
and `nc -z 192.168.31.109 22` reports **`tcp/ssh succeeded`** — so the network path,
the listener and the kernel are all alive. Also checked: LAN IPv4, `.local` (IPv6
link-local), and Tailscale `100.83.14.99` (which now times out at connect). Port 8765
(Foxglove bridge) is closed.

**Interpretation.** A TCP handshake completes but sshd never sends its version string.
That is not DNS or firewall — it is the sshd child being unable to run: the classic
cause on this box is **memory exhaustion**. The image has **no swap** (`Swap: 0B`),
4 GB RAM, and a `colcon build` (rf2o, and previously a `kiss-icp` pip compile) runs
4 parallel jobs on 4 cores. Under that load the OOM killer takes sshd children before
they can write the banner.

**Not yet tried:** physical power-cycle, and a longer wait.

**Fix before retrying any build:**

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
colcon build --symlink-install --executor sequential --parallel-workers 1
```

**Lesson.** "No swap" was recorded in [docs/02_pi_setup.md](../docs/system/02_pi_setup.md) as a
footnote for `kiss-icp`; it is a hard prerequisite for *any* build on this Pi, and it
can take the whole machine off the network rather than failing with an OOM message
you can read.

---

## 2026-10-22 · P0 on sherm-raspi — serial access half done

**Goal.** First real P0 steps: `dialout` membership and the `/dev/rplidar` udev alias.

**What ran.**

```
sudo usermod -aG dialout robot
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"' \
  | sudo tee /etc/udev/rules.d/99-rplidar.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/rplidar /dev/ttyUSB0; i2cdetect -y 1
```

**Result.**

| Step | Outcome |
| --- | --- |
| `usermod -aG dialout robot` | ✅ command succeeded — **not yet in effect** (`id` in the same session still showed the old groups; needs a fresh login) |
| udev rule written to `/etc/udev/rules.d/99-rplidar.rules` | ✅ |
| `udevadm control --reload-rules && udevadm trigger` | ✅ ran clean |
| `/dev/rplidar` exists | ❌ **still absent** — the rule did not materialise the symlink on a plain trigger |
| `i2cdetect -y 1` | ❌ `Command 'i2cdetect' not found` — `i2c-tools` is not installed |

**Reading.** `/dev/ttyUSB0` is still `root:dialout 0660`, so nothing is readable by
`robot` yet. Two likely causes for the missing symlink: the trigger did not emit an
`add` event for an already-attached device, or the rule needs the device to
re-enumerate. Next attempt: `sudo udevadm trigger -c add -s tty`, else unplug and
replug the CP210x adapter. The `MODE="0666"` in the rule means group membership stops
being the blocker once the symlink lands.

**Also missing:** `python3-pip`, `python3-venv`, `i2c-tools` — apt install next, plus
a 2 GB swapfile before any `kiss-icp` compile.

**Added this session.** `AGENTS.md` at the top of `CA3/` — the short "how to work
here" file: target machine, stack decisions, rules, current state, next actions in
order. Anything that changes goes in this notebook, not into `AGENTS.md`.

---

## 2026-10-22 · CA3 folder scaffolded, stack direction fixed

**Goal.** Give the project a home in `CA3/` and settle which machine and stack we build on.

**Decided.** Target is `robot@sherm-raspi` (Ubuntu 24.04.5, Pi 4B). ROS 2 Jazzy is
in scope; Foxglove replaces the plan's ZeroMQ telemetry and `tools/viewer.py`; the
pure-Python EKF / A\* / pure-pursuit / occupancy-grid maths stays ours, wrapped in
ROS nodes. `CA3_plan.md` §0 "no ROS" is superseded — recorded as D2 in the README.

**Done.** Created `README.md`, this notebook, `docs/01–07`, `scripts/`, `config/`,
`evidence/{lidar,imu,motors}`, `results/`, `report/`. Renamed
`Room Delivery Robot — Implementation Plan.md` → `CA3_plan.md` (spaces and an em
dash in a filename bite you in git and on the Pi).

**Next.** P0 on `sherm-raspi`: `python3-pip` + `python3-venv`, `dialout`, udev rule,
venv, then re-run the lidar probe on *this* box to answer OI-4.

---

## 2026-10-22 · Machine discovery: the brief's Pi is gone, sherm-raspi is the box

**Goal.** Get back to the lidar work; `ssh robot@100.73.7.24` had started timing out.

**What ran.** `tailscale status`, `ssh -v` banners, `ping` probes against every
candidate host.

**Result.** `robot` @ `100.73.7.24` — **offline, last seen 1 d**. That box held all
P0/P1 work from CA3's brief: `~/botenv` venv, `~/delivery-bot`, the udev rule,
`/dev/rplidar`. Two candidates instead:

| Host | Address | Banner | Outcome |
| --- | --- | --- | --- |
| `raspberrypi` | 100.98.163.85 | OpenSSH 10.0p2 Debian-13 | up, but `robot` key rejected |
| `sherm-raspi` | 100.83.14.99 / 192.168.31.109 | OpenSSH 9.6p1 Ubuntu | up; credentials `robot` / `robot` work |

`sherm-raspi` inventoried in [docs/02_pi_setup.md](../docs/system/02_pi_setup.md): Pi 4B
Rev 1.4, 4 GB, 32 GB card 13 % used, 40.4 °C, **no swap**, ROS 2 Jazzy (205
packages: `ros-base`, `ros-dev-tools`, `foxglove-bridge`, `rosbag2` with MCAP),
empty `~/ros2_ws/src`, CP210x lidar on `1-1.1` → `/dev/ttyUSB0`, `i2c-1` present.

**Blockers found.** `robot` is not in `dialout`, no udev rule, no venv, `pip` is
not installed (`/usr/bin/python3: No module named pip`), no `rplidar` module,
`vcgencmd` cannot open `/dev/vcio` (cosmetic — the tool is not on Ubuntu's default path).

**Access fixed.** Password login works; the Mac's ed25519 key is now in
`~robot/.ssh/authorized_keys`, so key auth works without a password.

**Lesson.** The bare hostname `sherm-raspi` does not resolve on the Mac — mDNS
needs `sherm-raspi.local`, otherwise `ssh: Could not resolve hostname`. Worth an
SSH alias later.

---

## 2026-10-20/21 · P1 lidar bring-up on the old Pi — works, but only 33 % of pings return

**Goal.** Follow CA3 brief P1: identify the lidar, confirm the Pi sees it, run
`test_lidar.py`, read the scan.

**Machine.** `robot` @ `100.73.7.24` (Debian 13, Raspberry Pi OS Lite 64-bit) — **now offline (OI-1)**.
This is the only session run on it; all of it is evidence for how the unit behaves.

**What ran.**

```
lsusb; ls -l /dev/ttyUSB*; groups; vcgencmd get_throttled      # brief step 2
udevadm rules check; ls -l /dev/rplidar                        # brief step 3
python -c "from rplidar import RPLidar; ..."                    # get_info / get_health
python ~/delivery-bot/scripts/test_lidar.py                    # brief step 4
scripts/probe_echo_rate.py                                      # our own diagnostic
```

**Result — hardware answers.**

| Item | Value | Verdict |
| --- | --- | --- |
| USB | `10c4:ea60` Silicon Labs CP210x, bus 001 device 003 | ✅ expected |
| Device | `/dev/ttyUSB0`, `/dev/rplidar -> ttyUSB0` (udev rule present) | ✅ |
| Groups | `robot … dialout …` | ✅ |
| Power | `throttled=0x0` when the lidar started | ✅ no undervoltage |
| `get_info()` | `model: 24` (= A1M8), fw `(1, 29)`, hw `7`, serial `EEA5ECF0…4110` | ✅ |
| `get_health()` | `('Good', 0)` | ✅ |
| Baud | 115200 (256000 not needed) | ✅ |
| Motor | stops on exit (`stop()` / `stop_motor()` / `disconnect()` in `finally`) | ✅ |

**Result — scan behaviour (the problem).**

| Quantity | Measured | Expected |
| --- | --- | --- |
| Rotation rate | 4.9–6.9 Hz | 5–10 Hz ✅ |
| Raw measurement packets / rev | 284 | ~360–400 ⚠️ |
| Returns with a distance | **95–105** | ~350 ❌ |
| **Echo rate** | **33–35 %, stable over 3 runs** | >90 % ❌ |
| Quality of the returns that arrive | median 15, max 15 | strong ✅ |
| Max range seen | 8.5–8.7 m | ~8 m ✅ |

Per 15° sector the echo rate is highly angle-dependent, which is the useful part:

| raw angle | echo % | median dist | Read |
| --- | --- | --- | --- |
| 15–30° | 11 % | **1.31 m** (max 1.32) | flat surface 1.3 m away, returning one ping in nine → **not range, not geometry** |
| 45–75° | 0 % | — | neighbours see 8.46 m → beam escapes through an opening ✅ |
| 120–150° | 66–68 % | 1.8–2.6 m | wall |
| 195–225° | 80–82 % | 0.85 m | best sector in the room |
| 240–255° | 34 % | **0.23 m** | the robot's own mast/cable → candidate `mask_deg` |
| 315–330° | 10 % | 0.56 m | |

**Reading.** Link is clean — angles step smoothly at ~1.27°, no sync errors, no
`Wrong body size` / descriptor exceptions, quality saturates. So the 67 % loss is
photons not coming back, not bytes. No sector exceeds 82 %, so there is a ~20 %
loss floor even on the best wall.

**Script quirk worth remembering.** The brief's `iter_scans(..., min_len=100)`
silently drops every revolution with under 100 valid points — about half of them —
so the printed "scan rate ~0.9 Hz" is an artefact. True rate measured off the
`new_scan` flag is 5–7 Hz. Keep `min_len=5` for diagnostics.

**Next.** Re-run this probe on `sherm-raspi` — different mounting, so it doubles
as a control experiment. If that box's lidar also sits near 35 %, the unit or the
series is the problem; if it jumps to ~90 %, the old mounting was.

**Artefacts.** [evidence/lidar/](../evidence/lidar/) — `2026-10-21_scan_run1.png`,
`2026-10-21_composite_20revs.png`.

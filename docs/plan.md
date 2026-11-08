# Plan

Goal: the robot maps one room once, then drives itself from the taped home mark to
named seats and back, reliably, without human touch during a run.

Odometry has no wheel encoders. `rf2o_laser_odometry` supplies forward speed and yaw
rate from consecutive scans; the MPU6050 supplies yaw rate; the EKF fuses both. That
means the lidar must be trustworthy before anything else is worth tuning.

| Phase | Work | Done when |
| --- | --- | --- |
| 1. Lidar + Foxglove | `lidar.launch.py`, `foxglove_bridge`; run `scan_stats` | `/scan` visible in Foxglove on the Mac; points-per-scan and the missing-points cause understood |
| 2. Drivers + teleop | URDF, IMU node, motor node (dry run → wheels raised → floor); record bags | 2-minute teleop bag replays in Foxglove |
| 3. Calibration | Motor dead zone and gain per side; gyro scale (5 spins vs lidar) | 0.1 m/s straight for 1 m within 10 cm; gyro integrates 5 turns within 5° |
| 4. Odometry | rf2o + EKF tuned on bags | 1 m square within 10 cm; 3 spins heading within 5° |
| 5. Mapping | `slam_toolbox` mapping, launched as a **lifecycle node** — configure, then activate; a plain `Node` leaves it unconfigured, with no `/map` and no error. The rf2o covariance relay must be in place so the EKF actually fuses the gyro. See [`slam.md`](slam.md) | Map saved **and** serialised, walls straight, and the Foxglove SLAM layout shows the pose graph and both paths |
| 6. Localisation + Nav2 | `slam_toolbox` localization, Nav2; the start pose is set over `/initialpose` from Foxglove ("Publish pose estimate") | 5 goals in a row within 15 cm, no collisions, **and** localisation holds after a deliberate 30 cm / 15° wrong start |
| 5b. Autonomous mapping (after the report, not needed for CA3) | `explore.launch.py`, frontier exploration; needs Nav2, hence its place after phase 6 | The robot maps the room unaided and returns home, and the map is comparable to the manual one — dimensions against the tape measure, coverage, return-to-start error |
| 7. Delivery | `save_goal`, `deliver` | Home → seat → home, 5 runs in a row, no human touch |
| 8. SLAM evaluation | Replay-based experiments through `slam_replay.launch.py`; repeatability and the IMU ablation follow [K26] and [M26]. Now feeds the report (E2, E3) and runs on the driven phase 7 runs. See [`slam.md`](slam.md) | Numbers comparable across conditions from the one parameter set, **frozen before 2026-11-06** |
| 9. People in the room (E4, requirement) | The phase 7 route repeated with 1–2 people walking, plus one person stepping in front of the robot. The motor and safety behaviour are the teammate's; this phase needs only that the stop works and the runs are bagged | Arrival error against the empty-room runs, localisation failures, stop distance and any contact recorded |

### Report evidence

The CA3 report is built from the robot work, so each phase feeds one experiment. The
plan itself is [`report_plan.md`](report_plan.md).

| Experiment | Fed by | What it needs |
| --- | --- | --- |
| E1 delivery mission | phase 7 | 5 driven runs home → seat → home, arrival error at the taped checkpoints |
| E2 IMU ablation | phase 8 (build path 9.4) | the E1 bags replayed with and without the gyro, plus one live run each |
| E3 repeatability | phase 8 (build path 9.3) | the same 5 runs: pairwise ATE and map IoU |
| E4 people in the room | phase 9 | the E1 route with people walking and someone stepping in front |
| Hazard table | the safety rules below | each hazard tied to a mitigation and a test that proves it |

All of these use the one frozen config (freeze 2026-11-06) and the checkpoints of
build path 9.1. Phase 5b is not part of the report.

The detail behind phases 5–8 lives in [`slam.md`](slam.md) (SLAM plan, known issues,
evaluation, and the full reference list — [R25], [K26], [M26] are cited from these
phases), [`foxglove/README.md`](foxglove/README.md) (the SLAM layout and its controls)
and [`system/04_architecture.md`](system/04_architecture.md) (pipeline and contracts).

### SLAM section

The SLAM work is done in the order of [`slam_build_path.md`](slam_build_path.md), not
straight down this table: the path splits each phase into the small tasks that actually
teach it, keeps its own Progress list, and records answers and numbers in
[`slam_journal.md`](slam_journal.md). The two plans line up as follows.

| Plan phase | Build-path stages |
| --- | --- |
| 1. Lidar + Foxglove | 0, 1 |
| 2. Drivers + teleop | 2 (URDF only; drivers belong to another section) |
| 4. Odometry | 3, 4 |
| 5. Mapping | 5, 7 |
| 6. Localisation + Nav2 | 6 |
| 5b. Autonomous mapping | 8 |
| 8. SLAM evaluation | 9 (9.2–9.4 feed E1–E3) |
| 9. People in the room | 9.7 (E4) |

## Ground rules

- **A value is not a result until it was measured on the robot.** Placeholders are
  marked `# MEASURE` in the URDF and `drivers.yaml`; leave the marker until the tape
  measure or calibration run replaces it.
- **Bags first, tuning second.** Every rf2o/EKF/Nav2 change must be evaluable from a
  recorded bag without the robot.
- **One difference at a time.** A driver swap and a mounting change in one session
  produce a result nobody can explain.
- **The lidar's missing points are the known open risk.** If about a third of pings
  return no distance, mapping and scan matching both degrade; understand it in
  phase 1 rather than discovering it in phase 5. Mitigated on this Pi: the gaps follow
  the room, and the first map was made despite them (`docs/CA3.md` OI-4, test_log 2026-10-31, 5.4).
- **SLAM parameters are frozen before evaluation runs — one parameter set for all
  conditions.** Tuning each condition separately invalidates the comparison, because
  the difference then measures the tuning rather than the condition.
- Safety: motors only ever reachable through the motor node's watchdog; `dry_run`
  defaults on; first live test with the wheels off the ground.

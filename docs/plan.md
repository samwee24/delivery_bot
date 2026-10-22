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
| 5. Mapping | `slam_toolbox` mapping; save map | Walls straight, furniture recognisable |
| 6. Localisation + Nav2 | `slam_toolbox` localization, Nav2 | 5 goals in a row within 15 cm, no collisions |
| 7. Delivery | `save_goal`, `deliver` | Home → seat → home, 5 runs in a row, no human touch |

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
  phase 1 rather than discovering it in phase 5.
- Safety: motors only ever reachable through the motor node's watchdog; `dry_run`
  defaults on; first live test with the wheels off the ground.

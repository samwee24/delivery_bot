# CA3 report — draft outline

Skeleton only. Write it from [`../notes/notes.md`](../notes/notes.md) and
[`../results/`](../results/) once P1 is clean; do not restate the plan — the plan is
[`../docs/design-plan.md`](../docs/design-plan.md).

## 1. System

- Target: Raspberry Pi 4B Rev 1.4, Ubuntu 24.04.5, ROS 2 Jazzy, standard package stack (D5).
- Sensors: RPLidar A1M8 (serial, 115200), MPU6050 (I2C 0x68); L298N + TT motors.
- Stack: `rplidar_ros` + `rf2o` + `robot_localization` + `slam_toolbox` + Nav2, with
  custom motor and IMU nodes and a URDF; Foxglove for live view; rosbag2 MCAP for
  logs. Decisions D1–D5 in [`../docs/CA3.md`](../docs/CA3.md).

## 2. Sensor characterisation

- A1M8 identity, health, rotation rate, points per revolution.
- **The echo-rate result**: 33–35 % on the original mounting, per-sector breakdown,
  and the two control experiments (50 cm white box; second mounting on `sherm-raspi`)
  with their outcomes.
- Consequence for mapping: what sparsity does to ICP and to the occupancy grid.

## 3. Setup and wiring

- Power separation, common ground, pin map, `mask_deg` provenance.
- Ubuntu-specific deviations from the plan (no `gpiozero` apt path, pip-based GPIO).

## 4. Odometry and fusion

- `rf2o` planar odometry on sparse scans; outlier/gate behaviour.
- `robot_localization` 2D EKF with gyro-z only: 3 spins, heading error vs rf2o alone.

## 5. Mapping

- `slam_toolbox` grid, save/load, `map.png`; walls straight, furniture recognisable.

## 6. Control and safety

- Motion calibration curves; 1 m straight-line test.
- Safety stop zone, watchdogs, kill switch; evidence that each actually fires.

## 7. Navigation and delivery

- Nav2 (RPP + Collision Monitor): 5 goals, error distribution, no collisions.
- Home → seat → home, repeatability.

## 8. What went wrong

Honest list: the 33 % echo rate, the offline Pi, the Ubuntu/Raspberry-Pi-OS split,
the `min_len=100` rate artefact. State what each cost and what it taught.

---

Captions and figures go in [`figures/`](figures/); one line per figure in
`captions.md`, matching CA2's convention.

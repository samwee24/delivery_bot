# 01 · Hardware

Reference. Detail lives in [`design-plan.md`](../design-plan.md) §1 and §4; this page is the
short form plus everything we have **measured** on the real robot.

## Bill of materials

| Part | Key specs | Role |
| --- | --- | --- |
| Raspberry Pi 4B Rev 1.4 | 4 GB, aarch64 | runs everything |
| RPLidar **A1M8** | `model 24`, fw `1.29`, hw `7`, ser. `EEA5ECF0C3E09ED2A0EA98F37D7D4110` | odometry, mapping, obstacle stop |
| CP210x USB adapter | `10c4:ea60` → `/dev/ttyUSB0`, udev alias `/dev/rplidar` | lidar serial, 115200 baud |
| MPU6050 (GY-521) | I2C `0x68`, gyro z for the EKF | `imu_node` reads it at 100.04 Hz at rest (test_log 2026-10-30) and on the robot (test_log 2026-10-31) |
| L298N motor driver | 2 ch, ENA/IN1/IN2 left, ENB/IN3/IN4 right | PWM from GPIO |
| 2WD chassis, TT motors, 65 mm wheels | ~1:48 gearing | differential drive |
| Separate motor battery | 2×18650 (7.4 V) + switch, ground shared with the Pi | keeps motor noise off the Pi |
| UGREEN camera 2K | USB `1bcf:2284`, `/dev/video0`, MJPG up to 2592x1520, `robot` in `video` | live view in Foxglove only, not used by SLAM; config in `camera.yaml` |

## Power

Two systems, one shared ground:

- **Pi + lidar + webcam** ← power bank, USB-C, 5 V 3 A.
- **Motors** ← 18650 pack → switch → L298N `+12V`; pack − → L298N `GND`.
- **Ground link**: L298N `GND` → Pi pin 34. Without it the GPIO has no reference.
- L298N `+5V` jumper **on**, `+5V` terminal **unconnected** — never feed 5 V back into the Pi.
- ENA/ENB jumpers **removed** so the Pi's PWM sets speed.
- 0.1 µF across each motor's terminals; motor wires twisted, away from I2C.

**Order:** Pi booted → motor switch on. Off: motor switch first.

## Pin map

| From | To | Physical | GPIO | Signal |
| --- | --- | --- | --- | --- |
| L298N ENA | Pi | 32 | 12 | left speed (HW PWM) |
| L298N IN1 | Pi | 29 | 5 | left dir A |
| L298N IN2 | Pi | 31 | 6 | left dir B |
| L298N ENB | Pi | 33 | 13 | right speed (HW PWM) |
| L298N IN3 | Pi | 38 | 20 | right dir A |
| L298N IN4 | Pi | 40 | 21 | right dir B |
| L298N GND | Pi | 34 | GND | common ground |
| MPU6050 VCC / GND / SDA / SCL | Pi | 1 / 6 / 3 / 5 | 3V3 / GND / 2 / 3 | power + I2C |
| RPLidar CP210x | USB 2.0 port | — | — | serial + power |

Black USB 2.0 ports only — USB 3 (blue) interferes with 2.4 GHz Wi-Fi.
Buzzer (P8, optional) on GPIO17, physical pin 11.

## Measured on the robot

The robot was built and taped on 2026-10-31 (notes 2026-10-31, "robot built"). Values
below are marked *measured*, *brief default* or MEASURE (not yet done); the URDF
(`delivery_bot_description/urdf/delivery_bot.urdf.xacro`) carries the same values.

| Parameter | Symbol | Value | How measured |
| --- | --- | --- | --- |
| Wheel base | `wheel_base_m` | 0.156, measured 2026-10-31 | left tyre centre → right tyre centre |
| Wheel diameter | `wheel_diameter_m` | MEASURE (65 mm brief default, `wheel_radius` 0.0325 in the URDF) | not measured (notes 2026-10-31) |
| Robot radius | `robot_radius_m` | ~0.12, measured 2026-10-31 (approx) | centre → farthest point |
| Lidar offset | `lidar.offset_xy_m` | x 0.02, y 0.0, z 0.12 m, measured 2026-10-31 (z approx) | tape, lidar centre → midpoint of the four wheels, x forward / y left (notes 2026-10-31) |
| Lidar yaw offset | `lidar.yaw_offset_deg` | 0, measured 2026-10-31 | box test 1.4, two reps: face at +6 and +2.6 deg, spread is hand placement, so 0 is kept (notes 2026-10-31; URDF `laser_yaw` comment: box at 0.39 m, not 0.50 m) |
| Self-occlusion | `lidar.mask_deg` | none needed on current evidence | the 0.23 m returns at raw 230–250° were on the old Pi; on this Pi the near-return bins move between bags, so they follow the scene (notes 2026-10-30 evening); OI-5 resolved after re-mounting (`docs/CA3.md`, 2026-10-31) |
| IMU offset | `imu_x/y/z` | x 0.023, y -0.055, z 0.07 m, measured 2026-10-31 (z approx) | tape, from the wheel midpoint (notes 2026-10-31) |
| IMU axis | which board axis is up | z vertical, inferred 2026-10-31 | hand turn of 360° clockwise read -360.2° on integrated gyro z (test_log 2026-10-31, 3.2 spin) |
| Motor curves | `dead_zone`, `gain` per side | MEASURE | P6 |

## Known mechanical findings

- On the old Pi the A1 sat close enough to the robot's own structure to return **0.23 m** at raw
  angles **230–250°** — mast, cable or post. On this robot the near returns follow the
  scene, not the mount, so no `mask_deg` is set (notes 2026-10-30 evening; OI-5 in
  [`../CA3.md`](../CA3.md)).
- Echo rate was 33–35 % on the old Pi. If that unit is re-used here, check for a
  protective film on the scan window and wipe it with a dry microfibre cloth before
  any mapping work. See [03_bringup.md](03_bringup.md).

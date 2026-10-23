# 01 · Hardware

Reference. Detail lives in [`design-plan.md`](../design-plan.md) §1 and §4; this page is the
short form plus everything we have **measured** on the real robot.

## Bill of materials

| Part | Key specs | Role |
| --- | --- | --- |
| Raspberry Pi 4B Rev 1.4 | 4 GB, aarch64 | runs everything |
| RPLidar **A1M8** | `model 24`, fw `1.29`, hw `7`, ser. `EEA5ECF0C3E09ED2A0EA98F37D7D4110` | odometry, mapping, obstacle stop |
| CP210x USB adapter | `10c4:ea60` → `/dev/ttyUSB0`, udev alias `/dev/rplidar` | lidar serial, 115200 baud |
| MPU6050 (GY-521) | I2C `0x68`, gyro z for the EKF | not yet probed |
| L298N motor driver | 2 ch, ENA/IN1/IN2 left, ENB/IN3/IN4 right | PWM from GPIO |
| 2WD chassis, TT motors, 65 mm wheels | ~1:48 gearing | differential drive |
| Separate motor battery | 2×18650 (7.4 V) + switch, ground shared with the Pi | keeps motor noise off the Pi |
| USB webcam | UVC | unused in v1 |

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

## Measured on the robot — **all still MEASURE**

Nothing has been measured on physical hardware yet. Fill these in with a tape
measure before P6; until then P3–P8 numbers are not comparable to the plan's.

| Parameter | Symbol | Value | How measured |
| --- | --- | --- | --- |
| Wheel base | `wheel_base_m` | MEASURE | left tyre centre → right tyre centre |
| Wheel diameter | `wheel_diameter_m` | MEASURE | nominal 65 mm |
| Robot radius | `robot_radius_m` | MEASURE | centre → farthest point |
| Lidar offset | `lidar.offset_xy_m` | MEASURE | lidar centre → wheel midpoint, x forward / y left |
| Lidar yaw offset | `lidar.yaw_offset_deg` | MEASURE | box at 50 cm test |
| Self-occlusion | `lidar.mask_deg` | candidate `[[230, 250]]` | 0.23 m returns at raw 230–250° on the old Pi |
| IMU axis | which board axis is up | MEASURE | plan assumes z vertical |
| Motor curves | `dead_zone`, `gain` per side | MEASURE | P6 |

## Known mechanical findings

- The A1 sits close enough to the robot's own structure to return **0.23 m** at raw
  angles **230–250°** — mast, cable or post. Plan §3 says top-deck it with nothing
  taller in view; whatever remains goes in `mask_deg`.
- Echo rate was 33–35 % on the old Pi. If that unit is re-used here, check for a
  protective film on the scan window and wipe it with a dry microfibre cloth before
  any mapping work. See [03_bringup.md](03_bringup.md).

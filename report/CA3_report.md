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

> Draft for sections 2, 3 and 5, written by Claude from `docs/test_log.md`,
> `notes/notes.md` and `docs/system/` on 2026-11-03. To be rewritten in the author's
> words. Every number names the log row it came from.

### 2.1 Lidar (RPLIDAR A1M8)

The unit reports `model 24` (A1M8), firmware 1.29, hardware 7, health `('Good', 0)`,
at 115200 baud (`docs/system/03_bringup.md`). The serial link was clean: no sync or
descriptor errors were raised in any run.

**Echo rate.** On the first Pi (`robot` @ 100.73.7.24, 2026-10-21), only 95–105 of
284 pings per revolution came back with a distance. That is an echo rate of 33–35 %
(three runs: 34, 35, 35 %), against more than 90 % expected
(`evidence/lidar/2026-10-21_*.png`). The returns that did arrive were strong (quality
median 15 of 15). A dropped return is reported as distance 0, so the loss happens in
the optics or the room, not on the wire.

Per 15° sector (`probe_echo_rate.py`), the echo rate ranged from 0 % in a sector
looking through an opening to 80–82 % on the best wall. Even that best wall lost
about 20 %, which pointed at the scan window.

The brief's `iter_scans(min_len=100)` dropped every revolution with fewer than 100
valid points. That made the rate read about 0.9 Hz when the true rate was 5–7 Hz.
Diagnostics use `min_len=5` instead.

**Controls.**
- Second mounting, on `sherm-raspi`: 26–29 % no-echo at 7.05 Hz, so roughly 71–74 %
  of pings return. The source is the P1 row of `docs/CA3.md`; the probe command is
  not recorded with that number, so it should be rerun and logged before the report
  quotes it.
- Near returns (under 0.30 m) were binned over three bags on 2026-10-30. The bins
  moved with the scene, so they are the room, not the robot, and no `mask_deg` is
  needed.
- The planned 50 cm white-box echo test was never run as specified. The 1.4 box
  tests done instead checked the lidar's yaw, not its echo rate: face at +6° and
  +2.6°, so `laser_yaw` stays 0.

OI-4 is therefore mitigated but not explained.

**Beam count.** With `angle_compensate` off (the `rplidar_ros` default), each scan
carries a varying number of beams, 1041–1046. slam_toolbox rejected 223 scans of the
first map run with
`LaserRangeScan contains 1041 range readings, expected 931`. Setting
`angle_compensate: True` gives a fixed 720 beams at 0.50°, with 0 rejections after
(commit 4a16fe8, test log 2026-10-31).

**Scale against tape.** Raw `/scan` ranges at two poses summed to 1.085 m against a
1.05 m tape gap (+3.5 cm) and 1.494 m against 1.48 m (+1.4 cm) (test log 2026-10-31,
`lr.sh`).

**Consequence for mapping.** The scans are sparse, but walls still show as dotted
arcs. slam_toolbox's correlative matcher and rf2o's range flow both still had
enough to work on: the first map closed its loop within 0.109 m over 42 m
(Section 5).

### 2.2 IMU (MPU6050)

At rest, before the robot was built (2026-10-30, `imu_node`):
- rate 100.04 Hz;
- gyro bias z −0.0279 rad/s, removed at start-up;
- after bias removal, z std 0.00175 rad/s (variance 3.1e-6).

Accel z reads 11.16 m/s² against 9.81, 14 % high. The scale is not calibrated, and
the EKF uses only gyro z, so this does not matter here.

On the built robot (2026-10-31), a hand-turned 360° read −360.2° on the gyro
integral, within 0.06 %. `gyro_scale_z` therefore stays 1.0 (one run). The fitted
`gyro_var` is 1e-4, about 60 times the at-rest variance as margin
(test log 2026-10-31, 4.4).

### 2.3 Camera

The UGREEN 2K USB camera is for live viewing only; SLAM does not use it. The Pi
decodes its MJPEG in software on one core, so the delivered rate is capped at about
11.6 Mpixel/s:
- 1280x720 at 10 fps delivers 10.0 Hz;
- 1920x1080 delivers only 4.5–5.7 Hz.

Under SLAM replay load, the camera made the EKF miss its update deadline 8–26 times
in 65 s, against 0 without it (test log 2026-10-31). Keep the camera off while
mapping.

## 3. Setup and wiring

**Power.** There are two supplies with one shared ground (`docs/wiring.md`):
- the Pi, lidar and camera run from a 5 V 3 A power bank;
- the motors run from a 2×18650 pack, through the kill switch, into the L298N 12 V
  input.

L298N GND goes to Pi pin 34. The L298N 5 V jumper is on, but its +5 V terminal is
left unconnected, so nothing feeds back into the Pi. The ENA/ENB jumpers are removed
so that PWM sets the speed.

The kill switch is the motor battery switch: software cannot override a stuck L298N
channel.

**Pin map (BCM).**

| Signal | GPIO |
| --- | --- |
| Left ENA / IN1 / IN2 | 12 / 5 / 6 |
| Right ENB / IN3 / IN4 | 13 / 20 / 21 |

The MPU6050 is on 3.3 V, I2C bus 1, address `0x68`.

**Mounting (measured 2026-10-31, tape, from the midpoint of the four wheels).**
- Lidar: 2 cm forward, centred, 12 cm up.
- IMU: 2.3 cm forward, 5.5 cm right, 7 cm up.
- Wheel base: 0.156 m.
- Robot radius: about 0.12 m.

The wheel radius, 0.0325 m, is the TT default and has not been measured. The robot
has four wheels and steers by skidding, so 0.156 m is only a first guess for the
effective track width. All of these values are in the URDF.

**`mask_deg`.** On the old mounting, a 0.23 m return at raw 230–250° was a candidate
for masking. After the re-mount, the near returns followed the scene (Section 2.1),
so no mask is set (OI-5, resolved).

**Ubuntu deviations from the plan (D1).** The build target runs Ubuntu 24.04, not
Raspberry Pi OS, so `raspi-config`, `/boot/firmware/config.txt` and apt `gpiozero`
are not available. `motor_node` uses gpiozero with `LGPIOFactory`; `lgpio` is in
`/usr/lib/python3/dist-packages`, and `RPi.GPIO` is absent on aarch64. There is no
venv, because the apt ROS stack covers the dependencies (`docs/system/02_pi_setup.md`).

**Brown-outs.** The portable power bank has caused real faults:
- the lidar hung at start (OI-6);
- a bag was lost when the battery went flat (2026-11-01);
- the Pi read `throttled=0x50005`, under-voltage, on 2026-11-02.

The motors have not yet been driven by us (P2 belongs to the teammate).

## 4. Odometry and fusion

- `rf2o` planar odometry on sparse scans; outlier/gate behaviour.
- `robot_localization` 2D EKF with gyro-z only: 3 spins, heading error vs rf2o alone.

## 5. Mapping

**Run.** The robot was pushed by hand around the room from a taped start mark and
back to it, with `slam_toolbox` in mapping mode on top of the base stack
(rf2o → EKF), recorded to `~/bags/2026-10-31_map_200956`. The map was saved with
`map_saver_cli` and serialised as a pose graph for localisation (test log 2026-10-31,
5.4).

**Result.** `results/maps/2026-10-31_room2.png`: 317 x 233 cells at 0.05 m, 65.5 m²
free, 4375 occupied cells. Walls and furniture are recognisable. The regular grid of
star-shaped dots on the floor is office chair bases and table legs, which Nav2
should treat as obstacles; at first these were wrongly taken for the person pushing.
On one tape gap the map read 1.00 m against 1.05 m (−5 cm, one cell). The second gap
has not been read from the map yet, so 5.4 stays open.

**The first attempt failed.** It came out as a 184 x 112 fan because of the varying
beam count (Section 2.1). This was the most useful single fix of the SLAM work.

**Parameter sweep (5.5).** Five replays of the map bag, changing one parameter each
time (test log 2026-10-31). Closure is the distance between the first and last poses
of the 42 m route, which starts and ends on the same mark.

| Variant | Closure | Occupied cells |
| --- | --- | --- |
| Baseline (`min_laser_range` 0.15, loop closing on, `minimum_travel_distance` 0.1) | 0.109 m | 4087 |
| `min_laser_range` 0 | 0.123 m | 3721 |
| Loop closing off | 0.658 m | 4285 |
| `minimum_travel_distance` 0.05 | 0.186 m | 4169 |
| `minimum_travel_distance` 0.2 | 0.113 m | 3468 |

Loop closing is the only setting that matters (×6 closure error without it). The
others land within about 1–8 cm on one run each, which is not a difference.
`slam_mapping.yaml` is frozen at the baseline (commit 6484678). A rerun at EKF 20 Hz
gave 0.115 m, inside the ~1 cm run-to-run spread, but that run was confounded by
stale processes and needs repeating on a quiet Pi.

**Caveat (OI-8).** rf2o later under-read straight pushes by 76 % on bags recorded
after the 720-beam change. Whether the map run was affected is not known. If it was,
slam_toolbox's scan matching and loop closure corrected for it: the map scale agrees
with tape to one cell. The cause is still under test (`docs/test_log.md`, 2026-11-02
rows).

**Localisation on the saved map** (`navigation.launch.py`, 2026-11-01). The live scan
sits on the saved map. A 30 cm / 20° wrong start converged after a short push; a
30 cm / 31° start did not. That fits the matcher's 20° coarse heading window
(`coarse_search_angle_offset` 0.349 rad). This belongs to Section 7 once Nav2 runs.

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

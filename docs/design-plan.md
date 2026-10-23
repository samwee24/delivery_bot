# Room Delivery Robot — Implementation Plan

Oct 8, 2026 · @Someone

> **Superseded in part.** The brief permits packages: v1 now runs the standard ROS 2
> stack (D5, 2026-10-22) — see [`docs/CA3.md`](CA3.md) and
> [`docs/07_ros_stack.md`](system/07_ros_stack.md). The goals, wiring, safety rules and
> test gates below still stand; the "no ROS", KISS-ICP and own-maths implementation
> sections are historical.

## 0. Overview

The robot maps a small room once, then drives itself from a known start point to any named spot in that map. Everything runs in pure Python on a Raspberry Pi 4B, with no ROS. Delivery features (buzzer, multiple stops) come only after mapping and navigation work reliably.

### Goals

1. **Map the room.** Build a 2D occupancy grid (5 cm cells) by driving the robot around by keyboard.
2. **Know where it is.** Estimate pose (x, y, heading) by fusing lidar odometry (KISS-ICP) with the MPU6050 gyro in an extended Kalman filter (EKF).
3. **Drive to a goal.** Plan a collision-free path with A\* and follow it with a pure-pursuit controller, stopping for anything in the way.
4. **Deliver.** Visit named spots (people's seats) and return home. Buzzer on arrival is optional and last.

### Scope and key decisions

- **No wheel encoders.** Lidar odometry replaces them; the gyro covers fast turns, where scan matching is weakest.
- **No loop closure in v1.** The robot always starts from the same taped "home" mark on the floor, so the map and every session share one coordinate frame. In a small room, drift over a single session is small enough to ignore.
- **Webcam is unused in v1.** It is reserved for later phases. No ArUco tags and no buttons anywhere in this plan.
- **Slow and safe.** Top speed 0.15 m/s; the robot stops if anything is within 20 cm ahead.
- **Record everything.** Every drive is logged (lidar, IMU, motor commands) so odometry, the EKF and mapping can be tuned on a laptop by replaying logs, without the robot.

### Phases

Each phase ends with a test the team can see pass before moving on.

| Phase | What gets built | Done when |
| --- | --- | --- |
| P0 Setup | Pi OS, SSH, Python venv, I2C and serial enabled | `python -c "import kiss_icp, rplidar, smbus2"` runs on the Pi |
| P1 Bring-up | Motor test, IMU read and gyro calibration, lidar scan plot | Each wheel spins both ways; gyro reads about 0 deg/s at rest after bias removal; a scan of the room plots correctly |
| P2 Teleop and logging | Keyboard driving over SSH; logger for all sensors and commands | A 2-minute drive replays on the laptop with matching scans and IMU |
| P3 Lidar odometry | KISS-ICP on replayed logs, then live | Drive a 1 m square and stop where you started: end-point error under 10 cm |
| P4 EKF fusion | 5-state EKF fusing KISS-ICP pose and gyro rate | Spin in place 3 full turns: heading error under 10 degrees, better than KISS-ICP alone |
| P5 Mapping | Log-odds occupancy grid; save and load map | Saved map PNG shows walls straight and furniture recognisable |
| P6 Motion calibration | PWM-to-speed curves, dead zone, left/right trim | Commanded 0.1 m/s straight drive goes 1 m within 10 cm and 10 degrees |
| P7 Navigation | Obstacle inflation, A\*, path smoothing, pure pursuit, safety stop | Robot reaches 5 goals in a row within 15 cm, with no collisions |
| P8 Delivery loop | Named goals file, go-to-goal, wait, return home; buzzer optional | Home to seat to home, 5 runs in a row, no human touch |

Later, optional: scan-to-map matching to remove drift, Kalman tracking of people walking around, camera features.

## 1. Materials

The hardware you already have is enough; the additions are batteries, mounting parts and small electronics, none of them large. The most important addition is a **separate battery for the motors**, so motor noise and current spikes never reset the Pi.

### Already have

| Part | Key specs | Role |
| --- | --- | --- |
| Raspberry Pi 4B | Quad-core, 64-bit; 4 GB RAM recommended | Runs everything: sensors, odometry, EKF, mapping, planning, control |
| RPLidar (likely A1M8) | 360 deg, about 0.15 to 12 m range, about 5.5 to 10 Hz scans, 5 V over USB | Main sensor: odometry (KISS-ICP), mapping, obstacle stop |
| MPU6050 (GY-521 board) | 3-axis gyro and accel, I2C address 0x68 | Yaw rate for the EKF |
| L298N motor driver | 2 channels, up to 2 A each, 5 to 35 V motor supply, drops about 2 V | Drives both TT motors from Pi PWM |
| 2WD chassis, 2 TT gear motors, 65 mm wheels, caster | Motors rated 3 to 6 V, typically 1:48 gearing | Differential drive base |
| USB webcam | Any UVC webcam | Not used in v1; reserved for later phases |

Check the exact lidar model printed on its base; the code below assumes an A1-series unit with the USB adapter board.

### To get (all small and cheap)

| Part | Qty | Why |
| --- | --- | --- |
| microSD card, 32 GB, class A1 or A2 | 1 | Raspberry Pi OS 64-bit |
| USB power bank, 10,000 mAh or more, rated **5 V 3 A** output | 1 | Powers the Pi and, through the Pi's USB, the lidar. Under 3 A causes undervoltage throttling |
| Short USB-C cable, thick gauge | 1 | Pi power; thin cables drop voltage |
| 18650 Li-ion cells, protected | 2 | Motor battery: 2 in series = 7.4 V nominal, 8.4 V full. After the L298N's about 2 V drop, the motors see about 5.4 to 6.4 V |
| 2-cell 18650 holder (series) with leads | 1 | Holds the motor battery |
| 18650 charger | 1 | Charging the cells. Alternative to all three: a 6xAA NiMH holder (7.2 V) |
| Small rocker or slide switch | 1 | Motor power on/off, so the robot can be killed instantly |
| 0.1 uF ceramic capacitors | 2 to 6 | Soldered across each motor's terminals to cut electrical noise |
| Jumper wires, female-female and male-female | 1 pack each | Pi to L298N and Pi to IMU |
| M3 brass standoffs (30 to 40 mm), screws, nuts | 1 kit | Second deck to lift the lidar above everything |
| Top deck plate (acrylic, plywood, stiff card or 3D print) | 1 | Lidar mounts here, with a clear 360 deg view |
| Pi 4 heatsinks and a small 5 V fan | 1 set | Pi 4 throttles under sustained load without cooling |
| Double-sided foam tape and zip ties | Some | Mount the IMU firmly and flat; tidy wiring |
| Painter's tape and a tape measure | 1 each | Mark the home pose on the floor; measure wheel base and test distances |
| Active buzzer module, 3.3 V | 1 | Optional, phase P8 only |

### Robot parameters to measure before coding

- **Wheel base** (centre of left tyre to centre of right tyre), in metres.
- **Wheel diameter** (nominally 65 mm; measure your tyres).
- **Lidar offset** from the midpoint between the wheels (x forward, y left), and which way the lidar's 0 deg mark points.
- **IMU orientation**: which board axis points up. The code assumes the z axis is vertical.

## 2. Pipeline

One Python process does everything: sensor threads feed the latest lidar scan and gyro reading into a main loop, which estimates pose, updates the map, plans and drives. The robot has two modes that share the same estimation stack: **mapping mode** (you drive by keyboard, the map is built) and **navigation mode** (the map is loaded and frozen, the robot drives itself).

### Rates and threads

| Stage | Rate | Runs in |
| --- | --- | --- |
| Lidar read | 5.5 to 10 Hz (one full scan per rotation) | Lidar thread |
| Gyro read | 100 Hz | IMU thread |
| EKF predict and gyro update | 100 Hz | IMU thread (EKF guarded by a lock) |
| KISS-ICP and EKF lidar update | Once per scan | Main loop |
| Map update | Once per scan (mapping mode only) | Main loop |
| Path planning | On a new goal, or when blocked | Main loop |
| Controller and motor command | 20 Hz | Main loop |
| Telemetry to laptop | 5 Hz | Main loop |

Threads share data through a small state object with a lock; each queue keeps only the newest item, so a slow stage never works on stale data.

### Stage 1: Lidar input

- Read full rotations with the `rplidar` library; each point is (quality, angle in degrees, distance in mm).
- Drop points with distance 0, under 0.15 m, over 8 m, or quality 0. Drop any angle sectors blocked by the robot's own posts (a mask set in config).
- RPLidar angles run **clockwise**; negate them so angles follow the usual counter-clockwise convention, then shift by the lidar's mounting offset into the robot frame (x forward, y left).
- Stamp each point with time: scan start time plus its fraction of the rotation times the scan period. KISS-ICP needs this for deskewing later.

### Stage 2: Gyro input

- Wake the MPU6050 (write 0 to register 0x6B), set its digital low-pass filter to about 44 Hz (register 0x1A = 3), keep the gyro at plus or minus 250 deg/s (131 counts per deg/s).
- Read gyro z (registers 0x47 and 0x48) at 100 Hz and convert to rad/s.
- **Bias calibration at every start:** keep the robot still for 3 s, average the readings, subtract that bias from every later reading. The program refuses to start if the robot moves during calibration (reading spread too large).

### Stage 3: Lidar odometry (KISS-ICP)

- Build an N x 3 numpy array per scan (x, y, z = 0) and call `register_frame(points, timestamps)`.
- Config to start: max range 8 m, min range 0.15 m, voxel size 0.05 m, deskew off. Turn deskew on once timestamps are verified in P3.
- Take only **x, y and yaw** from the returned 4 x 4 pose. A 2D scan cannot constrain height, roll or pitch, so those are ignored.
- Reject a result as an outlier if it jumps more than 0.3 m or 30 deg since the last scan; at 0.15 m/s that cannot be real motion.
- KISS-ICP is built for 3D lidar. If it misbehaves on flat scans, swap in the fallback `icp2d.py` (a simple numpy 2D ICP) behind the same interface; nothing else changes.

### Stage 4: Pose fusion (EKF)

State: position x, y (m), heading theta (rad), forward speed v (m/s), turn rate omega (rad/s). The prediction step assumes constant speed and turn rate over each small time step dt:

```latex
\begin{aligned}
x_{k+1} &= x_k + v_k \cos\theta_k\,\Delta t \\
y_{k+1} &= y_k + v_k \sin\theta_k\,\Delta t \\
\theta_{k+1} &= \theta_k + \omega_k\,\Delta t \\
v_{k+1} &= v_k, \quad \omega_{k+1} = \omega_k
\end{aligned}
```

- **Gyro update** (100 Hz): measures omega directly. Starting noise: standard deviation 0.02 rad/s.
- **Lidar update** (per scan): measures x, y, theta from KISS-ICP. Starting noise: 3 cm for x and y, 2 deg for theta.
- **Process noise** lets v and omega change: start with 0.3 m/s^2 and 1.0 rad/s^2 as standard deviations, then tune from replayed logs.
- Always wrap the heading error to between minus pi and pi before an update, or the robot will think it turned a full circle.
- KISS-ICP starts at the home mark, so its frame, the EKF frame and the map frame are all the same frame in v1.

### Stage 5: Mapping (mapping mode)

- Log-odds occupancy grid, 5 cm cells, 12 x 12 m (240 x 240 cells), with home at the centre.
- For each beam from the fused pose: cells along the ray get minus 0.4 (free), the end cell gets plus 0.85 (occupied), values clamped to plus or minus 4. Beams at max range mark free space only.
- Trace rays in vectorised numpy (sample each ray every half cell, de-duplicate cells) so a full scan updates in milliseconds.
- Save as `map.npy` plus `map.yaml` (resolution, origin, size) plus `map.png` for viewing. A cell is occupied above probability 0.65, free below 0.35, unknown in between.

### Stage 6: Planning (navigation mode)

- Treat occupied **and unknown** cells as blocked, so the robot never plans through unseen space.
- Inflate blocked cells by the robot's radius plus 5 cm (`scipy.ndimage.binary_dilation`). Add a cost that rises near walls (from `distance_transform_edt`) so paths run down the middle of gaps.
- A\* on an 8-connected grid from the current cell to the goal cell.
- Smooth the path by cutting corners wherever a straight line stays in free space, then resample it every 10 cm.

### Stage 7: Control

- **Pure pursuit:** pick the path point 0.25 m ahead, steer toward it with curvature 2 sin(alpha) / L, where alpha is the angle to that point and L the lookahead.
- Forward speed up to 0.15 m/s, slowing on tight curves and in the last 0.3 m; turn rate capped at 1.0 rad/s.
- If the path points more than 60 deg away from the current heading, turn in place first.
- Goal reached within 10 cm.
- Wheel speeds: left = v minus omega times wheel base / 2, right = v plus omega times wheel base / 2. Each wheel speed maps to PWM duty through the calibration from P6: duty = dead zone + gain x speed, with separate numbers for each side, capped at 85%.

### Stage 8: Safety (always on)

- Any lidar point within 20 cm in the front plus or minus 35 deg: stop. Blocked for more than 3 s: add the obstacle to the planning grid and replan.
- No motor command for 0.5 s, or no lidar scan for 0.5 s: motors off.
- Ctrl+C or any crash: a handler sets both PWMs to 0 before exit.
- The motor battery switch is the physical kill switch.

### Telemetry and debugging

- The Pi publishes pose, latest scan, path and occasional map snapshots over ZeroMQ at 5 Hz. A matplotlib viewer on a laptop shows them live; the Pi itself runs headless.
- The logger records raw scans, gyro readings and motor commands to disk. `replay.py` feeds a log through the same odometry, EKF and mapping code on the laptop, which is how all tuning is done.

## 3. Code structure and packages

The code is one Python package (`bot/`) plus one small script per phase, so each phase can be tested on its own. All robot numbers live in YAML config files, never in code.

### Repository layout

```
delivery-bot/
  config/
    robot.yaml           wheel base, wheel size, lidar offset and angle mask, pins, motor calibration
    ekf.yaml             EKF noise values
    goals.yaml           named poses, e.g. home, seat_1 (P8)
  bot/
    state.py             shared state object, locks, newest-item queues
    hw/
      lidar.py           lidar thread: scans to robot-frame points with timestamps
      imu.py             MPU6050 driver, bias calibration, 100 Hz thread
      motors.py          L298N driver: set(duty_left, duty_right), stop()
      buzzer.py          optional (P8)
    estimation/
      lidar_odom.py      KISS-ICP wrapper: returns x, y, yaw; outlier gate
      icp2d.py           fallback 2D ICP, same interface
      ekf.py             5-state EKF: predict, update_gyro, update_pose
    mapping/
      occupancy_grid.py  log-odds grid, ray tracing, save/load
    planning/
      costmap.py         inflation and near-wall cost
      astar.py           A*, shortcut smoothing, resampling
    control/
      pure_pursuit.py    path to (v, omega)
      drive.py           (v, omega) to wheel speeds to PWM duty
      safety.py          front stop zone, watchdogs
    io/
      logger.py          records scans, gyro and commands
      telemetry.py       ZeroMQ publisher to the laptop
    utils/
      geometry.py        angle wrap, 2D transforms
  scripts/               run on the Pi, one per phase
    test_motors.py       P1
    test_imu.py          P1
    test_lidar.py        P1: save one scan as an image
    teleop.py            P2: keyboard drive and log
    run_odometry.py      P3/P4: live pose printout
    map_room.py          P5: teleop plus live mapping, saves map
    calibrate_motion.py  P6
    navigate.py          P7: go to x, y or a named goal
    save_goal.py         P8: store current pose under a name
    deliver.py           P8: home to goal to home
  tools/                 run on the laptop
    replay.py            run a log through odometry, EKF, mapping
    viewer.py            live matplotlib view of telemetry
  logs/
  maps/
  requirements-pi.txt
  requirements-laptop.txt
```

### Python packages

| Package | Used for | Where |
| --- | --- | --- |
| `numpy` | All maths, point arrays, grids | Pi and laptop |
| `scipy` | Map inflation and wall distance (`ndimage`), nearest neighbours in fallback ICP (`spatial`) | Pi and laptop |
| `kiss-icp` | Lidar odometry | Pi and laptop |
| `rplidar-roboticia` (imported as `rplidar`) | Reading the RPLidar over USB serial | Pi |
| `smbus2` | Reading the MPU6050 over I2C | Pi |
| `gpiozero` with `lgpio` | PWM and direction pins for the L298N | Pi (installed through apt) |
| `pyyaml` | Config files | Pi and laptop |
| `pyzmq` | Telemetry from Pi to laptop | Pi and laptop |
| `msgpack` | Compact log files | Pi and laptop |
| `matplotlib` | Viewer, map images, tuning plots | Laptop (and Pi for saving PNGs) |

The EKF, A\*, pure pursuit and mapping are written by the team with numpy only; no extra libraries are needed for them. Teleop uses Python's built-in `curses` over SSH.

### Pi setup (P0)

1. Flash **Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager; set hostname, Wi-Fi, user and enable SSH in the Imager settings.
2. `sudo raspi-config` → Interface Options → enable **I2C**. For faster IMU reads, add `dtparam=i2c_arm_baudrate=400000` to `/boot/firmware/config.txt`.
3. `sudo usermod -aG dialout,i2c,gpio $USER`, then reboot (gives access to the lidar's serial port, I2C and GPIO without sudo).
4. `sudo apt install python3-venv python3-dev build-essential cmake i2c-tools python3-gpiozero python3-lgpio`
5. `python3 -m venv --system-site-packages ~/botenv` (so the apt-installed GPIO libraries are visible), activate it, then `pip install -r requirements-pi.txt`. If `kiss-icp` has no prebuilt wheel for the Pi, pip compiles it; allow 10 to 30 minutes.
6. Checks: `i2cdetect -y 1` shows `68`; the lidar appears as `/dev/ttyUSB0` when plugged in.

### Starting config

```yaml
# config/robot.yaml (values marked MEASURE must be measured on your robot)
wheel_base_m: 0.13          # MEASURE
wheel_diameter_m: 0.065     # MEASURE
robot_radius_m: 0.10        # MEASURE: centre to farthest point
lidar:
  port: /dev/ttyUSB0
  offset_xy_m: [0.0, 0.0]   # MEASURE: lidar centre relative to wheel midpoint
  yaw_offset_deg: 0.0       # MEASURE: where the lidar's 0 deg points
  min_range_m: 0.15
  max_range_m: 8.0
  mask_deg: []              # e.g. [[170, 190]] to ignore a post behind
imu:
  bus: 1
  address: 0x68
  rate_hz: 100
  calib_seconds: 3
motors:
  pins: {ena: 12, in1: 5, in2: 6, enb: 13, in3: 20, in4: 21}
  pwm_hz: 1000
  max_duty: 0.85
  dead_zone: {left: 0.35, right: 0.35}   # set in P6
  gain: {left: 2.0, right: 2.0}          # duty per m/s, set in P6
control:
  v_max: 0.15
  omega_max: 1.0
  lookahead_m: 0.25
  goal_tol_m: 0.10
safety:
  stop_dist_m: 0.20
  stop_half_angle_deg: 35
  watchdog_s: 0.5
map:
  resolution_m: 0.05
  size_m: 12.0
```

## 4. Wiring

There are two separate power systems that share only a ground wire: the power bank runs the Pi and everything on its USB ports, and the 18650 pack runs the motors through the L298N. The Pi talks to the L298N with six GPIO lines and to the MPU6050 over I2C.

&#91;embedded content: wiring · Pi, L298N, sensors and two power sources\]

Thick lines carry power; thin lines carry signals. The only link between the motor pack and the Pi side is the ground wire from L298N GND to Pi pin 34.

### Power

- **Pi:** power bank USB-C (5 V, 3 A) into the Pi's USB-C port.
- **Lidar and webcam:** plugged into the Pi's USB ports, powered by the Pi.
- **Motors:** 18650 pack plus → switch → L298N `+12V` terminal. Pack minus → L298N `GND` terminal.
- **Common ground:** a wire from the L298N `GND` terminal to a Pi GND pin. Without it the GPIO signals have no reference and the motors behave randomly.
- **L298N 5 V jumper:** leave it **on** (the pack is under 12 V, so the board makes its own 5 V logic supply). Leave the L298N `+5V` terminal **unconnected**. Never connect it to the Pi.
- Remove the **ENA and ENB jumpers** on the L298N so the Pi's PWM controls speed.

### Pin map

| From | To | Pi physical pin | Pi GPIO | Signal |
| --- | --- | --- | --- | --- |
| L298N ENA | Pi | 32 | GPIO12 | Left motor speed (hardware PWM capable) |
| L298N IN1 | Pi | 29 | GPIO5 | Left motor direction A |
| L298N IN2 | Pi | 31 | GPIO6 | Left motor direction B |
| L298N ENB | Pi | 33 | GPIO13 | Right motor speed (hardware PWM capable) |
| L298N IN3 | Pi | 38 | GPIO20 | Right motor direction A |
| L298N IN4 | Pi | 40 | GPIO21 | Right motor direction B |
| L298N GND | Pi | 34 | GND | Common ground (also to pack minus) |
| MPU6050 VCC | Pi | 1 | 3.3 V | IMU power |
| MPU6050 GND | Pi | 6 | GND | IMU ground |
| MPU6050 SDA | Pi | 3 | GPIO2 (SDA1) | I2C data |
| MPU6050 SCL | Pi | 5 | GPIO3 (SCL1) | I2C clock |
| L298N OUT1, OUT2 | Left motor | — | — | Left motor terminals |
| L298N OUT3, OUT4 | Right motor | — | — | Right motor terminals |
| RPLidar USB adapter | Pi USB port | — | — | Lidar data and power |
| Webcam | Pi USB port | — | — | Unused in v1 |
| Buzzer I/O (optional) | Pi | 11 | GPIO17 | Buzzer on/off (P8) |
| Buzzer VCC, GND (optional) | Pi | 17, 9 | 3.3 V, GND | Buzzer power |

The L298N accepts the Pi's 3.3 V signals as logic high, so no level shifter is needed. The MPU6050's XDA, XCL, AD0 and INT pins stay unconnected.

### Mechanical layout

- **Bottom deck:** motors, L298N, 18650 pack and switch, with the battery low and central for stability.
- **Middle:** Pi (with heatsinks and fan) and power bank. MPU6050 taped flat with foam tape, as close to the midpoint between the wheels as possible, its z axis pointing up.
- **Top deck, on standoffs:** lidar alone, centred over the wheel axle if possible, with nothing taller than it anywhere on the robot. Cable and standoff positions that still block some angles go in `mask_deg` in config.
- Solder a 0.1 uF capacitor across each motor's two terminals. Keep motor wires twisted and away from the I2C wires.

### Checks before the first power-on

- [ ] Motor switch **off**, power bank unplugged.
- [ ] Multimeter: no short between pack plus and minus at the L298N terminals.
- [ ] L298N `+5V` terminal unconnected; ENA and ENB jumpers removed.
- [ ] Ground wire present from L298N `GND` to Pi pin 34.
- [ ] MPU6050 on 3.3 V (pin 1), not 5 V.
- [ ] Robot raised on a box so the wheels spin freely for `test_motors.py`.
- [ ] Power order: Pi first and booted, then motor switch on. Off: motor switch first.
- [ ] If a wheel spins the wrong way, swap that motor's two wires at the OUT terminals.

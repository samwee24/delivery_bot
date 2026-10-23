# CA3 — room delivery robot: project record

Development log, evidence and documentation for CA3, kept in the same repository as
the code so the notes cannot drift from the system they describe. The design plan
lives in [design-plan.md](design-plan.md) and is superseded where noted below.

## Target machine (resolved 2026-10-22)

**`robot@sherm-raspi`** — Raspberry Pi 4B Rev 1.4, 4 GB, Ubuntu 24.04.5 LTS,
kernel `6.8.0-1065-raspi`, Python 3.12.

| | value |
| --- | --- |
| LAN | `192.168.31.109`, also `sherm-raspi.local` (the bare name `sherm-raspi` does **not** resolve) |
| Tailscale | `100.83.14.99` (tailnet owned by `chloe.tan.yi.ling@`) |
| Login | user `robot`, password `robot`; the Mac's key is in `authorized_keys` |
| ROS | ROS 2 **Jazzy** in `/opt/ros/jazzy`, `foxglove_bridge` and `rosbag2` (MCAP) installed |

### Decisions

| # | Decision | Date | Consequence |
| --- | --- | --- | --- |
| D1 | Build target is `sherm-raspi`, not the CA3 brief's Debian Pi | 2026-10-22 | Ubuntu, not Raspberry Pi OS: no `raspi-config`, no `/boot/firmware/config.txt`, no apt `gpiozero`/`lgpio` |
| D2 | **ROS 2 Jazzy is in scope** | 2026-10-22 | `design-plan.md` §0 "no ROS" is superseded — see [system/07_ros_stack.md](system/07_ros_stack.md) |
| D3 | **Foxglove Studio for live visualisation** | 2026-10-22 | The plan's ZeroMQ telemetry + `tools/viewer.py` is replaced by ROS 2 topics + `foxglove_bridge` |
| D4 | Keep the pure-Python maths stack | 2026-10-22 | EKF, A\*, pure pursuit and the occupancy grid stay as numpy modules, run inside ROS nodes — not bought from Nav2 in v1. **Superseded by D5.** |
| D5 | **`rf2o_laser_odometry` → `robot_localization` EKF replaces KISS-ICP + our own filter** | 2026-10-22 | Range-flow odometry is a better fit for a sparse 2D scan than ICP, and it outputs velocity, which is what the EKF wants. Cost: P3/P4 now measure `robot_localization` tuning, not code we wrote; drift behaviour is unchanged because there is still no absolute position input. `rf2o` runs with `publish_tf: false` — the EKF alone owns `odom → base_footprint`. |
| D6 | **Code lives in `~/ros2_ws/src/delivery_bot`** (git, commit `9e2fd2e`), not in this folder | 2026-10-22 | Packages: `bringup`, `description`, `drivers`, `mission`. Third-party `rf2o` is cloned alongside, outside the repo, pinned by branch/commit. This folder remains the documentation and evidence home. |
| D5 | **Standard ROS 2 package stack** in v1 — `rplidar_ros`, `rf2o_laser_odometry`, `robot_localization`, `slam_toolbox`, Nav2 | 2026-10-22 | Supersedes D4's own-maths scope (brief permits packages); `kiss-icp` dropped. We write only: motor node, IMU node, URDF, Simple Commander delivery script. Own maths documented as fallback — see [system/07_ros_stack.md](system/07_ros_stack.md) and the 2026-10-22 D5 entry in [notes.md](../notes/notes.md) |

What this costs: no venv exists yet, `pip` is not installed, `robot` is not in
`dialout`, there is no udev rule, and the `rplidar` Python module is absent.

## Status

| Phase | What it proves | Status |
| --- | --- | --- |
| **P0 Setup** | Python env, serial access, I2C, GPIO | **In progress** — see [docs/02_pi_setup.md](system/02_pi_setup.md) |
| **P1 Bring-up** | Motors both ways, gyro calibrated, lidar plot | **Partial** — lidar verified on the old Pi, echo rate only 33 % (see OI-4); motors and IMU untouched |
| **P2 Teleop + logging** | 2-minute drive replays on the laptop | Not started |
| **P3 Lidar odometry** | `rf2o`: 1 m square closes within 10 cm | Not started |
| **P4 EKF fusion** | `robot_localization` (2D): 3 spins, heading error under 10° | Not started |
| **P5 Mapping** | `slam_toolbox` occupancy grid with recognisable walls | Not started |
| **P6 Motion calibration** | 1 m straight within 10 cm and 10° | Not started |
| **P7 Navigation** | Nav2: 5 goals, 15 cm, no collisions | Not started |
| **P8 Delivery loop** | Home → seat → home ×5 | Not started |

## Open issues

| # | Issue | Effect | Next |
| --- | --- | --- | --- |
| OI-1 | `robot` @ `100.73.7.24` offline since 2026-10-21 | Everything from the brief (venv, `~/delivery-bot`, udev rule) is unreachable | Confirm whether that box is retired or just off |
| OI-2 | `raspberrypi` @ `100.98.163.85` online, same Debian build, key rejected | Unknown whether it is the same machine reflashed | `ssh-copy-id` if needed |
| OI-3 | `sherm-raspi` has no venv, no `pip`, no udev rule, user not in `dialout` | Cannot read `/dev/ttyUSB0` as `robot` | [docs/02_pi_setup.md](system/02_pi_setup.md) to-do list |
| OI-4 | Lidar returns a distance for only **33–35 %** of pings | Sparse scans; mapping quality at risk | [docs/03_bringup.md](system/03_bringup.md) and the 50 cm white-box test |
| OI-5 | Unit is 0.23 m from the robot's own structure at raw 230–250° | Self-occlusion | Goes in `mask_deg` once the unit is re-mounted |

## Layout

```
docs/CA3.md              this page: decisions, phase status, open issues
docs/design-plan.md      the design plan (Oct 8). Superseded where noted above
docs/plan.md             phase ladder and the definition of "done"
notes/notes.md           dated lab notebook — append per session, never rewrite
docs/system/             reference, kept true in place
  01_hardware.md         BOM, wiring, pin map, measured parameters
  02_pi_setup.md         OS, packages, venv, udev, serial access, SSH, Tailscale
  03_bringup.md          P0/P1 evidence: lidar, IMU, motors
  04_architecture.md     pipeline, threads/rates, frames, config contract
  05_config_reference.md every YAML key, units, provenance
  06_troubleshooting.md  symptom → cause → fix
  07_ros_stack.md        standard package stack + Foxglove plan (D5, supersedes D4)
docs/wiring.md           pin map and power, short form
docs/pi_setup.md         from-scratch install; system/02 is the measured state
tools/                   probe_echo_rate.py, test_lidar.py — mirrors of the Pi copies
evidence/                append-only artefacts, dated filenames
  lidar/  imu/  motors/
results/                 experiment outcomes: metrics, logs, maps
report/                  CA3_report.md, figures/
```

## Conventions

- **Dates in filenames**, newest-first-free: `2026-10-22_scan.png`. Never overwrite — append a new run.
- **Evidence is append-only; docs are edited in place; notes.md is append-only.**
- Every measurement gets the command that produced it next to the number.
- Anything on the Pi is written as a path: `~/ros2_ws/src/delivery_bot/...`.

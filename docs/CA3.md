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
| Login | user `robot`; key auth from the Mac (its key is in `authorized_keys`); no password stored here |
| ROS | ROS 2 **Jazzy** in `/opt/ros/jazzy`, `foxglove_bridge` and `rosbag2` (MCAP) installed |

### Decisions

| # | Decision | Date | Consequence |
| --- | --- | --- | --- |
| D1 | Build target is `sherm-raspi`, not the CA3 brief's Debian Pi | 2026-10-22 | Ubuntu, not Raspberry Pi OS: no `raspi-config`, no `/boot/firmware/config.txt`, no apt `gpiozero`/`lgpio` |
| D2 | **ROS 2 Jazzy is in scope** | 2026-10-22 | `design-plan.md` §0 "no ROS" is superseded — see [system/07_ros_stack.md](system/07_ros_stack.md) |
| D3 | **Foxglove Studio for live visualisation** | 2026-10-22 | The plan's ZeroMQ telemetry + `tools/viewer.py` is replaced by ROS 2 topics + `foxglove_bridge` |
| D4 | Keep the pure-Python maths stack | 2026-10-22 | EKF, A\*, pure pursuit and the occupancy grid stay as numpy modules, run inside ROS nodes — not bought from Nav2 in v1. **Superseded by D5.** |
| D5 | **`rf2o_laser_odometry` → `robot_localization` EKF replaces KISS-ICP + our own filter** | 2026-10-22 | Range-flow odometry is a better fit for a sparse 2D scan than ICP, and it outputs velocity, which is what the EKF wants. Cost: P3/P4 now measure `robot_localization` tuning, not code we wrote; drift behaviour is unchanged because there is still no absolute position input. `rf2o` runs with `publish_tf: false` — the EKF alone owns `odom → base_footprint`. |
| D6 | **Code lives in `~/ros2_ws/src/delivery_bot`** (git) | 2026-10-22 | Originally kept apart from this folder; since merged: this repo holds code, docs and evidence, and is cloned on the Pi at that path. Packages: `bringup`, `description`, `drivers`, `mission`, `slam`. Third-party `rf2o` is pinned in `deps.repos`, outside the repo. |
| D7 | **Standard ROS 2 package stack** in v1 — `rplidar_ros`, `rf2o_laser_odometry`, `robot_localization`, `slam_toolbox`, Nav2 | 2026-10-22 | Supersedes D4's own-maths scope (brief permits packages); `kiss-icp` dropped. We write only: motor node, IMU node, URDF, Simple Commander delivery script. Own maths documented as fallback — see [system/07_ros_stack.md](system/07_ros_stack.md) and the 2026-10-22 D5 entry in [notes.md](../notes/notes.md) |
| D8 | **Report and presentation framing (tentative): re-evaluation against published baselines** [K26]/[M26] on the delivery robot (E3 partial replication, E2 analogue), extended to people in the room [Y21]; the delivery mission is the application and demo | 2026-11-03 | Robot work is ordered by the evidence the report needs (E1 delivery, E2 IMU ablation, E3 repeatability, E4 people, hazard table); config frozen before 2026-11-06. Plan in [report_plan.md](report_plan.md); revisit after OI-8 closes and after the E1 runs |
| D8a | **D8 widened to a method × condition comparison**: 4 odometry configs (rf2o, rf2o + IMU, IMU heading, none) and 2 localisers (`slam_toolbox`, AMCL offline) under empty room, people and degraded lidar; RQ1 lidar spec, RQ2 odometry, RQ3 localiser, RQ4 people; E1 stays as the demo; papers become reference points inside the matrix | 2026-11-09 | Single-number checks against [K26]/[M26] gave yes/no answers with little room for insight; most cells are offline replays of bags. No E1–E4 bags existed on 2026-11-09; schedule reset in [report_plan.md](report_plan.md) §6 |
| D8b | **D8a narrowed to plan H: people as the axis, live runs as the results.** Odometry configs and localisers run live on the robot, each in an empty room and with people walking; RQ1 impact of people, RQ2 odometry, RQ3 localiser, RQ4 step-in safety; E1 demo; lidar degradation and the offline replay matrix dropped to future work / background | 2026-11-09 | OI-8 is the one real discovery and people are the most delivery-specific condition; replay reads ~71 % of live and the degradation axis was simulated; live closed-loop runs measure the robot itself. Plan in [report_plan.md](report_plan.md) §2–4 |

What this cost at the start, all resolved since: no `dialout` (fixed), no udev rule (`/dev/rplidar` exists, 2026-10-30), no `i2c-tools` (installed). No venv and no `pip`: still absent, because the apt stack (D1, D7) covers the dependencies.


## Status

| Phase | What it proves | Status |
| --- | --- | --- |
| **P0 Setup** | Python env, serial access, I2C, GPIO | **Essentially done** (2026-10-22; `/dev/rplidar` and I2C resolved 2026-10-30) — only the venv is open, see [system/02_pi_setup.md](system/02_pi_setup.md) |
| **P1 Bring-up** | Motors both ways, gyro calibrated, lidar plot | **Partial** — lidar verified on this Pi (7.05 Hz, 26–29 % no-echo, follows the room: OI-4 not a driver fault, mask not needed on this evidence); IMU checked at rest (2026-10-30) and on the built robot (2026-10-31, gyro 360.2° for a true 360°); robot built, mounting measured into the URDF (2026-10-31); motors untouched by us |
| **P2 Teleop + logging** | 2-minute drive replays on the laptop | Not started |
| **P3 Lidar odometry** | `rf2o`: 1 m square closes within 10 cm | **Partial** (2026-10-31, by hand) — full turn read 352.9° for a true 360° (−2 %), 1 m push read 0.962 m (−3.8 %); two 2026-11-01 pushes read 24 % of true travel (OI-8, test_log 2026-11-01); no square yet |
| **P4 EKF fusion** | `robot_localization` (2D): 3 spins, heading error under 10° | **Partial** — variances fitted 2026-10-31 (vx 1e-4, vyaw 5e-3, gyro 1e-4); no fusion-vs-no-fusion spins yet (4.5) |
| **P5 Mapping** | `slam_toolbox` occupancy grid with recognisable walls | **First map done** (2026-10-31, pushed by hand): 317×233 cells, 65.5 m² free, `results/maps/2026-10-31_room2.png`; scale vs tape +3.5 / +1.4 cm on the raw scan, map −5 cm on one gap; 5.5 sweep done 2026-10-31: loop closing is the only setting that matters, `slam_mapping.yaml` frozen; second tape gap not yet read; `base.launch.py` and `mapping.launch.py` run live from one command (2026-11-01) |
| **Localisation (build path stage 6)** | Live scan sits on the saved map | **Done by hand** (2026-11-01): `navigation.launch.py` = base + `localization_slam_toolbox_node` on `~/maps/2026-10-31_room2_graph`, no Nav2 yet; recovers a 30 cm / 20° wrong start after a push, fails at 30 cm / 31° (heading window about 20°); Foxglove pose estimate works |
| **P6 Motion calibration** | 1 m straight within 10 cm and 10° | Not started |
| **P7 Navigation** | Nav2: 5 goals, 15 cm, no collisions | Not started |
| **P8 Delivery loop** | Home → seat → home ×5 | Not started |

## Open issues

| # | Issue | Effect | Next |
| --- | --- | --- | --- |
| OI-1 | `robot` @ `100.73.7.24` offline since 2026-10-21 | Everything from the brief (venv, `~/delivery-bot`, udev rule) is unreachable | Confirm whether that box is retired or just off |
| OI-2 | `raspberrypi` @ `100.98.163.85` online, same Debian build, key rejected | Unknown whether it is the same machine reflashed | `ssh-copy-id` if needed |
| OI-3 | ~~`sherm-raspi` has no udev rule, user not in `dialout`~~ **Resolved 2026-10-30**: `dialout` active, `/dev/rplidar` exists. No venv by choice (apt stack) | — | [system/02_pi_setup.md](system/02_pi_setup.md) |
| OI-4 | Lidar returns a distance for only **33–35 %** of pings | **Mitigated**: 26–29 % no-echo on this Pi, gaps follow the room not the lidar (not a driver fault); the first map was made despite it. The echo rate itself is unexplained | [system/03_bringup.md](system/03_bringup.md) |
| OI-5 | ~~Unit is 0.23 m from the robot's own structure at raw 230–250°~~ **Resolved 2026-10-31**: robot built, lidar re-mounted and measured into the URDF; mask not needed on this evidence | — | — |
| OI-6 | `rplidar_composition` sometimes hangs at start (`RPLIDAR running` and no S/N), more often right after a restart | A launch that looks up produces no `/scan`; cost several retries on 2026-11-01 | wait 20 s after stopping the lidar; see [system/06_troubleshooting.md](system/06_troubleshooting.md); cause unknown, possibly USB power on the portable battery |
| OI-8 | rf2o reads about 24 % of real travel on two 2026-11-01 pushes (-76 %), against -3.8 % on 2026-10-31 | The EKF gets a velocity about 4 times too small; fusion, drift and any driven run would be off. The map is not affected | Offline checks done (test_log 2026-11-02/03 rows, notes 2026-11-03): bad bag replays to 24 % every time and at 0.25x, so not CPU or power; good-bag replay varies about 12 % run to run and is no control; 720-beam bags show no more empty or repeated beams than 1046-beam bags; push3-5 bags hold no push. Left: scan format or a person behind the robot. Live push 2026-11-03 (charged battery, stick, 1 m tape): `angle_compensate:=true` (720 beams) read 1.008 m of 1.00 m, `false` (1022 beams) read 0.971 m of 1.01 m, both above the 0.87 line, so the scan format is cleared and the 2026-11-01 failure points at the person behind the robot; cause identified: the two bad 2026-11-01 bags show 105-158 scan points 0.35-0.94 m behind the robot through the push (stick runs: 16-18) and the range behind jumping to 3.4 m and 5.26 m when it ended, with rf2o at 0.28 and 0.25 of the front-wall travel, so a person walking behind the robot pulled rf2o down. Fix tested offline 2026-11-03: dropping ranges below 0.6 m before rf2o replays the bad bags at 99.5 % (230535, 1.216 of 1.222 m) and about 95 % (225752); not shipped, not reproduced live (C1/C2 skipped). Not fixed: rf2o needs nobody near the robot on hand pushes (README rule, push with a stick); driven runs avoid it. If people may walk near a driven robot, add a `laser_filters` range filter feeding rf2o only, collision monitor and costmap stay on raw `/scan`. `angle_compensate:=true` stays |
| OI-7 | GitHub repo is public (checked 2026-11-01), `AGENTS.md` said private | Anyone can read the repo; `main` is protected with `build-and-test` | decide whether to make it private |

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
tools/                   probe_echo_rate.py, test_lidar.py — mirrors of the Pi copies;
                         robot_control.py (Foxglove buttons), streams/, analysis/
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

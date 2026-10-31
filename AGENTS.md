# AGENTS.md — delivery_bot (CA3 Room Delivery Robot)

Working instructions for any agent (or person) picking up this repo. Read this
first; it is short on purpose. State changes go in
[`notes/notes.md`](notes/notes.md), not here.

## What this is

A Raspberry Pi 4B robot that maps a small room once, then drives itself from a taped
home mark to named spots and back. The design is
[`docs/design-plan.md`](docs/design-plan.md); this file says how to work against it.
The assessed-project record (target machine, decisions, phase status, open issues)
is [`docs/CA3.md`](docs/CA3.md).

## Target machine

| | |
| --- | --- |
| SSH | `robot@sherm-raspi.local` (also `192.168.31.109`, Tailscale `100.83.14.99`) |
| Password | `robot`; Mac key already authorised, so key auth works from here |
| OS / ROS | Ubuntu 24.04.5 LTS, **ROS 2 Jazzy**, Foxglove bridge + rosbag2 MCAP |
| Project dir on Pi | `~/ros2_ws/src/delivery_bot/` — this repo, cloned on the Pi (D6). `~/delivery-bot/` is the older pre-ROS layout, scripts only |

The CA3 brief's other machine, `robot` @ `100.73.7.24` (Debian 13), has been
**offline since 2026-10-21**. Do not plan around it.

## Stack (decisions D1–D5, see README)

- ROS 2 wraps everything; the **estimation/mapping/navigation maths ships as packages**
  in v1 (D5): `rplidar_ros`, `rf2o_laser_odometry`, `robot_localization`,
  `slam_toolbox`, Nav2.
- Foxglove replaces the plan's ZeroMQ telemetry and matplotlib viewer.
- rosbag2 (MCAP) replaces the `msgpack` logger.
- We write only the hardware glue: motor node, IMU node, URDF, delivery script. The
  own numpy EKF / A\* / pure pursuit are the documented *fallback*, not the
  implementation.
- **`odom → base_footprint` is published by `robot_localization` alone.** rf2o runs
  with `publish_tf: false`. Two publishers of one transform makes the map spin and
  looks exactly like a broken sensor — check `tf2_tools view_frames` first.
- `motor_node` defaults to `dry_run:=true` from the launch file (computes duties,
  never touches GPIO). Live motors are a deliberate act.

## Rules

1. **Safety is structural.** Motors are driven only through the safety node/watchdog
   (`stop_dist_m`, `watchdog_s`, SIGINT zeroes PWM). Do not let any node write GPIO
   directly, and do not raise `v_max` (0.15 m/s) casually.
2. **Our code stays thin.** We own only the motor node, the IMU node, the URDF and the
   delivery script. No second EKF, planner or controller: if a module imports `rclpy`
   *and* re-implements estimation or planning maths, it has leaked.
3. **Config, never constants.** Every number in
   [`docs/system/05_config_reference.md`](docs/system/05_config_reference.md) lives in
   YAML inside the packages (`delivery_bot_bringup/config/`,
   `delivery_bot_drivers/config/`) and is copied back per experiment run.
4. **Mark provenance.** A value is *brief default*, *measured*, or *fitted*. Never
   report a MEASURE value as a result until it has been measured on the robot.
5. **`evidence/` is append-only** — new dated file per run, never overwrite.
   **`docs/` is edited in place.** **`notes/notes.md` is append-only**, newest entry
   first.
6. **Every number travels with the command that produced it.**
7. Don't touch the motor battery until the wiring checklist in
   `docs/design-plan.md` §4 is ticked. Kill switch is the motor switch, not software.

## Current state (2026-10-31)

| Phase | State |
| --- | --- |
| P0 Setup | **essentially done** (2026-10-22): apt stack, 2 GB swapfile (persisted in `/etc/fstab`), `dialout`, udev rule written, D5 stack installed, `rf2o` built and verified. **Resolved 2026-10-30:** `/dev/rplidar` symlink exists, `i2c-tools` installed, MPU6050 answers at 0x68. **Still open:** no venv |
| P1 Bring-up | lidar verified on this Pi (A1M8, 7.05 Hz, 26–29 % no-echo, gaps follow the room not the lidar); IMU node written and checked at rest (100 Hz, gyro z std 0.00175 rad/s); motors never driven by us; **robot built 2026-10-31**, lidar and IMU mounting measured into the URDF; gyro reads a hand-turned 360° as 360.2° |
| P3–P5 (SLAM side) | rf2o hand tests done (−2 % turn, −3.8 % push); variances fitted; **first room map saved** (`results/maps/2026-10-31_room2.png`); 5.5 tuning sweep pending |
| P2, P6–P8 | not started (motors are the teammate's) |

Known blockers live in [`docs/CA3.md`](docs/CA3.md) as OI-1…OI-5. The live one is
**OI-4, the 33 % echo rate** — resolve it before any mapping work, because sparse
scans degrade `slam_toolbox` and rf2o alike.

## Next actions, in order

*2026-10-31 update:* items 1–3 below are done (see `docs/test_log.md`); the robot is built and the hand-push SLAM steps (3.2, 4.4, 5.4) are done. Next: 5.5 sweep and freeze, then stage 6 localisation on `~/maps/2026-10-31_room2_graph`; motor-driven work waits on the teammate. Build path progress (stages 0–9) is in
`docs/slam_build_path.md`; the SLAM software that can run without the robot is written
and replay-tested (rf2o, covariance relay, mapping and replay launches, trajectory
recorder, imu_node, explore_lite built). Waiting on the robot: 2.1 measurements, 3.2/3.3
spin and push tests, 4.4 variances, 5.4 room map, 5.5 tuning sweep, stages 6, 8.4, 9.

0. ~~P0 install + rf2o build~~ — **done 2026-10-22**: apt stack in, 2 GB swapfile
   (persisted in `/etc/fstab`), D5 packages installed, `rf2o_laser_odometry` built
   from source and verified with `ros2 pkg prefix`; full `colcon build
   --symlink-install` = 5 packages in 3 min 43 s. GPIO route settled: **gpiozero +
   `LGPIOFactory`** (`lgpio` is in `/usr/lib/python3/dist-packages`), so
   `python3-gpiozero python3-lgpio python3-smbus2` are the apt dependencies.
1. Make `/dev/rplidar` appear: `sudo udevadm trigger -c add -s tty`, else unplug and
   replug the CP210x. `dialout` is now active for `robot`, so until the symlink lands
   the driver can run on `/dev/ttyUSB0` as a stopgap.
2. `sudo apt install i2c-tools`, then `i2cdetect -y 1` must show `68`.
3. Run [`tools/probe_echo_rate.py`](tools/probe_echo_rate.py) **on this box** — its own
   CP210x lidar is a control experiment: ~90 % echoes means the old mounting was at
   fault, ~35 % means the unit or the series is.
4. 50 cm white-box test; record the box angle → `yaw_offset_deg`, and any consistent
   short returns → `mask_deg`.
5. First live check of the stack: `ros2 launch delivery_bot_bringup base.launch.py`
   with `dry_run:=true`, confirm `/scan` in Foxglove and that `/odometry/filtered`
   stays sane while the robot is pushed by hand.

## Conventions

- Filenames carry dates: `2026-10-22_scan.png`. One run per file.
- Write remote paths as `~/ros2_ws/src/delivery_bot/...`; write local paths relative to
  the repo root.
- The Pi is headless: verify with Foxglove or a saved PNG, never "it should print".
- SSH sessions are non-interactive — `source ~/botenv/bin/activate` explicitly, since
  `.bashrc` is not sourced. Use `cat > f << 'EOF'` for file writes over SSH.
- Errors we have actually hit live in
  [`docs/system/06_troubleshooting.md`](docs/system/06_troubleshooting.md) with their
  exact text. Add to it when you hit something new.

## Syncing (Mac ↔ GitHub ↔ Pi)

One repo, three copies. The GitHub repo is private; it is the source of truth.

- **`git pull` at the start of every session, `git push` at the end.** No long-lived
  divergence, no merge conflicts to resolve by hand.
- **Never edit the same file on the Mac and the Pi in one session.** Prose and
  analysis on the Mac; hardware runs on the Pi.
- **The Pi pulls; it is not a second author** unless the run happened there and could
  not be reproduced. If it did, commit on the Pi and push before touching the Mac.
- **`notes/notes.md` is append-only** — a conflict in it means someone rewrote
  history; keep both blocks and re-sort by date.
- Commit messages carry the date and the phase: `notes: 2026-10-23 echo-rate control
  on sherm-raspi`.
- Bags, `build/`, `install/`, `log/`, `.venv` and `.DS_Store` stay out of git
  (`.gitignore` covers them). Evidence PNGs are small and do go in.

## Folder map

```
README.md          what the robot is, hardware, stack, common commands
AGENTS.md          this file — how to work here
notes/notes.md     dated lab notebook, newest first, append-only
docs/CA3.md        assessed-project record: decisions D1–D6, phases, open issues
docs/design-plan.md  the Oct 8 design plan (superseded where docs/CA3.md says so)
docs/plan.md       phase ladder and the definition of "done"
docs/system/       01 hardware · 02 pi setup · 03 bring-up · 04 architecture
                   05 config · 06 troubleshooting · 07 ros stack
docs/wiring.md     pin map and power
docs/pi_setup.md   from-scratch install (system/02 is the measured state)
evidence/          lidar/ imu/ motors/ — raw artefacts, append-only
results/           experiment outcomes and metrics
report/            CA3_report.md, figures/
tools/             probe_echo_rate.py, test_lidar.py (mirrors of the Pi copies)
delivery_bot_*/    the four ROS 2 packages
```

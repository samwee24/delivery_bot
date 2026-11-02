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
| SSH | `robot@100.83.14.99` (Tailscale, works from anywhere); LAN fallback `robot@192.168.31.109` or `sherm-raspi.local` |
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

## Current state (2026-11-01)

| Phase | State |
| --- | --- |
| P0 Setup | **essentially done** (2026-10-22): apt stack, 2 GB swapfile (persisted in `/etc/fstab`), `dialout`, udev rule written, D5 stack installed, `rf2o` built and verified. **Resolved 2026-10-30:** `/dev/rplidar` symlink exists, `i2c-tools` installed, MPU6050 answers at 0x68. **Still open:** no venv |
| P1 Bring-up | lidar verified on this Pi (A1M8, 7.05 Hz, 26–29 % no-echo, gaps follow the room not the lidar); IMU node written and checked at rest (100 Hz, gyro z std 0.00175 rad/s); motors never driven by us; **robot built 2026-10-31**, lidar and IMU mounting measured into the URDF; gyro reads a hand-turned 360° as 360.2° |
| P6 localisation | **done by hand** (2026-11-01): `navigation.launch.py` = base + `localization_slam_toolbox_node` on the room graph (no Nav2 yet); a 30 cm / 20° wrong start recovers after a push, 31° does not; Foxglove pose estimate works. `base.launch.py` and `mapping.launch.py` run live from one command |
| P3–P5 (SLAM side) | rf2o hand tests done (−2 % turn, −3.8 % push); variances fitted; **first room map saved** (`results/maps/2026-10-31_room2.png`); 5.5 sweep done and `slam_mapping.yaml` frozen; USB camera streams to Foxglove (1280x720 at 10 fps) |
| Foxglove buttons | **done on the Pi** (2026-11-02): `robot_control.py` stacks, bag, camera, stream, power; `/run/save`; `/imu_node/recalibrate`. Power buttons need the sudoers rule (owner step) |
| P2, P6–P8 | not started (motors are the teammate's) |

Known blockers live in [`docs/CA3.md`](docs/CA3.md) as OI-1…OI-5. OI-3 and OI-5 are
resolved and OI-4 (the 33 % echo rate) is mitigated: the first map is made and gaps
follow the room, not the lidar. The open risks now are in the next-actions list.

## Next actions, in order

Done and recorded in `docs/test_log.md`: P0 install and rf2o build, `/dev/rplidar`,
`i2c-tools`, echo-rate probe, hand-push rf2o/SLAM runs (3.2, 4.4, 5.4), 5.5 sweep with
`slam_mapping.yaml` frozen. Build path progress (stages 0–9) is in
`docs/slam_build_path.md`.

1. Stage 6 is done by hand (6.2 to 6.4, 2026-11-01). Left from it: the second tape gap on the map (5.4); the new home mark is taped at the old position (the original tape was lost), so `goals.yaml` home stays 0, 0, 0.
2. **rf2o under-reads a hand push by 76 % (OI-8).** Two straight pushes on 2026-11-01 read 24 % of the true distance, against −3.8 % on 2026-10-31. Leads: scan format (`angle_compensate: True`, 720 beams) or a person behind the robot. Next: fix `tools/analysis/rf2o_fmt.sh` (offline rig, control gave 0 updates), then repeat the live push with `angle_compensate:=false` on a charged battery. Charge the portable battery first.
3. Keep the camera off while mapping, or accept EKF `Failed to meet update rate`
   (`frequency` is now 20). The 20 Hz late-update count is still unconfirmed on a quiet Pi (closure 0.115 m against 0.109 m); rerun the check with nothing else running.
4. Still waiting on the robot: 3.3 failure tests, 4.5 fusion comparison, stages 8.4
   and 9. Motor-driven work (P2, P6–P8) waits on the teammate.
5. Foxglove buttons (`tools/robot_control.py`, 2026-11-02) run on the Pi and are logged in `notes/notes.md` and `docs/test_log.md`. Still open: the owner steps in the README (sudoers rule, linger and the systemd unit, Foxglove layout export), `/imu_node/recalibrate` with the robot nudged, `/stack/localisation`. Never pass `dry_run:=false` from it.
6. Analysis scripts that produced the logged numbers are in `tools/analysis/`; bags
   and maps live only on the Pi (`~/bags`, `~/maps`), backed up by hand to
   `../delivery_bot_pi_backup/` on the Mac.

## Conventions

- Filenames carry dates: `2026-10-22_scan.png`. One run per file.
- Write remote paths as `~/ros2_ws/src/delivery_bot/...`; write local paths relative to
  the repo root.
- The Pi is headless: verify with Foxglove or a saved PNG, never "it should print".
- SSH sessions are non-interactive, so `.bashrc` is not sourced: `source
  /opt/ros/jazzy/setup.bash` and `~/ros2_ws/install/setup.bash` explicitly. There is no
  venv. Use `cat > f << 'EOF'` for file writes over SSH.
- Errors we have actually hit live in
  [`docs/system/06_troubleshooting.md`](docs/system/06_troubleshooting.md) with their
  exact text. Add to it when you hit something new.

## Git workflow

`main` is protected: changes land by pull request with CI green, never by direct push.

- **One task, one short branch** from `main`, named `type/topic` (`docs/test-log`,
  `slam/run-save`, `fix/imu-bias`). Open a PR, squash-merge, the branch is deleted
  automatically. No long-lived branches.
- **PR title is the commit:** `type: YYYY-MM-DD what`, with the date (CI checks it).
  The PR template asks for the Pi command and result that back any number (rule 6).
- **CI enforces what a file cannot** (job `repo-rules`): `notes/notes.md` is
  append-only, `evidence/` files are never modified or deleted, and no added line
  contains `dry_run:=false` outside markdown.
- Tag a milestone as `vX.Y-name` (`v0.1-slam-mapping`) and add a GitHub Release.
- The repo settings behind this are recorded in `docs/system/08_github.md`.

## Syncing (Mac ↔ GitHub ↔ Pi)

One repo, three copies. The GitHub repo (public as of 2026-11-01, see OI-7) is the source of truth.

- **`git pull` at the start of every session; push a branch at the end** (see Git
  workflow). No long-lived divergence, no merge conflicts to resolve by hand.
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
tools/             probe_echo_rate.py, test_lidar.py (mirrors of the Pi copies);
                   robot_control.py (Foxglove buttons: stacks, bag, camera, power);
                   streams/ (stream, lidar-off extras); analysis/ (offline scripts)
delivery_bot_*/    the four ROS 2 packages
```

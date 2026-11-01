# Handover: delivery_bot (CA3 room delivery robot, SLAM side) — 2026-11-02

> **To the new chat:** This is a handover from a previous conversation. Read the whole brief before
> replying. Then reply with a short summary (3–5 lines) of where things stand and what you'll do
> first, and wait for me to confirm before starting — unless I've already told you to go ahead.

## 1. Goal
Finish the assessed project CA3 (MA4890): a Raspberry Pi 4B robot that maps a small room once, then drives itself from a taped home mark to named spots and back. **I own the SLAM part** (mapping, localisation, odometry fusion), tracked in `docs/slam_build_path.md` (stages 0–9). A teammate owns the motors. The end product is working SLAM plus an honest evaluation and write-up (`report/CA3_report.md`, stage 9) that cites the papers behind each design choice. Priority I set on 2026-10-30: **finish everything first, understand it later.** You do the work, move fast.

## 2. Context & background
- Repo: `/Users/shermanwee/Documents/MA4890/delivery_bot` on my Mac, branch `slam/build-path` (origin = GitHub, public as of 2026-11-01, see OI-7; `main` is protected, `build-and-test` required). The repo is also cloned on the Pi at `~/ros2_ws/src/delivery_bot/` (colcon `--symlink-install`, so pulled YAML/launch edits are live).
- Read `AGENTS.md` first (project rules, state, next actions), then `docs/CA3.md` (decisions D1–D6, phase status, open issues OI-1…OI-8), `docs/slam_build_path.md`, `docs/test_log.md` (every number with its command), `notes/notes.md` (newest first).
- Robot: Pi 4B 4 GB, Ubuntu 24.04.5, **ROS 2 Jazzy**. SSH `robot@100.83.14.99` (Tailscale, works from any network; password `robot`, my Mac's key is authorised). LAN `192.168.31.109` / `sherm-raspi.local` only works on the Pi's own Wi-Fi (my Mac is usually on 192.168.1.x). The Foxglove bridge is `ws://100.83.14.99:8765`.
- Hardware now built (4 wheels, skid-steer): RPLidar A1M8, MPU6050 IMU, UGREEN 2K USB camera (`/dev/video0`, USB 1bcf:2284), portable battery or wall power for the Pi, separate motor battery. Motors have never been driven by us.
- Stack: `rplidar_ros`, `rf2o_laser_odometry` (pinned b38c68e, `publish_tf: false`), `odom_covariance_relay`, `robot_localization` EKF (**sole** `odom → base_footprint` publisher, 20 Hz now), `slam_toolbox` 2.8.5 (lifecycle: configure then activate), `foxglove_bridge`, rosbag2 MCAP, `usb_cam` 0.8.1, Nav2 (not yet used).
- Packages: `delivery_bot_bringup`, `_description`, `_drivers`, `_slam`, `_mission`.
- **Teammate owns, never edit:** `motor_node`, twist, `/cmd_vel`, teleop, motor parts of `delivery_bot_drivers/config/drivers.yaml`.
- Terms: "5.4/5.5/6.2" etc. are task numbers in `docs/slam_build_path.md`. OI-n = open issue in `docs/CA3.md`. "The sweep" = the 5.5 slam_toolbox parameter sweep. "Home mark" = taped start position (original tape lost; new tape at the old position, `goals.yaml` home stays 0, 0, 0).
- Papers behind the design (cited by key in `docs/slam.md` §refs near line 978): Ran 2025 review [R25], Jaimez 2016 rf2o [J16], Kudriashov 2026 AMCL-EKF benchmark [K26], Macenski 2021 SLAM Toolbox [MJ21], Merrick 2026 EKF vs SLAM [M26], Huang 2022 [H22], Filatov 2017 map metrics [F17], Ye 2021 [Y21], Salem 2023 [S23]. They shaped the design (graph SLAM, rf2o + gyro EKF without encoders, no AMCL feedback into the EKF, covariances fitted on separate data) and the stage-9 evaluation plan (map coverage, map IoU, pairwise trajectory error via `evo`). I have not read them in the sessions so far; the build path's "explain it back" questions are unanswered by choice.

## 3. Current state
✅ **Done and confirmed (numbers in `docs/test_log.md` with commands):**
- URDF mounting measured (laser x 0.02, z 0.12; imu x 0.023, y −0.055, z 0.07; wheel_base 0.156; robot_radius 0.12; `laser_yaw` 0.0 from the box test, +2.6° inside placement error). `wheel_radius` 0.0325 is still the TT default, **not measured**.
- rf2o hand tests 2026-10-31: full turn −2 %, 1 m push −3.8 %. Gyro reads a hand-turned 360° as 360.2°.
- Variances fitted: `odom_covariance.yaml` vx 1e-4, vyaw 5e-3; `drivers.yaml` imu_node `gyro_var` 1e-4 (provisional), `gyro_scale_z` 1.0 (measured).
- First room map `results/maps/2026-10-31_room2.{pgm,yaml,png}` (317×233 cells, 65.5 m² free). Raw scan vs tape +3.5 / +1.4 cm; map −5 cm on one gap.
- 5.5 sweep done: loop closing is the only parameter that matters (first-to-last pose distance 0.658 m off, 0.109 m on). `slam_mapping.yaml` kept and frozen.
- Stage 6 localisation by hand (2026-11-01): `navigation.launch.py` = base + `localization_slam_toolbox_node` on the saved graph (no Nav2 yet); 30 cm / 20° wrong start recovers after a push, 31° does not; Foxglove pose estimate works. `base.launch.py` and `mapping.launch.py` run live from one command.
- Camera streams to Foxglove. Measured ceiling: the Pi decodes MJPEG on one core, about 11.6 Mpixel/s. Delivered `/image_raw/compressed`: 640x480 @30 28 Hz, 1024x768 @15 11.5, 1280x720 @10 10.1, 1920x1080 @15 5.7. `camera.yaml` is 1280x720 @10. Under SLAM replay: 1024x768 @15 gave 9.9 Hz, 1280x720 @10 8.3 Hz, and the EKF missed its update deadline 8–26 times in 65 s versus 0 without the camera; slam_toolbox dropped 0 scans.
- Docs updated through 2026-11-01 (config reference, hardware, troubleshooting, README, status lines).

⚠️ **Done but unverified / partly confirmed:**
- 5.4 map reading: the first tape gap read −5 cm (borderline at 5 cm cells); the second gap is not read yet.
- EKF at 20 Hz: loop closure 0.115 m vs 0.109 m, but the late-update count is confounded by other load. Recheck on a quiet Pi.
- Foxglove layout JSONs (`docs/foxglove/camera_layout.json`, `slam_layout.json`): imports never confirmed.
- Unexplained: a wall read 0.46 m behind the robot; rf2o direction offset of 18° (not claimed as a result).

🔄 **In progress (as the repo stood at the start of this handover):**
- **OI-8, rf2o under-reads a hand push by 76 %.** Two pushes on 2026-11-01 (1.00 m and 1.20 m) read 0.243 m and 0.289 m; the lidar's own front-wall range confirmed the true travel (0.996 and 1.222 m). Same stack read −3.8 % on 2026-10-31. Candidate causes: scan format (`angle_compensate: True`, 720 beams) or a person behind the robot. The offline replay rig (`tools/analysis/rf2o_fmt.sh`) does not work yet (its control gave 0 updates, so it cannot reproduce −3.8 %).
- **Uncommitted working tree on the Mac (not made in the conversation this brief comes from; check `git diff` and ask me before committing):** edits to `delivery_bot_bringup/launch/base.launch.py` (new `bridge` launch arg, default true, so `robot_control.py` can own the single Foxglove bridge on port 8765), `mapping.launch.py`, `navigation.launch.py`, and `tools/streams/stream_control.py` renamed/rewritten to `tools/robot_control.py` (268 lines). The branch is also 2 commits ahead of origin (latest `c9cbfa5`: `/imu_node/recalibrate` and `/run/save` services). Nov 1–2 work on streaming tools, the audio/video relay, lidar motor on/off and Foxglove service buttons is in the git log (`77f41da` … `c9cbfa5`) and README lines ~128–131; I only know it from the log.

## 4. Decisions & reasoning
- **rf2o + robot_localization EKF owns `odom → base_footprint`; rf2o `publish_tf: false`.** Two publishers of one transform make the map spin.
- **No AMCL, no SLAM pose fed back into the EKF** (Kudriashov: feedback hurts repeatability in repetitive spaces). Absolute pose comes from `slam_toolbox` localisation writing `map → odom` against a frozen graph.
- **Use packages, write only glue (D5):** motor node, IMU node, URDF, delivery script. No second EKF/planner/controller.
- **`laser_yaw` = 0:** box test at 0.39 m put the face at +2.6° (and +6° on the first rep), inside by-eye placement error.
- **`angle_compensate: True` in `lidar.launch.py`:** slam_toolbox drops scans whose beam count differs from the first, and a variable count produced a fan-shaped map. Fixed count 720. (Now a launch argument, default true, for the OI-8 test.)
- **5.5 config frozen at the baseline** (`min_laser_range`, `minimum_travel_distance` variants landed within 1–8 cm, one run each, not a difference).
- **Camera at 1280x720 @10 for viewing; off or 1024x768 @15 while mapping.** Quality (JPEG) setting does not change the rate.
- **Docs rules:** `evidence/` and `notes/notes.md` append-only (newest first); `docs/` edited in place; every number travels with its command; mark provenance (brief default / measured / fitted).
- **Tried and failed / rejected:**
  - `pixel_format: raw_mjpeg` on usb_cam publishes nothing on `/image_raw/compressed`.
  - Streaming raw `/image_raw` to Foxglove (14 MB/s) lagged 10 s: use `/image_raw/compressed`, and hide raw with the bridge `topic_whitelist` regex `^(?!/image_raw$)(?!/image_raw/(zstd|theora|compressedDepth)).*`.
  - Replaying a bag with `--start-offset` skips `/tf_static`, so slam_toolbox drops every scan. Play from the start with `--topics /scan /imu/data /tf_static` and `--clock`, `use_sim_time:=true`, and never replay the recorded `/tf`.
  - First map was a fan until `angle_compensate` was fixed.
  - The IMU calibration failed (z std 0.0211) while the robot moved: it must be still.
  - The scattered floor dots on the map are chair bases and table legs, not the person pushing.

## 5. Exact details (verbatim)
- Pi helper pattern: scripts in `/tmp` on the Pi are wiped by a reboot; keep copies in `tools/analysis/` (cam_sweep.sh, sweep2.sh, loadtest.sh, push_start.sh, push_stop.sh, rf2o_fmt.sh, etc.).
- Launch commands (from README/notes): `ros2 launch delivery_bot_bringup base.launch.py`; `ros2 launch delivery_bot_bringup camera.launch.py`; `ros2 launch delivery_bot_bringup lidar.launch.py`; `ros2 launch delivery_bot_slam slam_replay.launch.py use_sim_time:=true foxglove:=false [slam_params_file:=<yaml>] [tum_output_dir:=<dir>]`; mapping via `mapping.launch.py`; `bash tools/streams/start_streams.sh [av]`.
- Data on the Pi: bags `~/bags` (e.g. `2026-10-31_map_200956`, `_turn_194945`, `_push_195343`), maps `~/maps` (`2026-10-31_room2` + `_graph`). Mac backup: `../delivery_bot_pi_backup/` (and `bags/` in the repo folder per the 2026-11-01 note).
- Error texts worth searching: `parameter 'framerate' has invalid type ... setting it to {integer} is not allowed.` (write `30.0`); `Message Filter dropping message: frame 'laser'`; `Failed to meet update rate!` (EKF); Foxglove `Check that the WebSocket server at ws://192.168.31.109:8765 is reachable.` (wrong network: use the Tailscale address).
- Provenance for camera numbers: `docs/test_log.md` rows dated 2026-10-31 (commits c6beb1b, 924f4de); config in `delivery_bot_bringup/config/camera.yaml` (brightness 130, gain 64; usb_cam default 50/0 reads near-black).
- Full final code is in the repo; none is reproduced here. Where this brief needs a file's contents, read it from the repo.

## 6. Corrections & gotchas
- I said "wheel base" is left-to-right wheel centre distance: **0.156 m**; front-to-back wheel centre distance is 0.113 m. Skid-steer, so the effective track width needs calibration once motors run.
- I move the robot by hand (pushing from behind blocks part of the scan, so keep the push clean or use a stick/string). Spinning on the spot by hand is hard.
- The lidar can stall after being killed mid-scan (`Failed to set scan mode` / no health line, OI-6): wait ~6–20 s and relaunch it alone.
- `pkill -f` patterns inside an ssh command line can kill the ssh session itself: put them in script files, or use the `[x]` bracket trick.
- `nohup ros2 bag record` ignores SIGINT: use SIGTERM and wait for `metadata.yaml`. Orphan `ros2 launch` children can survive SIGINT.
- `sudo` on the Pi needs a terminal and a password: never type passwords. I run `ssh -t robot@100.83.14.99 sudo ...` myself.
- macOS `sed -i` needs `sed -i ''`.
- A bash script that `wait`s with no arguments also waits for a nohup'd background node: use `wait $PID...`.
- The portable battery went flat mid-recording on 2026-11-01 and a reboot cleared `/tmp`: charge it before recordings, prefer wall power for long runs.
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## 7. Open issues & unknowns
- OI-8 (rf2o scale) is the big risk: until fixed, EKF velocity is about 4× too small and any driven run or fusion comparison is off.
- OI-4: 26–29 % no-echo on the lidar, mitigated, cause unexplained. OI-6: lidar hang at start, cause unknown. OI-7: repo is public (`AGENTS.md` once said private): decide whether to make it private. OI-1/OI-2: old Pi boxes offline/unreachable, ignore.
- `wheel_radius` not measured; `gyro_var` provisional; track width needs recheck once motors run.
- Not done: 2.2 URDF box check, 3.3 failure-mode tests, 4.5 fusion vs no fusion, 5.4 second-gap reading, stages 8.4 and 9 (`evo` not installed on the Pi, which blocks 9.3), the person-free repeat of the room run.
- Lidar, camera and bridge do not restart after a Pi reboot (a systemd service was offered, needs sudo, not done).
- The Foxglove bridge command is documented in the README but the lidar launch does not include it by default now (`robot_control.py` owns it when used).

## 8. Next steps
**For the new chat, in order:**
1. `git status` and `git diff`: confirm what the uncommitted launch/`robot_control.py` changes are with me, then commit/push (or leave) as I say. Keep the commit trailer.
2. OI-8: fix `tools/analysis/rf2o_fmt.sh` so its control reproduces about −3.8 %, then run the `resampled` variant (if rf2o drops to about 24 %, the 720-beam format is the cause). Otherwise repeat a live 1 m push with `angle_compensate:=false` on a charged battery, with the person clear of the rear scan (or pull with a string). I must be at the robot for the push.
3. Rerun the EKF 20 Hz late-update check on a quiet Pi (nothing else running, camera off).
4. Read the second tape gap on the saved map (stage 6 localisation gives the pose); tick 5.4 only if both gaps are read.
5. Then: 3.3 failure tests, 4.5 fusion vs no fusion, install `evo`, stage 9 evaluation (map coverage and IoU, five runs, pairwise ATE) and the write-up with citations.
**For me (outside the chat):**
- Charge the portable battery; be at the robot for pushes; run any `sudo` steps myself.
- Decide OI-7 (repo public/private) and whether I want a boot-time systemd service.
- Confirm the Foxglove layout JSONs import (camera and SLAM layouts).

## 9. Working preferences
- Replies terse, fragments fine (caveman style: no filler, no pleasantries). Code, commits and docs written in normal prose.
- Do the work yourself and move fast; don't nag about the journal or "explain it back".
- Never edit motor files; never type passwords; ask before anything outward-facing or hard to reverse.
- Keep docs honest: say what was and wasn't verified, and give the command behind each number.
- Keep a short task list as you work and close each turn with a brief recap.

# 06 · Troubleshooting

Symptom → cause → fix. Anything we actually hit is marked **hit**, with the exact
text of the error, so it is searchable later.

## Access and networking

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `ssh: Could not resolve hostname sherm-raspi: nodename nor servname provided, or not known` | bare mDNS name | use `sherm-raspi.local`, `192.168.31.109`, or Tailscale `100.83.14.99` |
| **hit** `Permission denied (publickey,password)` | key not in `authorized_keys` | `ssh-copy-id -i ~/.ssh/id_ed25519.pub robot@sherm-raspi.local`, or install the key over one password login |
| **hit** `ssh: connect to host 100.73.7.24 port 22: Operation timed out` | the old bot Pi is offline (`tailscale status`: `offline, last seen 1d`) | power it on; do not debug it as a network problem |
| host key mismatch after a reflash | old key in `known_hosts` | `ssh-keygen -R <host>` |
| password prompt never appears | BatchMode or piped stdin | run from an interactive terminal; `sshpass`/`expect` only for automation |

## Lidar

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `Permission denied` opening `/dev/ttyUSB0` | user not in `dialout`, or udev rule absent | `sudo usermod -aG dialout robot` + re-login; install `99-rplidar.rules` |
| **hit** echo rate only 33–35 %, `distance = 0` for 2/3 of pings | film, dust or damage on the scan window; robot self-occlusion; dark/glass surfaces | white box at 50 cm test: ~95 % → scene, ~35 % → optics. See [03_bringup.md](03_bringup.md) |
| **hit** script prints `Scan rate ~0.9 Hz` while the sensor spins at 5–7 Hz | `iter_scans(min_len=100)` skips revolutions with <100 valid points; the script divides by wall time | use `min_len=5` for diagnostics, or time between `new_scan` flags |
| `Wrong body size`, `Descriptor length mismatch`, `Incorrect descriptor starting bytes` | stale bytes in the buffer | re-run; if it repeats, unplug and replug the lidar |
| hangs or times out on `get_info()` | baud does not match the model | A1/A2M8 = 115200; A2M12/A3/S1/S2 = 256000 |
| spins but very few points | dirty lens, or something right next to it | clean the window; check `min_range_m` |
| Pi reboots, or `vcgencmd get_throttled` ≠ `0x0` when the motor starts | power bank or USB-C cable too weak | report it; do not work around it |
| `vcgencmd: Can't open device file: /dev/vcio` | **hit** on Ubuntu — `vcgencmd` is not the default path/tool | install `raspi-utils`, or read `/sys/class/thermal/thermal_zone0/temp` (idle was 40.4 °C) |

## Python / environment

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `/usr/bin/python3: No module named pip` | `python3-pip` not installed on this image | `sudo apt install python3-pip python3-venv` |
| `ModuleNotFoundError: No module named 'rplidar'` | wrong interpreter — plain `python3` instead of the venv, or ROS sourced over it | activate `~/botenv` **after** `/opt/ros/jazzy/setup.bash` |
| **hit** `ModuleNotFoundError: No module named 'rplidar'` over SSH | non-interactive shells do not run `.bashrc` | `source ~/botenv/bin/activate` explicitly in the command |
| `kiss-icp` build runs out of memory or dies | no swap on this image (historical — `kiss-icp` dropped in D5) | only if a heavy source build returns: add a 2 GB swapfile first |
| `Error opening terminal: xterm-ghostty` (from the Mac) | Ghostty terminfo missing on the Pi | **Durable fix** — on the Mac: `infocmp -x xterm-ghostty \| ssh robot@sherm-raspi.local 'tic -x -'` (tic prints a harmless alias warning); verify on the Pi with `infocmp xterm-ghostty \| head -3`. Quick fallback: `export TERM=xterm-256color`. **hit 2026-10-22** as `tmux attach` → `missing or unsuitable terminal`, cascading to `no server running on /tmp/tmux-1000/default` |
| `gpiozero`/`lgpio` import fails | those are Raspberry Pi OS apt packages; this box is Ubuntu | use `lgpio` from pip, or Adafruit Blinka — decide once, record in [01_hardware.md](01_hardware.md) |

## ROS 2 / Foxglove

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `ros2 launch foxglove_bridge ...` hangs or refuses to bind | a stale bridge already holds 8765 | `sudo fuser -k 8765/tcp` |
| no topics in Foxglove | bridge and client on different networks | the bridge binds 0.0.0.0:8765; connect by Tailscale IP `100.83.14.99` |
| `ros2 bag record` produces huge files | recording `/scan` at high rate uncompressed | MCAP + zstd is installed; keep `/scan`, `/imu/data`, `/odom`, `/cmd_vel`, `/plan` only |
| `.bashrc` sources ROS but the venv is lost | sourcing order | ROS first, `source ~/botenv/bin/activate` second |
| **hit** `LaserRangeScan contains 1041 range readings, expected 931` (slam_toolbox, repeated) | rplidar_ros sends a varying beam count per scan when `angle_compensate` is off, and slam_toolbox drops every scan that differs from the first | `angle_compensate: True` in `delivery_bot_bringup/launch/lidar.launch.py` (fixed 720 beams); symptom is a map that stops growing |
| **hit** lidar prints `RPLIDAR running on ROS 2 package` and nothing more, no `/scan`, or `Failed to set scan mode` | the unit was killed mid-scan | stop everything, wait about 6 s, relaunch the lidar alone |
| **hit** `imu_node`: `gyro z std 0.0211 rad/s during calibration exceeds calib_max_std; keep the robot still and restart` | robot was moving during the 3 s start-up calibration | hold still, restart `imu_node` |
| **hit** ssh to the Pi exits 255 mid-command | `pkill -f <pattern>` matched the ssh command line itself | put the `pkill` in a script file and run that |
| **hit** `ros2 bag record` left running, no `metadata.yaml`, `Could not open ... with 'mcap'` | SIGINT ignored by a backgrounded process in a non-interactive shell | `kill -TERM <pid>`, wait for `metadata.yaml` |
| **hit** Foxglove camera stream lags 10 s or more, Pi ping 250 ms, bridge RSS near 900 MB | the Image panel subscribed to raw `/image_raw` (about 920 KB per frame, 14 MB/s at 15 fps) instead of `/image_raw/compressed` (70 KB); also the Pi was at load 18 with the SLAM sweep running | pick `/image_raw/compressed`; start the bridge with `-p topic_whitelist:='["^(?!/image_raw$)(?!/image_raw/(zstd\|theora\|compressedDepth)).*"]'` to hide the raw topic; do not stream the camera while a replay or mapping run is using the CPU |
| **hit** Foxglove: `Check that the WebSocket server at ws://192.168.31.109:8765 is reachable.` | the LAN address only exists on the Pi's own Wi-Fi (192.168.31.x); the Mac was on 192.168.1.x and `ping` read 100 % loss | connect to `ws://100.83.14.99:8765` (Tailscale, same on every network while Tailscale is up on both ends); the bridge does not start itself after a reboot |
| **hit** `usb_cam_node_exe` aborts: `parameter 'framerate' has invalid type: Wrong parameter type, parameter {framerate} is of type {double}, setting it to {integer} is not allowed.` | `framerate: 30` written without a decimal | write `30.0` |
| **hit** camera delivers far less than `framerate` (1920x1080 @30 gives 4.5 Hz, 1280x720 @30 gives 13 Hz) | software MJPEG decode on one core, about 11.6 Mpixel/s; `jpeg_quality` 50 to 95 changes nothing; `pixel_format: raw_mjpeg` gives an empty `/image_raw/compressed` | choose resolution and rate to fit under the cap (see `docs/system/05_config_reference.md`, camera.yaml); under SLAM load the rate falls another 10 to 20 % |
| **hit** every scan dropped: `Message Filter dropping message: frame 'laser' ...` during a bag replay | `ros2 bag play --start-offset 60` skipped the `/tf_static` messages at the start of the bag | play from the start, with `--topics /scan /imu/data /tf_static` |
| **hit** `LocalizationSlamToolbox: Starting localization at first node (dock) is correctly not supported`, no `map -> odom` | `map_start_at_dock: true` is rejected in localisation mode (slam_toolbox 2.8.5) | use `map_start_pose: [x, y, yaw]`; the home mark is the map origin, so `[0.0, 0.0, 0.0]` |
| **hit** localisation started in the wrong place and the scan points stay rotated or shifted | slam_toolbox matches scans only after the robot has travelled `minimum_travel_distance` 0.1 m or `minimum_travel_heading` 0.1 rad; at rest it keeps the start pose | push the robot 0.5–1 m; a heading error above about 20° will not be repaired, use Foxglove "Publish pose estimate" |
| **hit** `Failed to make transition 'TRANSITION_CONFIGURE' for LifecycleNode '/slam_toolbox'`, node stays `unconfigured` | `mapping.launch.py include_base:=false`: configure was sent before the node's lifecycle services existed and is not retried | fixed 2026-11-01: configure is sent 5 s after start by a `TimerAction` |
| **hit** two lidar drivers or IMU nodes, `/imu/data` at about 200 Hz, `/scan` silent | the child nodes of an earlier `ros2 launch` outlived it (SIGINT from a non-interactive script is ignored) | stop with `kill -TERM`, then `pkill` the children by name; check `ps -eo cmd` for leftovers before each run |
| **hit** `ros2 lifecycle get /slam_toolbox` says `active` but the run just started failed | a slam_toolbox from an earlier run is still alive | same as above: check for stale processes first |
| **hit** Foxglove `/scan` shows '57 Infinity invalid values detected' | no-echo beams are `inf`, which Foxglove cannot colour | harmless; set Color mode to Flat |
| **hit** `ros2 topic hz`, `ros2 topic echo --once`, `tf2_echo` print nothing or `Failed to create publisher: rcl node's context is invalid` | the command-line tools are flaky on this Pi under load | retry; pipe `ros2 topic hz` into `grep 'average rate'` instead of a file; for a pose use `tf2_echo map base_footprint` a few times |
| **hit** `EKF Failed to get parameters: parameter 'imu1' is not initialized`, every 15 s | robot_localization probing for a second IMU | benign, ignore |
| **hit** lidar prints `RPLIDAR running` and no `RPLIDAR S/N` after a restart | restarted too soon after the stop (3 s, 12 s both hung on 2026-11-01), or the USB device was re-created | wait 20 s after stopping; if it repeats check `ls -l /dev/ttyUSB*` and the USB cable |
| **hit** `ffmpeg`/ALSA `Cannot get card index for U2K` (or for `2`), `Input/output error` opening the camera microphone | `robot` is not in the `audio` group; `/dev/snd/*` is `root:audio 0660` (card 2 is the camera's USB mic, `U2K`) | `sudo usermod -aG audio robot`, then log out and in (or reboot); check with `id` and `ffmpeg -f alsa -i plughw:2,0 -t 2 -f null -` |
| **hit** the lidar keeps spinning after the driver was stopped (no ROS node running) | the USB adapter's DTR line drives the motor and falls back to "on" when the port is closed | `python3 tools/streams/lidar_off.py` on the Pi asserts DTR and holds the port open (confirmed to stop the motor, 2026-11-02); stop it with `pkill -f lidar_off.py` before running `lidar.launch.py`, which cannot open the port while it runs |
| lidar motor on/off from Foxglove while the driver runs | `rplidar_ros` exposes `/stop_motor` and `/start_motor` (`std_srvs/Empty`); confirmed on 2026-11-02 | Foxglove, Call Service panel, service name `/stop_motor` or `/start_motor`, request `{}`, press Call; the motor stays stopped until `/start_motor` or a driver restart. With no driver running use `tools/streams/lidar_off.py` instead |
| **hit** an `ssh` command that mentions `ekf_node`, `rplidar_composition` or `slam_toolbox` ends with `exit 255` and no output the moment `/stack/*` is called | `robot_control.py` killed it as a stray: its stray pattern matched any command line containing those names | fixed 2026-11-02: the pattern is anchored to the executable path (`^(/usr/bin/python3 )?\S*/(name)( \|$)`), so a shell that only mentions a name is left alone |
| **hit** `/stack/mapping` replies `FAIL: mapping {'rplidar_composition': 0, 'ekf_node': 0}` on a stack that is in fact coming up | the launch needs 9 to 16 s on the Pi before its nodes exist; the first check was a fixed 8 s | fixed 2026-11-02: it polls up to 25 s and replies as soon as both processes exist (`pass after 10 s` to `16 s`) |
| **hit** a bag has `/marker` with 1 message, or 0, though two were published | the recorder logs `Recording...` about 2.5 s after `ros2 bag record` starts; markers sent before that are lost, and `ros2 topic pub --once` also makes a new publisher each time | `/bag/start` now returns only after `Recording...`; to test without Foxglove use `python3 tools/analysis/marker_pub.py "push start" 3 "push end"`, one persistent publisher |
| **hit** `/run/save` never replies, `.pgm`/`.yaml` written but no `.posegraph` | the first version awaited both `slam_toolbox` calls inside an async service callback on a single-threaded executor and the reply never arrived (`serialize_map` from the CLI answers `result=0` in about 9 s) | fixed 2026-11-02: blocking `Client.call` on a `MultiThreadedExecutor` with a reentrant callback group; the call takes about 25 s |
| **hit** `/pi/shutdown {data: true}` replies `sudo: a password is required` | no sudoers rule yet; the Pi stays up and nothing is stopped | add `/etc/sudoers.d/robot-power` (README, Foxglove buttons); `{}` is refused with `refused: send {data: true}` |
| `/camera/start` replies `camera running` but `/image_raw/compressed` is missing | `usb_cam` takes about 10 s to open the device and create the topics; the log shows `unknown control 'focus_auto'` and a missing calibration file, both harmless | wait 10 to 12 s; 9.9 Hz measured with `ros2 topic hz` |
| **hit** Foxglove Indicator tile always shows its fallback label (VIDEO OFF with the camera on, POWER OK while under-voltage) | the panel's `path` was the bare topic (`/robot/status/video`), so it saw the whole message and no rule matched | path must name the field: `/robot/status/video.data` (fixed in `cockpit_layout.json`, checked by `tools/tests/test_layouts.py`) (2026-11-03) |
| **hit** `ros2 topic echo` / `ros2 topic hz` on the Pi fail with `the given context is not valid, either rcl_init() was not called or rcl_shutdown() was called` or `rcl node's context is invalid`, while a plain rclpy script subscribes fine | not found; seen while the Pi was under-voltage (2026-11-03) | read the topic with a short rclpy script (`~/status_probe.py` on the Pi), or retry after `ros2 daemon stop` |
| **hit** `ros2 run ... -p name:=` aborts with `Couldn't parse parameter override rule: '-p init_pose_from_topic:='`, `rclcpp::exceptions::RCLInvalidROSArgsError` | rcl rejects an empty value in a parameter override | pass the empty string as `"name:=''"` (fixed in `tools/analysis/rf2o_fmt.sh`) |
| **hit** rf2o reads about 24 % of a hand push (`/odom_rf2o` x 0.29 m for 1.22 m) | a person within about 1 m behind the robot is a moving object in the scan; rf2o assumes a still room (OI-8) | nobody within 1 m of the robot during odometry runs, push with a stick. Offline, dropping ranges below 0.6 m before rf2o restores 95-99 % (2026-11-03) |
| **hit** `/odom_rf2o` shows `twist.linear.y` exactly 0 | rf2o is non-holonomic and never reports vy | not a fault; do not read sideways drift from the twist |
| **hit** after one launch the next one has no `/scan`: `rf2o` logs `Waiting for laser_scans....` forever, `rplidar_node` prints `RPLIDAR running` but never `RPLIDAR S/N`, AMCL logs no `createLaserObject`, Nav2 then fails with `Failed to activate global_costmap because transform from base_footprint to map did not become available before timeout` | the previous launch was started with `nohup ... &`, which ignores SIGINT, so `rplidar_node` was killed without its shutdown and left the lidar scanning; it recovers after one failed start | start stacks in the foreground and stop them with SIGINT (`timeout -s INT 50 ros2 launch ...`, or Ctrl+C); never background a launch with `&` for a test |

## CI

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** CI build-and-test fails in setup-ros: `curl: (22) The requested URL returned error: 404`, `exit code 22`; a rerun passes | setup-ros reads the ros-apt-source version from the GitHub API without a token; the shared runner IP hits the 60/hour limit, the tag is empty and the .deb URL 404s | fixed 2026-11-02: build-and-test runs in the `ros:jazzy-ros-base` container, no setup-ros |

## Reporting a problem

Put it in [`../notes.md`](../../notes/notes.md) with: date, exact error text, the command
that produced it, and what was tried. Then add a row here once it is understood.

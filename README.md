# delivery_bot

A two-wheel differential-drive robot that maps one room, then drives itself from a
taped home mark to named seats and back. Lidar-only odometry (no wheel encoders):
RPLidar A1M8 + MPU6050 gyro, fused by `robot_localization`, mapped and localised by
`slam_toolbox`, driven by Nav2 at 0.15 m/s.

> **This repository is a rebuild skeleton (2026-10-22).**
> Structure, configs, docs and `package.xml` files are complete, but every node,
> every launch file and the URDF body has been emptied down to its docstring and
> `NotImplementedError`. Write them yourself: each docstring states the contract
> that file must satisfy, and `docs/` describes the system it belongs to. The
> finished implementation is the tag `reference-v1` (`git checkout reference-v1`)
> if you want to compare once yours runs.

## Hardware

| Part | Detail |
| --- | --- |
| Compute | Raspberry Pi 4B, Ubuntu 24.04, ROS 2 Jazzy |
| Lidar | RPLidar A1M8, CP210x USB adapter, 115200 baud, `/dev/rplidar` (udev alias) |
| IMU | MPU6050 (GY-521), I2C bus 1, address `0x68`, gyro yaw rate only |
| Motors | 2× TT motor via L298N, Pi GPIO: ENA 12 / IN1 5 / IN2 6 / ENB 13 / IN3 20 / IN4 21 (BCM) |
| Power | Pi from a 5 V 3 A bank; motors from a separate 2×18650 pack through a kill switch |
| Viewing | Foxglove Studio on the team's Mac, `ws://<pi-ip>:8765` |

Wiring and power details: [`docs/wiring.md`](docs/wiring.md).

## Stack

| Job | Package |
| --- | --- |
| Lidar driver | `rplidar_ros` (apt) |
| Lidar odometry | `rf2o_laser_odometry` (source, pinned in `deps.repos`) |
| Fusion | `robot_localization` EKF, 2D mode |
| Mapping + localisation | `slam_toolbox` |
| Navigation | Nav2 — Regulated Pure Pursuit, Collision Monitor |
| Autonomous mapping | `explore_lite` — frontier exploration for one-shot mapping |
| Evaluation (later) | `slam_toolbox` replay + `evo` offline |
| Visualisation / logging | `foxglove_bridge`, `ros2 bag -s mcap` |
| Keyboard driving | `teleop_twist_keyboard` |

We write only the hardware glue: the L298N motor node, the MPU6050 IMU node, the
URDF, and the delivery scripts.

## Layout

```
delivery_bot_description/   URDF (xacro), no code
delivery_bot_drivers/       motor_node, imu_node, drivers.yaml
delivery_bot_bringup/       launch/ + config/ (EKF, slam_toolbox, Nav2) + maps/
delivery_bot_slam/          SLAM support: covariance relay, trajectory recorder,
                            explore and replay launches
delivery_bot_mission/       scan_stats, save_goal, deliver, goals.yaml
docs/                       plan, wiring, Pi setup, test log
deps.repos                  third-party source packages (rf2o, m-explore-ros2), pinned
```

## Quickstart (on the Pi)

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone git@github.com:samwee24/delivery_bot.git
vcs import . < delivery_bot/deps.repos
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -y
# m-explore-ros2 also ships multirobot_map_merge, a multi-robot package this robot does not use
colcon build --symlink-install --packages-skip multirobot_map_merge
source install/setup.bash
```

`rosdep` cannot install the GPIO/I2C Python libraries on Ubuntu 24.04, because it has
no keys for them. Install them with apt once (see [`docs/pi_setup.md`](docs/pi_setup.md)):

```bash
sudo apt install python3-smbus2 python3-gpiozero python3-lgpio
```

## Common commands

```bash
# base stack only: robot_state_publisher, lidar, IMU, motors (dry run), rf2o, EKF, Foxglove
ros2 launch delivery_bot_bringup base.launch.py

# mapping: base + slam_toolbox online async
ros2 launch delivery_bot_bringup mapping.launch.py dry_run:=false

# navigation: base + slam_toolbox localization + Nav2
ros2 launch delivery_bot_bringup navigation.launch.py map:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_bringup/maps/room

# autonomous mapping: frontier exploration, no human driving
ros2 launch delivery_bot_slam explore.launch.py dry_run:=true   # skeleton: starts driving immediately

# SLAM evaluation: replay a recorded bag, mapping or localization
ros2 launch delivery_bot_slam slam_replay.launch.py slam_mode:=mapping   # offline, from a bag

# keyboard driving (Motors: see safety below)
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true

# recording
ros2 bag record -s mcap /scan /imu/data /cmd_vel /odom_rf2o /odometry/filtered /tf /tf_static

# save the map (while mapping runs; writes into the repo through symlink-install)
ros2 run nav2_map_server map_saver_cli -f $HOME/ros2_ws/src/delivery_bot/delivery_bot_bringup/maps/room
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph \
  "{filename: '$HOME/ros2_ws/src/delivery_bot/delivery_bot_bringup/maps/room'}"

# goals and delivery
ros2 run delivery_bot_mission save_goal seat_1
ros2 run delivery_bot_mission deliver seat_1 seat_2

# lidar diagnostics
ros2 run delivery_bot_mission scan_stats
```

## Foxglove

Connect to `ws://100.83.14.99:8765` (Tailscale: works on any network; the LAN address `192.168.31.109` only works on the Pi's own Wi-Fi) (Jazzy + `foxglove_bridge`). Panels: 2D/3D plot for
`/scan`, `/odometry/filtered`, `/map`; Publish for goals; Timeline for bag replay.
The bridge holds port 8765 between runs — `sudo fuser -k 8765/tcp` if a relaunch
refuses to bind.
The camera is `ros2 launch delivery_bot_bringup camera.launch.py`; show `/image_raw/compressed`, and
hide the raw topic by starting the bridge with
`ros2 run foxglove_bridge foxglove_bridge --ros-args -p 'topic_whitelist:=["^(?!/image_raw$)(?!/image_raw/(zstd|theora|compressedDepth)).*"]'`.
The lidar, camera and bridge do not restart after a reboot, and the camera takes a full core: leave it off during mapping.

**Side extras for watching the robot** (not part of the SLAM stack; `tools/`):
- `bash tools/start_streams.sh` starts the camera, the bridge, the microphone stream and the control node; `bash tools/start_streams.sh av` starts one combined picture-and-sound stream instead (`vlc http://100.83.14.99:8090/stream.mkv`, 1280x720 at 30 fps). The streams do not restart after a reboot. Needs `robot` in the `audio` group.
- Foxglove Call Service panel: `/stream/start` and `/stream/stop` (`tools/stream_control.py`) switch the combined stream on and off; `/start_motor` and `/stop_motor` (the lidar driver's own services) spin the lidar motor up and down. With no driver running, `python3 tools/lidar_off.py` holds the motor off.
- Speech or voice commands could read the same stream later (see `tools/audio_stream.py`); not built.

## Safety

- **Motors start in dry run.** `base.launch.py` and `navigation.launch.py` default
  `dry_run:=true`; only `mapping.launch.py` forwards it explicitly. Turning it off is
  always a deliberate act.
- **First live test with the wheels off the ground.** Nothing moves on the floor until
  the dead zone/gain calibration is done with the robot raised.
- The **motor switch is the kill switch**; there is no software emergency stop that
  can override a stuck L298N.
- The motor node stops both channels if no `/cmd_vel` arrives for 0.5 s, on Ctrl+C,
  and on any exception.
- `v_max` is 0.15 m/s. Do not raise it casually: the planner, the smoother and the
  controller are all tuned to it.

## Deviations from the team brief

Recorded here because they change how you use the repo:

- **`use_stamped` defaults to true.** Nav2 Jazzy's controller publishes
  `geometry_msgs/TwistStamped` by default (`enable_stamped_cmd_vel` no longer exists
  in Jazzy's controller). `teleop_twist_keyboard` still defaults to plain `Twist`, so
  pass `-p stamped:=true` when driving by keyboard.
- **Lidar executable is `rplidar_composition`**, not `rplidar_node`: the Jazzy apt
  package is the Slamtec composition node. `lidar.launch.py` uses the installed name.
- **Motor pins are flat parameters** (`ena_pin`, `in1_pin`, …) rather than a nested
  `pins` dict, because declaring nested dicts in rclpy is awkward and error-prone.
- **GPIO/I2C Python libraries are apt, not rosdep** (`python3-gpiozero`,
  `python3-lgpio`, `python3-smbus2`); rosdep has no Ubuntu 24.04 keys for them.
- **Map saving writes into the source tree** (`delivery_bot_bringup/maps`) so the map
  can be committed; `--symlink-install` makes that the installed share directory too.
- **`slam_toolbox` 2.8.5 is a lifecycle node.** Both launches use
  `launch_ros.actions.LifecycleNode` with configure then activate rather than a plain
  `Node`; a plain `Node` looks healthy and publishes nothing. See
  [`docs/slam.md`](docs/slam.md).
- **rf2o publishes zero covariance**, so a relay rewrites the twist covariance before
  the EKF; without it the EKF treats rf2o's yaw rate as perfect and the gyro barely
  contributes. See [`docs/slam.md`](docs/slam.md).

## Docs

- [`docs/plan.md`](docs/plan.md) — phases and what "done" means
- [`docs/slam_build_path.md`](docs/slam_build_path.md) — the SLAM section as 45 ordered tasks, with a Progress list
- [`docs/slam_journal.md`](docs/slam_journal.md) — answers, numbers and commit hashes per build-path task
- [`docs/slam.md`](docs/slam.md) — SLAM plan, known issues, evaluation
- [`docs/foxglove/README.md`](docs/foxglove/README.md) — the SLAM layout and its controls
- [`docs/wiring.md`](docs/wiring.md) — pins and power
- [`docs/pi_setup.md`](docs/pi_setup.md) — Ubuntu/Jazzy setup, udev, groups, Ghostty
- [`docs/test_log.md`](docs/test_log.md) — the test record table

## Project log and coursework record (CA3)

This repository is also the assessed CA3 project for MA4890. The record lives beside
the code so it cannot drift from it:

- [`docs/CA3.md`](docs/CA3.md) — target machine, decisions D1–D6, phase status, open issues OI-1…OI-5
- [`notes/notes.md`](notes/notes.md) — dated lab notebook, newest first, append-only
- [`docs/design-plan.md`](docs/design-plan.md) — the Oct 8 design plan (superseded in part by D5)
- [`docs/system/`](docs/system/) — hardware, Pi setup, bring-up, architecture, config, troubleshooting, ROS stack
- [`evidence/`](evidence/) — dated raw artefacts; [`report/`](report/) — the CA3 report draft
- [`AGENTS.md`](AGENTS.md) — how to work here, including the sync rules between Mac, GitHub and the Pi

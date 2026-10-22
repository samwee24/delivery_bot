# delivery_bot

A two-wheel differential-drive robot that maps one room, then drives itself from a
taped home mark to named seats and back. Lidar-only odometry (no wheel encoders):
RPLidar A1M8 + MPU6050 gyro, fused by `robot_localization`, mapped and localised by
`slam_toolbox`, driven by Nav2 at 0.15 m/s.

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
| Visualisation / logging | `foxglove_bridge`, `ros2 bag -s mcap` |
| Keyboard driving | `teleop_twist_keyboard` |

We write only the hardware glue: the L298N motor node, the MPU6050 IMU node, the
URDF, and the delivery scripts.

## Layout

```
delivery_bot_description/   URDF (xacro), no code
delivery_bot_drivers/       motor_node, imu_node, drivers.yaml
delivery_bot_bringup/       launch/ + config/ (EKF, slam_toolbox, Nav2) + maps/
delivery_bot_mission/       scan_stats, save_goal, deliver, goals.yaml
docs/                       plan, wiring, Pi setup, test log
deps.repos                  third-party source packages (rf2o), pinned
```

## Quickstart (on the Pi)

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone git@github.com:samwee24/delivery_bot.git
vcs import . < delivery_bot/deps.repos
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install
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

Connect to `ws://<pi-ip>:8765` (Jazzy + `foxglove_bridge`). Panels: 2D/3D plot for
`/scan`, `/odometry/filtered`, `/map`; Publish for goals; Timeline for bag replay.
The bridge holds port 8765 between runs — `sudo fuser -k 8765/tcp` if a relaunch
refuses to bind.

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

## Docs

- [`docs/plan.md`](docs/plan.md) — phases and what "done" means
- [`docs/wiring.md`](docs/wiring.md) — pins and power
- [`docs/pi_setup.md`](docs/pi_setup.md) — Ubuntu/Jazzy setup, udev, groups, Ghostty
- [`docs/test_log.md`](docs/test_log.md) — the test record table

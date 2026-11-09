# 07 · ROS 2 stack — what is actually installed

**Verified on `sherm-raspi`, 2026-10-22.** This page describes the running system,
not an intention. Where it disagrees with `design-plan.md`, this page wins.

## Workspace

```
~/ros2_ws/
  src/
    delivery_bot/                 git repo, commit 9e2fd2e "Initial delivery_bot stack"
      delivery_bot_bringup/       launch + config (ekf, slam_mapping, slam_localization, nav2_params)
      delivery_bot_description/   URDF / xacro
      delivery_bot_drivers/       imu_node, motor_node (rclpy)
      delivery_bot_mission/       delivery/goal logic
      docs/
    rf2o_laser_odometry/          third-party, branch `ros2`, HEAD b38c68e
  build/ install/ log/            never committed
```

Build: `colcon build --symlink-install` — **5 packages, 3 min 43 s**, `rf2o` alone
3 min 17 s. Build with `--executor sequential --parallel-workers 1` on this Pi; a
parallel build without swap took the machine off the network (see `notes.md`,
2026-10-22 incident).

Verify:

```bash
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
ros2 pkg prefix rf2o_laser_odometry      # -> /home/robot/ros2_ws/install/rf2o_laser_odometry
```

## Ownership of `tf` — the one rule that breaks everything

| Transform | Publisher | Must not be published by |
| --- | --- | --- |
| `odom → base_footprint` | **`ekf_filter_node` only** | rf2o (`publish_tf: false`), the lidar driver, anything else |
| `base_footprint → base_link → laser` | `robot_state_publisher` from the URDF | — |
| `map → odom` | `slam_toolbox`: mapping, or `localization_slam_toolbox_node` in `navigation.launch.py` (resolves, test_log 2026-11-01, 6.2) | `robot_localization` (`world_frame: odom`) |

Two publishers of one transform makes the map spin and looks exactly like a broken
lidar. If the map rotates on the spot, check `ros2 run tf2_tools view_frames` before
touching any filter.

## Nodes

| Node | Package | Publishes | Subscribes | Key parameters |
| --- | --- | --- | --- | --- |
| `rplidar_node` | `rplidar_ros` (`rplidar_composition`) | `/scan` | — | `serial_port: /dev/rplidar`, `115200`, `frame_id: laser`, `angle_compensate: true`, `scan_mode: Standard` |
| `rf2o_laser_odometry` | built from source | `/odom_rf2o` (velocity) | `/scan` | `publish_tf: false`, `base_frame_id: base_footprint`, `odom_frame_id: odom`, `freq: 10.0` |
| `imu_node` | `delivery_bot_drivers` | `/imu/data` | — | `bus 1`, `address 104` (0x68), `rate_hz 100`, 3 s bias calibration, `calib_max_std 0.01` |
| `ekf_filter_node` | `robot_localization` | `odometry/filtered`, **`odom → base_footprint`** | `/odom_rf2o_cov` (rf2o via `odom_covariance_relay`, test_log 2026-10-30, 4.3), `/imu/data` | `two_d_mode`, `20 Hz` (lowered from 30, `ekf.yaml`; 19.93 Hz measured, test_log 2026-11-01), `world_frame: odom` |
| `motor_node` | `delivery_bot_drivers` | — | `/cmd_vel` (`TwistStamped`) | pins 12/5/6/13/26/16, `pwm_hz 1000`, 20 Hz control, duty = `min_duty 0.11` + `gain` × \|wheel speed\| clamped to `max_duty 0.85`, `watchdog_s 0.5`, lidar stop (`stop_dist_m 0.20`, ±35°), stale-scan stop (`scan_timeout_s 0.5`); **`dry_run` default true, the launch file passes it; live needs `dry_run:=false` on the command line** |
| `foxglove_bridge` | `foxglove_bridge` | — | — | `port 8765`, `address 0.0.0.0` |
| `robot_state_publisher` | — | `tf`, `robot_description` | — | URDF via `xacro` |
| `run_save` | `delivery_bot_slam` (started by `mapping.launch.py`) | service `/run/save` | calls `/slam_toolbox/save_map`, `/slam_toolbox/serialize_map` | `maps_dir ~/maps`; map, pose graph and config YAMLs under one dated name |
| `robot_control` | `tools/robot_control.py`, outside the packages | `/marker` topic (created, never published), services `/stack/*`, `/camera/*`, `/stream/*`, `/bag/*`, `/control/status`, `/pi/*` | — | `bag_label`, `bag_topics`; starts and stops whole stacks in their own process groups; run by `robot-control.service` |

`imu_node` also serves `/imu_node/recalibrate` (`Trigger`: re-measure gyro bias, fails if the board moves).

Launches: `base.launch.py` (everything above), `lidar.launch.py`, `mapping.launch.py`,
`navigation.launch.py`. `base.launch.py` starts `motor_node` and declares `dry_run:=true` (passed to `motor_node`), `use_sim_time:=false` and `bridge:=true`;
`mapping` and `navigation` pass `bridge` through. For the experiments `base.launch.py` also takes `ekf` (`false` = identity `odom -> base_footprint`, no EKF) and `ekf_params_file` (`config/ekf_variants/`), and `navigation.launch.py` forwards both and adds `localizer:=slam|amcl` (AMCL: `map_server` on `map_yaml`, `amcl` from `config/amcl.yaml`, Nav2 5 s later); defaults keep the old behaviour. `robot_control` starts stacks with `bridge:=false` because it owns the one
Foxglove bridge on port 8765 (two bridges fight for the port). The buttons are tabulated in the README.

## What the EKF fuses, and why

`robot_localization`, 2D mode, deliberately minimal (`bringup/config/ekf.yaml`):

- **rf2o → `vx` and `vyaw` only.** Its absolute x/y drifts, so the filter integrates
  velocity itself rather than trusting a position.
- **MPU6050 → `vyaw` only.** No accelerometer (noisy), no absolute yaw (no
  magnetometer, nothing absolute to trust).

Consequence worth writing down: **there is no absolute position input.** The EKF's
x/y come from integrating velocity, so drift accumulates exactly as in the original
plan — just inside `robot_localization` instead of our own filter.

## Parameters that are placeholders

`drivers.yaml` marks these; none may be reported as measured:

| Parameter | Placeholder | Filled in by |
| --- | --- | --- |
| `wheel_base` | 0.156 (measured 2026-10-31) | tape measure |
| `min_duty` | 0.11, one value for both wheels; replaces `dead_zone_left/right` (commented out in the YAML). The teammate's 12 V test, no `test_log` row yet | P6 calibration, logged |
| `gain_left/right` | 2.0 duty per m/s | P6 calibration |
| `gyro_scale_z` | 1.0 (measured 2026-10-31, one hand turn, -360.2° for 360°; test_log 2026-10-31) | 5-spin test still to do |
| `ekf.yaml` covariances | defaults; the rf2o twist variances (`vx_variance` 1e-4, `vyaw_variance` 5e-3) and `gyro_var` 1e-4 are fitted 2026-10-31 from two hand-moved bags (test_log 2026-10-31, 4.4) | recheck with motors running |

## Gotchas that have already bitten, or will

1. **`dry_run` defaults to `true`.** `motor_node` computes and logs duties but never
   touches GPIO until you pass `dry_run:=false`. Good default; surprising if forgotten.
   Live, it also stops linear motion at 0.20 m (±35°) and stops on a stale scan.
2. **Jazzy publishes `TwistStamped`.** Nav2 does; `teleop_twist_keyboard` needs
   `-p stamped:=true`, otherwise the robot ignores commands and looks dead.
3. **`twist_mux`/safety layer is not in the launch file yet.** The plan's "safety node
   owns the motors" rule is not yet enforced — `motor_node` subscribes to `/cmd_vel`
   directly. Until a mux exists, the watchdog (`0.5 s`) and the lidar stop in `motor_node` are the protection.
4. **Stale Foxglove bridge holds 8765**: `sudo fuser -k 8765/tcp` before relaunching.
5. **Non-interactive SSH does not source `.bashrc`** — always `source /opt/ros/jazzy/setup.bash`
   and `source ~/ros2_ws/install/setup.bash` explicitly in the command.

## Foxglove

```bash
ros2 launch delivery_bot_bringup base.launch.py        # bridge included on 8765
# or press /stack/base in Foxglove once robot_control.py runs (it starts the bridge itself)
```

Connect Foxglove Studio to `ws://100.83.14.99:8765` (Tailscale) or
`ws://192.168.31.109:8765` (LAN). The `/scan` display is the fastest way to judge
whether a mounting change helped: fixed holes in the ring = room or robot geometry;
holes that persist in *every* direction = optics (OI-4).

## Logging

`rosbag2` with MCAP is installed:

```bash
ros2 bag record -s mcap /scan /imu/data /odom_rf2o /odometry/filtered /cmd_vel /tf
```

Bags get large (hundreds of MB per drive) — keep them on the Pi or a shared drive,
never in git.

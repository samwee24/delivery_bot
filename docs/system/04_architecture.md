# 04 · Architecture

> **Superseded in part (D5, 2026-10-22).** The pipeline table below records the
> own-node design (D4). v1 now runs the standard package stack — see
> [07_ros_stack.md](07_ros_stack.md). The contracts and modes sections still apply,
> with the package occupying the stage: clock discipline, angle sign, heading wrap,
> config-not-constants and safety are unchanged; "outlier gate" and "replay" now
> belong to the rf2o/EKF and bag workflows described there.

The pipeline itself is specified in [`design-plan.md`](../design-plan.md) §2 — this page
records how it is deployed now that ROS 2 is in scope, plus the contracts that are
easy to break later.

## One process, or many?

The plan says one Python process with threads. Under ROS 2 each stage becomes its
own node, so threads become subscriptions. The state object with its lock and
newest-item queue survives as the *intra*-node pattern wherever one node does two
things (EKF predict+update, planner+controller).

| Plan stage | ROS node (actual) | Package | Rate |
| --- | --- | --- | --- |
| 1. Lidar input | `rplidar_node` → `/scan` | `rplidar_ros` | 5–7 Hz (one scan per revolution) |
| 2. Gyro input | `imu_node` → `/imu/data` | `delivery_bot_drivers` | 100 Hz |
| 3. Lidar odometry | `rf2o_laser_odometry` → `/odom_rf2o` (velocity) | built from source | 10 Hz |
| 4. Pose fusion | `ekf_filter_node` → `odometry/filtered` + `odom→base_footprint` | `robot_localization` | 30 Hz |
| 5. Mapping | `slam_toolbox` | apt | on scan |
| 6. Planning | Nav2 | `nav2_bringup` | on goal |
| 7. Control | `motor_node` | `delivery_bot_drivers` | 20 Hz |
| 8. Safety | **not yet built** — `motor_node` watchdog only | — | 0.5 s timeout |

See [07_ros_stack.md](07_ros_stack.md) for topics, frames and Foxglove panels.

## Contracts that must not drift

1. **Clock.** Lidar and IMU timestamps come from the same clock. On the Pi, use
   `time.monotonic()` for intervals and one conversion to wall time at the top.
   KISS-ICP deskew depends on per-point timestamps: `t_scan_start + angle/360 × period`.
2. **Angles.** RPLidar reports **clockwise** degrees; negate, then apply the mount
   offset, so the robot frame is x forward / y left. Negating twice is the single
   easiest way to produce a mirrored map.
3. **Heading wrap.** Every angle error is wrapped to (−π, π] before an EKF update.
   Missing this makes the filter think a full turn happened.
4. **Outlier gate.** Reject a KISS-ICP result jumping >0.3 m or >30° from the last.
   At 0.15 m/s that cannot be real motion; it is almost always a bad match on a
   feature-poor scan — and with a 33 % echo rate, feature-poor scans are common.
5. **Safety is not optional.** Intended: motors get commands only from a safety node.
   **Actual (2026-10-22): `motor_node` subscribes to `/cmd_vel` directly** — there is no
   mux or safety node yet, so the only protection is the 0.5 s watchdog, `max_duty: 0.85`,
   and `dry_run` defaulting to `true`. Closing this gap is a P7/prequel task, not a
   nice-to-have: Nav2 publishes `TwistStamped`, and a stale or runaway publisher is
   one launch file away.
6. **Unknown space is blocked.** Planning treats occupied *and* unknown cells as
   obstacles, so the robot never plans through space it has not seen.
7. **Config, never constants.** Every number lives in YAML. See
   [05_config_reference.md](05_config_reference.md).

## Modes

| Mode | Map | Driver |
| --- | --- | --- |
| **Mapping** (P2–P5) | built, logged | human, keyboard teleop |
| **Navigation** (P7–P8) | loaded and **frozen** | pure pursuit on A\* path |

Both share the estimation stack; only the mapper and the goal source differ.

## Replay

The plan's tuning loop — record on the Pi, replay on the laptop — is now:

```bash
ros2 bag record /scan /imu/data /odometry/filtered /cmd_vel /plan    # on the Pi
ros2 bag play <bag> --clock                                          # on the laptop
```

The nodes must be runnable off-robot: pure-python code with no ROS imports inside,
ROS only at the edges. That is the test — if `kiss_icp` or the EKF needs a ROS
graph to be exercised, the layering has leaked.

## Risks

| Risk | Why here | Mitigation |
| --- | --- | --- |
| Sparse scans break ICP | 33 % echo rate, 95 pts/rev | settle OI-4 first; raise `min_range` filter, tighten the mask, consider `min_len` |
| Compile of `kiss-icp` on the Pi | no aarch64 wheel, no swap by default | add a 2 GB swapfile first; allow 10–30 min |
| GPIO on Ubuntu | plan assumed Pi-OS `lgpio` | decide `lgpio` pip vs Blinka before P1 motors |
| Headless debugging | Pi has no display | Foxglove + rosbag; never rely on local plots |

# 05 · Config reference

Every number the robot runs on lives in YAML inside the packages, not in code:

| Contract file | Actual file |
| --- | --- |
| driver parameters | `delivery_bot_drivers/config/drivers.yaml` |
| EKF fusion | `delivery_bot_bringup/config/ekf.yaml` |
| mapping / localisation | `delivery_bot_bringup/config/slam_{mapping,localization}.yaml` |
| planning and control | `delivery_bot_bringup/config/nav2_params.yaml` |
| named goals | `delivery_bot_mission/config/goals.yaml` |

The `robot.yaml` block below is the **contract**: the numbers that are mapped into
those package files. Where a key has no home in a package file yet, this page is the
record of the intended value.

**Provenance is recorded per key:** *brief default* (from
[`../design-plan.md`](../design-plan.md) §3), *measured* (tape measure on the robot),
or *fitted* (from a replay). Nothing marked MEASURE may be reported as a result until
it is actually measured.

## `robot.yaml`

```yaml
wheel_base_m: 0.13          # MEASURE  left→right tyre centre
wheel_diameter_m: 0.065     # MEASURE  nominal 65 mm
robot_radius_m: 0.10        # MEASURE  centre→farthest point; sets map inflation
lidar:
  port: /dev/rplidar        # udev alias, not the raw /dev/ttyUSB0
  model: A1M8
  baudrate: 115200
  offset_xy_m: [0.0, 0.0]   # MEASURE  lidar centre relative to wheel midpoint
  yaw_offset_deg: 0.0       # MEASURE  box-at-50 cm test
  min_range_m: 0.15
  max_range_m: 8.0
  mask_deg: []              # MEASURE  e.g. [[230, 250]] for the 0.23 m returns seen on the old Pi
imu:
  bus: 1
  address: 0x68
  rate_hz: 100
  calib_seconds: 3          # refuse to start if the robot moves during this
motors:
  pins: {ena: 12, in1: 5, in2: 6, enb: 13, in3: 20, in4: 21}
  pwm_hz: 1000
  max_duty: 0.85
  dead_zone: {left: 0.35, right: 0.35}   # FITTED in P6
  gain: {left: 2.0, right: 2.0}          # duty per m/s, FITTED in P6
control:
  v_max: 0.15               # m/s cap — safety, do not raise casually
  omega_max: 1.0            # rad/s
  lookahead_m: 0.25
  goal_tol_m: 0.10
safety:
  stop_dist_m: 0.20
  stop_half_angle_deg: 35
  watchdog_s: 0.5
map:
  resolution_m: 0.05
  size_m: 12.0              # 240×240 cells, home at the centre
```

## `ekf.yaml` — `robot_localization`, `two_d_mode: true` (D5)

| Parameter | Start value | Notes |
| --- | --- | --- |
| `frequency` | 30 | Hz; fine on the Pi at 0.15 m/s |
| `two_d_mode` | `true` | planar robot; no z/roll/pitch |
| `odom0` | `/odom` (rf2o) | fuse **vx** and **vyaw** only |
| `imu0` | `/imu/data` (MPU6050) | fuse **vyaw only** — no accelerometer, no absolute yaw |
| `publish_tf` | `true` | publishes `odom → base_link` |
| covariances | default first | tuned from P4 replay, recorded per run |

## `nav2_params.yaml` / `slam_toolbox.yaml`

The `control:`, `safety:` and `map:` keys in `robot.yaml` above are the **contract
values**; they are mapped into the package config files at run time:

| `robot.yaml` key | Lands in |
| --- | --- |
| `control.v_max`, `omega_max`, `lookahead_m` | Nav2 RPP controller (`desired_linear_vel`, `max_angular_vel`, `lookahead_dist`) |
| `control.goal_tol_m` | Nav2 goal checker |
| `safety.stop_dist_m`, `stop_half_angle_deg` | Collision Monitor polygon; motor-node watchdog follows `watchdog_s` |
| `map.resolution_m`, `size_m` | `slam_toolbox` `resolution` / map bounds, occupancy grid |

## `goals.yaml` (P8)

```yaml
home:    [x_m, y_m, yaw_deg]   # MEASURE: the taped home mark
seat_1:  [x_m, y_m, yaw_deg]   # MEASURE
```

## Known config values with evidence behind them

| Key | Value | Source |
| --- | --- | --- |
| `lidar.port` | `/dev/rplidar` | udev rule `99-rplidar.rules`, verified on the old Pi |
| `lidar.baudrate` | `115200` | `get_info()` returned at 115200; 256000 timed out |
| `lidar.model` | `A1M8` | `get_info()['model'] == 24` |
| `lidar.max_range_m` | `8.0` | longest echo seen 8.7 m, but 67 % of pings silent → keep conservative |
| `lidar.mask_deg` | *candidate* `[[230, 250]]` | 0.23 m returns at raw 230–250°, old Pi |

Everything else is still the brief's default, not a measurement.

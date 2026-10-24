# SLAM — mapping, localisation and evaluation

This section turns a lidar scan and a gyro into a map of one room, and then keeps the
robot's position inside that map while Nav2 drives it. It owns the two `slam_toolbox`
modes, the small `delivery_bot_slam` package that sits between rf2o and the EKF and
records trajectories, the SLAM side of the URDF frame tree, the bag-replay recipe that
makes any of it reproducible, and the plan for measuring whether a map is any good.
Nothing here is a result yet: every value that has not been measured on the robot
carries `# MEASURE`, `# CALIBRATE` or `# TUNE`, and [§9](#9-open-items-and-measure-list)
lists all of them in one place.

Work through this in order with [slam_build_path.md](slam_build_path.md); record answers in [slam_journal.md](slam_journal.md).

The dependencies this section assumes and does not own: the lidar driver and its echo
rate (OI-4), rf2o and the EKF tuning, Nav2's controller and costmaps, and the Foxglove
bridge. Where this file needs a change in one of those, it is an interface request in
[§8](#8-interface-requests-to-teammates), not an edit.

| This section owns | This section does not own |
| --- | --- |
| `delivery_bot_bringup/launch/mapping.launch.py`, `navigation.launch.py` | `base.launch.py` (bringup owner) — this section only requests a change to it |
| `delivery_bot_bringup/config/slam_mapping.yaml`, `slam_localization.yaml` | `ekf.yaml` process noise and `odom0_config` (odometry section); this section owns only the `odom0` *topic* change |
| `delivery_bot_slam/` — covariance relay, trajectory recorder, explore and replay launches, its configs and test | rf2o itself (never forked, never patched) |
| `laser` and `imu_link` geometry in the URDF, and the `base_footprint` link | the rest of the URDF: body, wheels, visuals |
| the map-saving procedure and the naming of map artefacts | Nav2 parameters, behaviour tree and `explore_lite`'s own code |
| the replay contract (which topics may be replayed) | recording the bags (bringup owner) and the Foxglove layout |
| the evaluation plan for mapping and localisation | delivery logic and named goals (`delivery_bot_mission`) |

## 1. Architecture

The chain below is the whole section. It is drawn with the EKF in the middle because
everything downstream of it is a consumer of one of two things: a velocity estimate or
a transform. There is no path from Nav2 back into the EKF; that omission is deliberate
and is argued in [§2](#2-design-decisions-with-sources).

```
  RPLidar A1M8            rplidar_node
  5–7 Hz, OI-4   ───────► /scan ───────────────────────────────────────┐
  /dev/rplidar                                                         │
  115200 baud                                                          │
                                                                       │
                                                          ┌────────────▼─────────────┐
                                                          │  rf2o_laser_odometry     │
                                                          │  10 Hz                   │
                                                          │  publish_tf: false       │
                                                          └────────────┬─────────────┘
                                                                       │ /odom_rf2o
                                                                       │ (twist covariance all zero)
                                                          ┌────────────▼─────────────┐
                                                          │ odom_covariance_relay    │
                                                          │ delivery_bot_slam        │
                                                          └────────────┬─────────────┘
                                                                       │ /odom_rf2o_cov
                                                                       │
  MPU6050 0x68           imu_node                                      │
  yaw rate only  ───────► /imu/data ────────────────────────┐           │
  100 Hz                                                   │           │
                                                           ▼           ▼
                                                    ┌──────────────────────┐
                                                    │  ekf_filter_node     │
                                                    │  robot_localization  │
                                                    │  2D, 30 Hz           │
                                                    │  world_frame: odom   │
                                                    └──────┬────────┬──────┘
                                        odom→base_footprint│        │ /odometry/filtered
                                     (TF, sole publisher)  │        │
                                                           │        ▼
                                                           │  ┌──────────────────────┐
                                                           │  │ trajectory_recorder  │
                                                           │  │ /odom/path           │
                                                           │  │ /slam/path (needs    │
                                                           │  │  map→base_footprint) │
                                                           │  └──────────────────────┘
                                                           │
  /scan ───────────────────────────────────────────────────┼──►┌──────────────────────┐
                                                           │   │  slam_toolbox        │
                                                           │   │  mapping  (P5)       │
                                                           └──►│  localisation (P7)   │
                                                               └──────┬───────────────┘
                                                                      │ /map
                                                                      │ map→odom (TF)
                                                                      ▼
                                                               ┌──────────────────────┐
                                                               │ explore_lite         │
                                                               │ exploration only     │
                                                               └──────┬───────────────┘
                                                                      │ NavigateToPose action
                                                                      ▼
                                                               ┌──────────────────────┐
                                                               │ Nav2                 │
                                                               │ (planner+controller) │
                                                               └──────────────────────┘
```

Two consequences of that shape:

- `slam_toolbox` never sees a position. It reads `/scan` and the current
  `odom → base_footprint` transform, matches the scan against its graph, and *writes*
  `map → odom`. All the absolute information in the system is created at that node.
- `trajectory_recorder` is a tap, not a filter. It reads transforms and republishes
  them as paths; removing it changes no estimate.

### 1.1 Which component owns which transform

| Transform | Publisher | Frame source | Must never be published by |
| --- | --- | --- | --- |
| `base_footprint → base_link` | `robot_state_publisher` | URDF (fixed joint) | the EKF |
| `base_link → laser` | `robot_state_publisher` | URDF, `laser_x/y/z` + `laser_yaw` | the lidar driver (`frame_id: laser` only) |
| `base_link → imu_link` | `robot_state_publisher` | URDF, `imu_x/y/z` | `imu_node` |
| `odom → base_footprint` | `ekf_filter_node` only | fused velocities | rf2o (`publish_tf: false`), `slam_toolbox`, anything else |
| `map → odom` | `slam_toolbox` | scan matching | `robot_localization` (`world_frame: odom`), Nav2, `map_server` |
| `map → base_footprint` | nobody | composed from the two above | — |

**The rule: exactly one publisher per transform.** Two publishers of the same pair do
not conflict loudly — the consumer silently takes whichever arrives last, so the map
jumps or spins and the symptom looks like a broken lidar. Check before touching a
filter:

```bash
ros2 run tf2_tools tf2_monitor map base_footprint   # lists every authority per edge
ros2 topic info /tf --verbose                       # publishers of dynamic tf
```

`base_footprint` is a URDF link even though its *transform from `odom`* comes from the
EKF. The URDF supplies the link and the fixed joint to `base_link`; the EKF supplies
the moving parent. Without the link, `robot_state_publisher` has nothing to hang
`base_link` from and the whole tree below `base_footprint` disappears. This is the
correction recorded as §3.3.

### 1.2 Mapping and localisation are two modes, not two nodes we wrote

| | Mapping | Localisation |
| --- | --- | --- |
| Config | `slam_mapping.yaml` | `slam_localization.yaml` |
| Executable | `async_slam_toolbox_node` | `localization_slam_toolbox_node` |
| `mode` parameter | `mapping` | `localization` |
| Launch file | `mapping.launch.py` (and `explore.launch.py`) | `navigation.launch.py`, `slam_replay.launch.py` |
| Map input | none — built from scans | `map_file_name` from the `map:=` argument (serialised posegraph) |
| `/map` | rebuilt and republished every `map_update_interval` (5.0 s; 2.0 s under exploration) | loaded from `.posegraph` + `.data` once, then frozen |
| `map → odom` | from scan matching; moves in a jump when a loop closes | from scan matching against the frozen graph |
| CPU on the Pi | higher: the graph and the occupancy grid both grow | lower: no new nodes, no loop search worth the name |
| Lifetime | one mapping session per room, then save | every delivery run |
| Saving | `map_saver_cli` (grid) **and** `serialize_map` (graph) | none; it reads what mapping saved |

Mapping and localisation are the two executables of `slam_toolbox` [MJ21]; both are
lifecycle nodes and both need the launch pattern in §3.1. A mode
mismatch is not an error message: launching the mapping config for a delivery run
builds a new map from scratch and ignores the saved one, and launching the
localisation config without `map_file_name` fails at configuration with a missing-file
error only in the log.

## 2. Design decisions, with sources

Four decisions shape everything above. Each is stated with the thing it costs, because
each cost is visible later as a limitation rather than a bug.

- **Graph-based SLAM (`slam_toolbox`) rather than a particle filter.** The review of
  2D lidar SLAM sorts the field into scan-matching, graph-based, particle-filter and
  learning-based families, and graph methods are the ones that keep a whole-room map
  consistent because poses are optimised jointly rather than fixed as they are
  acquired [R25]. `slam_toolbox` is that kind of system: a pose graph built online,
  optimised with Ceres, with a serialisable map and a localisation mode [MJ21]. Filter
  methods (FastSLAM, grid-based particle SLAM) instead carry the whole map in the
  particle state and assume a usable motion model — usually wheel odometry — to
  propagate it [R25]. This robot has no encoders, so a filter's motion model would be
  the EKF's integrated velocity, whose uncertainty grows without bound and is not
  Gaussian after a slip. Consequence: map quality depends on scan-matching quality, so
  a poor `odom → base_footprint` deforms the map between loop closures rather than
  merely drifting.

- **Encoder-free odometry: rf2o plus gyro through `robot_localization`.** rf2o recovers
  planar motion from the range flow between consecutive scans, which is exactly the
  quantity that can stand in for wheel encoders on a differential-drive base [J16].
  The same encoder-free pipeline — lidar range-flow velocity fused with a MEMS gyro in
  an EKF — is what Kudriashov et al. run on a comparable robot under Jazzy [K26].
  Consequence: heading is integrated from the gyro, so it drifts slowly (no
  magnetometer, nothing absolute), and x/y is integrated from lidar-derived velocity,
  so it drifts with scan-match noise; SLAM corrects both only where it can close a
  loop.

- **No AMCL, and no SLAM pose fed back into the EKF.** Kudriashov et al. found that
  feeding a localisation estimate back into the filter degraded repeatability in
  repetitive or symmetric spaces — a wrong match pulls the filter, the pulled filter
  changes the next match, and each run diverges differently [K26]. So
  `robot_localization` stays a pure odometry filter with `world_frame: odom`, and
  absolute pose is supplied downstream by `slam_toolbox` localisation writing
  `map → odom` against a frozen pose graph [MJ21]. Consequence: the EKF can never be
  corrupted by a bad scan match, and equally can never be corrected by a good one; a
  bad `map → odom` is only visible in Nav2's behaviour and the map.

- **Yaw rate only from the MPU6050.** The board has no magnetometer, so any "absolute"
  yaw it could supply would be an integrated rate with a made-up reference.
  Consequence: there is no heading measurement anywhere in the stack — the only
  absolute heading in the system is the one `slam_toolbox` infers from geometry.

A fifth, smaller decision belongs here because every experiment depends on it: the
robust kernel stays `HuberLoss` [H22]. Wrong loop closures and degeneracy in
featureless areas are the two failure modes a 2D lidar SLAM system has to survive, and a
robust kernel is what stops the first one from dragging the whole trajectory. Nothing in
this section changes between runs except the variable under test, and all configs are
frozen for the duration of a comparison [K26]. A configuration that differs between two
runs measures the configuration.

## 3. Known issues and fixes

Six issues are recorded here because each one produces a failure with no error message
and each has already been diagnosed. The first two are **blocking**: nothing in this
section works until they are fixed.

### 3.1 `slam_toolbox` 2.8.x is a lifecycle node and stays unconfigured (BLOCKING)

**Verified against `slam_toolbox` 2.8.5 on the Pi.**

| | |
| --- | --- |
| Symptom | `mapping.launch.py` runs, the node is listed, and there is no `/map` topic and no `map → odom` transform. No error, no warning. `ros2 lifecycle get /slam_toolbox` returns `unconfigured`. |
| Cause | In 2.8.5 `async_slam_toolbox_node` and `localization_slam_toolbox_node` are lifecycle nodes whose `main()` only spins. Nothing configures or activates them unless a lifecycle manager does, and the reference implementation launches them with a plain `launch_ros.actions.Node` — a `Node` action cannot send lifecycle transitions, so the process spins in `unconfigured` for ever. |
| Fix | Launch with `launch_ros.actions.LifecycleNode`; emit `ChangeState(TRANSITION_CONFIGURE)`; on reaching `inactive`, emit `ChangeState(TRANSITION_ACTIVATE)`. Set `use_lifecycle_manager: false` in the parameters so no manager is expected. |
| Verify | `ros2 lifecycle get /slam_toolbox` → `active [3]`; `ros2 topic list` contains `/map`; `ros2 run tf2_ros tf2_echo map odom` prints a transform; after a short drive `ros2 topic echo /map --once` shows occupied cells. |

The pattern, mirroring `slam_toolbox`'s own `launch/online_async_launch.py` (read the
installed copy at
`$(ros2 pkg prefix slam_toolbox)/share/slam_toolbox/launch/online_async_launch.py` and
copy its imports verbatim — they differ between ROS 2 releases):

```python
slam = LifecycleNode(
    package='slam_toolbox', executable='async_slam_toolbox_node',
    name='slam_toolbox', namespace='', output='screen',
    parameters=[params_file, {'use_sim_time': use_sim_time,
                              'use_lifecycle_manager': False}])

ld.add_action(EmitEvent(event=ChangeState(
    lifecycle_node_matcher=matches_action(slam),
    transition_id=Transition.TRANSITION_CONFIGURE)))
ld.add_action(RegisterEventHandler(OnStateTransition(
    target_lifecycle_node=slam, goal_state='inactive',
    entities=[EmitEvent(event=ChangeState(
        lifecycle_node_matcher=matches_action(slam),
        transition_id=Transition.TRANSITION_ACTIVATE))])))
```

Two details that are easy to get wrong and both fail silently:

- `OnStateTransition` must see the node reach `inactive`: register it with
  `goal_state='inactive'` (upstream also pins `start_state='configuring'` for
  precision). Do not react to the configure *request*: the activate transition is
  rejected while the node is still `configuring`.
- Do **not** include `slam_toolbox`'s `localization_launch.py`. It forwards only
  `slam_params_file` and therefore cannot pass `map_file_name`, so localisation runs
  with no map. `navigation.launch.py` builds the node itself for that reason.

Both launch files must forward `use_sim_time` to the node — bag replay runs on `/clock`
and a node left on wall time stamps every transform in 2026 while the bag plays 2025.

### 3.2 rf2o publishes zero covariance, so the EKF ignores the gyro (BLOCKING)

**Verified at rf2o commit `b38c68e`** (the commit pinned in `deps.repos`).

| | |
| --- | --- |
| Symptom | Heading in `/odometry/filtered` follows rf2o's yaw rate almost exactly and ignores the gyro. A hand rotation with the scan window covered, or any run with sparse scans, shows `odometry/filtered` yaw flat while the robot turns; a three-spin test misses its 5° tolerance for reasons that are not the gyro's fault. |
| Cause | `CLaserOdometry2DNode::publish()` at `b38c68e` fills pose and twist but never assigns covariance — every diagonal element is zero — even though the node computes `cov_odo` internally and simply does not publish it. `robot_localization` (Jazzy, `ekf.cpp`) replaces a zero measurement variance with `1e-9` rather than rejecting it, so rf2o's yaw rate is treated as almost perfect and the IMU's yaw rate (variance `4e-4`) can barely move the estimate. |
| Fix | A relay node between the two — **our design**, since no upstream package exposes rf2o's internal covariance and the pinned commit may not be patched: subscribe `/odom_rf2o`, copy the message, write the configured variances into the twist covariance diagonal for `vx` and `vyaw`, leave every other diagonal at `1e3` so nothing else can ever be fused by accident, publish `/odom_rf2o_cov`; point `ekf.yaml`'s `odom0` at that topic. Do **not** fork or patch rf2o [J16]: the pinned commit is part of the record, and a local patch makes every replay depend on an unversioned tree. |
| Calibrate | A dedicated calibration run compares rf2o's reported speeds against a reference (tape-measured straight push at constant speed; gyro-integrated rotation for `vyaw`) and sets each variance to the residual variance σ². Never calibrate on a run that is also used for evaluation [M26]. |
| Verify | `ros2 topic echo /odom_rf2o --once --field twist.covariance` → all zeros; `ros2 topic echo /odom_rf2o_cov --once --field twist.covariance` → `[vx_var, 1e3, 1e3, 1e3, 1e3, vyaw_var]`. Behaviourally: three hand spins with the scan window covered — the gyro alone must now carry the heading, so `/odometry/filtered` yaw must track the integrated gyro within 5°. |

### 3.3 Frames: the URDF must define `base_footprint`, and the lidar yaw must be re-measured

| | |
| --- | --- |
| Symptom | (a) `robot_state_publisher` publishes nothing below `base_link`, or `tf2` cannot connect `base_footprint` to `laser`, so `slam_toolbox` and Nav2 both refuse to work and every scan is dropped with a transform timeout. (b) The map is mirrored, or rf2o reports *reverse* motion when the robot drives forward, or both. |
| Cause (a) | The current URDF comment claims "`base_footprint` is published by the EKF, not here — this file must only describe `base_link` and below". That mixes up a *transform* with a *link*. The EKF publishes the transform `odom → base_footprint`; it cannot create the `base_footprint` link, and the fixed joint `base_footprint → base_link` is the URDF's job. |
| Cause (b) | The lidar yaw found earlier with a standalone Python script does not carry over. That script read the A1M8 directly and worked in the sensor's raw clockwise angle convention; `rplidar_ros` publishes its own convention (it applies `angle_compensate` and its internal inversion), so a yaw derived from raw angles is wrong by whatever the two conventions differ by — and a 180° error is exactly the case that makes rf2o report reverse motion and folds the map through itself. |
| Fix | Add the `base_footprint` link, the fixed `base_footprint → base_link` joint at `z = wheel_radius`, `laser` and `imu_link` links and joints, and `laser_yaw` as a xacro property. Re-measure `laser_yaw` with the 50 cm box test *in ROS terms*: place a box at 50 cm directly ahead of the robot, view `/scan` in Foxglove **in the `laser` frame**, and set `laser_yaw` so the box's return sits at 0 rad. |
| Verify | `xacro delivery_bot.urdf.xacro > /tmp/robot.urdf && check_urdf /tmp/robot.urdf` exits 0; `ros2 run tf2_ros tf2_echo base_footprint laser` prints the measured xyz and yaw; box test shows the return at 0 ± 2°; driving forward by hand gives positive `twist.twist.linear.x` on `/odom_rf2o` and a map whose walls stay parallel to the taped floor marks. |

The yaw sign is worth stating once: positive `laser_yaw` is a rotation about `+z`
(counter-clockwise seen from above), the same convention as `odom` and `map`. If the
box appears at 0 rad in the `laser` frame but rf2o still reports reverse motion, the
error is not the lidar yaw — check the sign of `/odom_rf2o`'s `vx` against a push.

### 3.4 rf2o's startup race: it looks the lidar transform up once

| | |
| --- | --- |
| Symptom | The whole run's odometry is subtly wrong — often plausible-looking but rotated — and the map shears as soon as the robot turns. Nothing in the log at normal verbosity after the first line. |
| Cause | rf2o resolves `base_footprint → laser` once, on the first scan it receives, and caches it. If the static transform has not arrived yet it logs a `lookupTransform` failure once and then proceeds with an **all-zero rotation** for the rest of the process's life. `base.launch.py` starts rf2o in the same instant as `robot_state_publisher`, so which wins is a race. |
| Fix | Start rf2o behind a `TimerAction(period=2.0)`. That file belongs to a teammate — this section records it as an interface request (§8 item 1) and does not edit it. |
| Verify | In rf2o's own log at startup there is no `lookupTransform` / "Could not find transform" line, and `twist.twist.linear.x` is positive for a forward push on the very first scan after launch. Repeat the launch five times; the check must pass five times, because a race that passes once proves nothing. |

A test for this belongs in the bringup package's launch test (interface request, §8 item 1):
fail the launch test if the node's output contains `lookupTransform`.

### 3.5 Config baseline the branch must carry

These are edits on top of the upstream Jazzy configs, not defaults. Each one is checked
before an experiment because a re-copied config silently reverts it —
`slam_localization.yaml` started life as `mapper_params_localization.yaml`, which
ships `ceres_loss_function: None` and `min_laser_range: 0.0`.

| File | Key | Value | Why | Check |
| --- | --- | --- | --- | --- |
| both SLAM configs | `min_laser_range` | `0.15` | the A1M8's minimum range; anything closer is the robot's own mast and standoffs, which would otherwise be mapped as walls around every pose | `ros2 param get /slam_toolbox min_laser_range` |
| `slam_mapping.yaml` | `enable_interactive_mode` | `false` | RViz-only feature (click to add scan nodes); Foxglove cannot use it and it costs Pi CPU during a mapping run | `ros2 param get /slam_toolbox enable_interactive_mode` |
| both SLAM configs | `ceres_loss_function` | `HuberLoss` | robust kernel: one wrong loop closure otherwise drags the whole trajectory [H22]. Must stay fixed across every experiment | `ros2 param get /slam_toolbox ceres_loss_function` |
| `slam_mapping.yaml` | `map_update_interval` | `5.0` (default), overridden to `2.0` by `explore.launch.py` | 5 s is fine for manual mapping; exploration needs the frontier list and the Foxglove map to refresh faster | `ros2 param get /slam_toolbox map_update_interval` |
| `ekf.yaml` | `odom0` | `/odom_rf2o_cov` | the relay's output, per §3.2. Pointing at `/odom_rf2o` silently reintroduces the zero-covariance bug | `ros2 param get /ekf_filter_node odom0` |

`ceres_loss_function` is the one value that must never vary inside an experiment: a
different kernel changes the objective, so two maps differ for a reason that has
nothing to do with the thing being tested.

### 3.6 Bag replay: never replay `/tf`

| | |
| --- | --- |
| Symptom | The map jumps or spins during replay, the robot's pose teleports to where it was during recording, and `tf2_monitor` shows two authorities for `odom → base_footprint`. |
| Cause | The bag contains the recorded `/tf`, which includes the EKF's `odom → base_footprint` and `slam_toolbox`'s `map → odom`. Replaying it publishes those transforms from `rosbag2` while the live EKF and `slam_toolbox` publish their own — two publishers of one transform, which is the same failure as §1.1. |
| Fix | Replay only the sensor inputs and the static tree. Everything else is recomputed by the live stack. |
| Verify | `ros2 topic list` during replay contains no `/tf` publisher other than the live nodes; `ros2 run tf2_tools tf2_monitor odom base_footprint` lists exactly one authority; the map does not jump when the bag loops. |

```bash
# record (bringup owner): static tree is required, dynamic tf is not
ros2 bag record -s mcap -o ~/bags/2026-10-24_room_drive \
  /scan /imu/data /tf_static

# replay: sensors and statics only
ros2 launch delivery_bot_slam slam_replay.launch.py use_sim_time:=true
ros2 bag play ~/bags/2026-10-24_room_drive --clock \
  --topics /scan /imu/data /tf_static
```

`--clock` publishes `/clock`; every node in the replay must be started with
`use_sim_time:=true` or it will stamp in wall time and every lookup will extrapolate.
Because `tf_static` comes from the bag, a replay uses the URDF geometry that was
current at *record* time — so a URDF change invalidates older bags, and a new bag
must be recorded after §3.3 is fixed.

## 4. Implementation guide, file by file

Each subsection states the contract, the steps in order, the APIs that matter, and one
acceptance test that is pass/fail without interpretation. `delivery_bot_slam` does not
exist yet; it is created alongside this document and nothing in it may re-implement
estimation or planning — it is glue, in line with `AGENTS.md` rule 2.

Package skeleton the rest of this section assumes:

```
delivery_bot_slam/
  package.xml                       ament_python
  setup.py                          entry points, install config/ and launch/
  delivery_bot_slam/
    __init__.py
    odom_covariance_relay.py
    trajectory_recorder.py
  launch/
    explore.launch.py
    slam_replay.launch.py
  config/
    odom_covariance.yaml
    explore.yaml
  test/
    test_imports.py
```

### 4.1 `delivery_bot_slam/odom_covariance_relay.py`

**Build path:** task 4.3 in [slam_build_path.md](slam_build_path.md).

**Contract.** Subscribe `nav_msgs/msg/Odometry` on `/odom_rf2o`; republish a copy on
`/odom_rf2o_cov` with configured twist variances; change nothing else. No filtering, no
smoothing, no timestamp rewriting — the message must be the same message the EKF
would have received, with a different covariance. The node is **our design**, not a
wrapper around an upstream feature: rf2o's internal `cov_odo` never leaves the process
(§3.2), and the point of the relay is to keep the pinned commit untouched [J16].

Steps:

1. Declare parameters: `input_topic` (`/odom_rf2o`), `output_topic`
   (`/odom_rf2o_cov`), `vx_variance` (`1.0e-3  # CALIBRATE`), `vyaw_variance`
   (`4.0e-3  # CALIBRATE`), `unused_variance` (`1.0e3`). Values live in
   `config/odom_covariance.yaml`, not in the node.
2. Create the publisher with the same QoS depth as the subscriber (rf2o publishes with
   the default reliable QoS; a `SensorDataQoS` subscriber will still match, but keep
   both default so a bag replay behaves the same way).
3. On each message: copy it, then write
   `msg.twist.covariance[0] = vx_variance` and
   `msg.twist.covariance[35] = vyaw_variance`; set the remaining twist diagonals
   `[7], [14], [21], [28]` to `unused_variance`. Leave `header` untouched — copying the
   stamp is what keeps the EKF's time ordering intact; restamping would add this
   node's latency to every measurement.
4. Leave the 6×6 pose covariance as received. Nothing fuses it
   (`odom0_config` enables `vx` and `vyaw` only), and a comment in the file must say so
   — if someone later enables `x` or `y`, a zero pose variance becomes the §3.2 bug
   again in a different place.
5. Log once at startup: the two variances and the topic pair, at `INFO`. A calibration
   run must be able to see from the log which numbers were active.
6. `test/test_imports.py`: import the module and assert the node class exists; keep it
   offline (no ROS graph needed) so it runs in CI.

Calibration (owned by this section, executed on the robot): push the robot along a
tape-measured 2 m straight line at constant speed ten times, record `/scan`,
`/imu/data` and `/odom_rf2o`; integrate `vx` and compare with the tape for `vx`'s
residual, and integrate `vyaw` over a measured 360° rotation for `vyaw`'s. Set each
variance to the residual variance. Record the numbers in `results/`, never in this
document as prose.

**Acceptance test.** With `base.launch.py` running:

```bash
ros2 topic echo /odom_rf2o_cov --once --field twist.covariance
# -> [vx_var, 1000, 1000, 1000, 1000, vyaw_var]
ros2 topic hz /odom_rf2o_cov        # ~10 Hz, same as /odom_rf2o
ros2 topic echo /odom_rf2o_cov --once --field header # identical stamp to /odom_rf2o
```

### 4.2 `delivery_bot_slam/trajectory_recorder.py`

**Build path:** task 7.1 in [slam_build_path.md](slam_build_path.md).

**Contract.** Publish two `nav_msgs/msg/Path` trajectories and, optionally, write both
to disk as TUM files for `evo`. It reads transforms; it never publishes one and never
modifies an estimate.

| Item | Value |
| --- | --- |
| `/slam/path` | `header.frame_id: map`, poses from `tf2` `map → base_footprint` |
| `/odom/path` | `header.frame_id: odom`, poses from `/odometry/filtered` (message pose, no TF lookup) |
| Append rule | a new pose is appended only after **2 cm** of translation or **2°** of rotation from the last appended pose |
| `min_translation_m` | `0.02` |
| `min_rotation_deg` | `2.0` |
| `publish_rate_hz` | `1.0  # TUNE` (Foxglove does not need more; the Pi does not need the serialisation cost) |
| `sample_rate_hz` | `20.0  # TUNE` (faster than the EKF, so no pose is missed at 0.15 m/s) |
| `tum_output_dir` | `""` — empty means off; a directory path enables writing |
| `map_frame`, `base_frame` | `map`, `base_footprint` |
| `odom_topic` | `/odometry/filtered` |
| `use_sim_time` | forwarded by both launch files; must be honoured |

Steps:

1. Declare the parameters above; construct a `tf2_ros.Buffer` and
   `tf2_ros.TransformListener` in the constructor.
2. Timer at `sample_rate_hz`: for the SLAM path, call
   `buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())` (latest
   available; do not use a fixed stamp — the two clocks never agree exactly).
   Catch `tf2_ros.TransformException`, increment a skipped counter, log at most once
   per second, and return without appending. Before `map → odom` exists this is the
   normal state, not an error: the recorder must come up before `slam_toolbox` is
   active and must not spam the log while it waits.
3. Distance test against the *last appended* pose, not the previous sample: sum the
   increments or compare directly to the last appended transform. Comparing to the
   previous sample at 20 Hz would append every sample, because 0.15 m/s moves 7.5 mm
   per tick — 2 cm is crossed only every third tick, so the naive version inflates the
   file by 3×.
4. Rotation test: yaw difference wrapped to (−π, π], compared in radians against
   `min_rotation_deg × π/180`. Same "from the last appended pose" rule.
5. Build a `PoseStamped` (copy stamp and frame from the transform) and append to the
   relevant `Path`. Publish each `Path` on its own publisher at `publish_rate_hz`,
   with `header.stamp` set to now. Paths grow without bound; that is acceptable here
   (a 50 m mapping run at 2 cm is 2500 poses) but the node must not republish a copy at
   `sample_rate_hz` for that reason.
6. On shutdown (SIGINT handler and `destroy_node`), if `tum_output_dir` is non-empty:
   `os.makedirs(..., exist_ok=True)`, then write `slam_<yyyymmdd-HHMMSS>.tum` and
   `odom_<yyyymmdd-HHMMSS>.tum`, one line per pose, space-separated, eight columns,
   no header:

   ```
   timestamp x y z qx qy qz qw
   ```

   The timestamp is `header.stamp` in seconds (`sec + nanosec × 1e-9`) — under
   `use_sim_time` that is bag time, which is what `evo` needs to align a replay against
   the run it came from. Writing on shutdown, not on every append, keeps the file off
   the SD card's critical path during a mapping run.
7. Keep the two trails independent: if `map → base_footprint` never becomes available,
   `/odom/path` must still be written. An evaluation run with no SLAM is a valid
   datapoint (§7).

**Acceptance test.**

```bash
ros2 launch delivery_bot_slam slam_replay.launch.py use_sim_time:=true \
  tum_output_dir:=$HOME/results/replay-01
ros2 bag play ~/bags/2026-10-24_room_drive --clock --topics /scan /imu/data /tf_static
ros2 topic hz /slam/path            # ~1 Hz once map->odom exists
ros2 topic echo /slam/path --once --field poses  # length grows over the run
# after Ctrl+C on the launch:
ls ~/results/replay-01/*.tum
evo_traj tum ~/results/replay-01/slam_*.tum --ref ~/results/replay-01/odom_*.tum -p
```

Pass: both files exist, both have a strictly increasing first column, and `evo_traj`
plots two trajectories that start together and separate slowly rather than diverging
by metres in the first second (a metre-scale immediate split means a frame or a yaw
sign is wrong, not that the filter is mistuned).

### 4.3 `delivery_bot_slam/launch/explore.launch.py`

**Build path:** task 8.3 in [slam_build_path.md](slam_build_path.md).

**Contract.** Bring up autonomous mapping: the mapping stack, Nav2 for motion, and
`explore_lite` as the goal source. Exploration is the only thing that uses this file;
delivery runs use `navigation.launch.py`.

Steps:

1. Declare `use_sim_time` (false), `dry_run` (**true**), `autostart` (true),
   `map_update_interval` (`2.0`), `slam_params_file` (bringup's
   `slam_mapping.yaml`), `explore_params_file` (`config/explore.yaml`),
   `params_file` (bringup's `nav2_params.yaml`).
2. `IncludeLaunchDescription` of `base.launch.py`, forwarding `use_sim_time` and
   `dry_run`. Do not include `mapping.launch.py`: this file needs its own
   `slam_toolbox` node so the interval override is visible where it is set, and
   including the mapping launch would either duplicate the node or hide the override
   in another file.
3. Create the `LifecycleNode` as in §3.1, `executable='async_slam_toolbox_node'`,
   `name='slam_toolbox'`, parameters `[slam_params_file, {'use_sim_time': ...,
   'use_lifecycle_manager': False, 'map_update_interval': map_update_interval}]`.
   The faster interval is the only difference from manual mapping; overriding it here
   rather than in the YAML keeps the manual-mapping behaviour unchanged (§3.5).
4. `IncludeLaunchDescription` of `nav2_bringup/launch/navigation_launch.py` with
   `params_file`, `use_sim_time`, `autostart`. Nav2's `navigation_launch.py` starts no
   map server and no AMCL, which is what mapping mode needs — the global costmap's
   `StaticLayer` takes `/map` straight from `slam_toolbox`.
5. Add `collision_monitor` with `config/nav2_params.yaml`'s `collision_monitor` block.
   `navigation_launch.py` does not start it; without it the 0.20 m stop wedge is inert
   while the robot drives itself, which is the one situation it exists for. Remaps:
   in `cmd_vel_smoothed`, out `cmd_vel`.
6. Add the `explore_lite` node: `package='explore_lite'`, `executable='explore'`,
   `name='explore_node'` (the name must match the `explore_node:` key in
   `config/explore.yaml`), parameters from `explore_params_file` [EXP]. Key values:
   `robot_base_frame: base_footprint`, `costmap_topic: /global_costmap/costmap`,
   `costmap_updates_topic: /global_costmap/costmap_updates`, `return_to_init: true`,
   `planner_frequency: 0.3  # TUNE`, `progress_timeout: 30.0`,
   `potential_scale: 3.0`, `orientation_scale: 0.0`, `gain_scale: 1.0`,
   `transform_tolerance: 0.3`, `min_frontier_size: 0.3  # TUNE`, and
   `visualize: true` so `/explore/frontiers` is visible in Foxglove.
7. `explore_lite` is pinned in `deps.repos` (`m-explore-ros2`, commit `326cf8a`) and
   declared in `delivery_bot_slam/package.xml`, so a clean `vcs import` plus
   `colcon build` produces it. The vendored repo also ships `multirobot_map_merge`,
   which this robot never runs; the build skips that package.

`dry_run` defaults true, which means exploration is exercised with the wheels doing
nothing: Nav2 accepts goals, publishes `/cmd_vel`, `motor_node` logs duties and never
touches GPIO, and `explore_lite` will retry the same frontier until `progress_timeout`
fires. That is a wiring rehearsal, not a mapping run; say so in the notes when it is
done.

**Acceptance test (dry).** `ros2 action list | grep navigate_to_pose` lists the action;
`ros2 topic echo /explore/frontiers --once` shows at least one frontier once the map
has unknown space; Nav2's log shows an accepted goal; no `motor_node` GPIO write
appears in the log. **Acceptance test (floor, wheels down, watched):** the robot leaves
the home mark unaided, the map grows, and after no frontier remains the robot drives
back to the start pose within 0.15 m.

### 4.4 `delivery_bot_slam/launch/slam_replay.launch.py`

**Build path:** task 5.5 in [slam_build_path.md](slam_build_path.md).

**Contract.** Re-run SLAM and odometry on a recorded bag, with no hardware. It starts
every node that consumes the bag and *nothing that publishes to it*, and it must run
entirely on bag time.

Steps:

1. Declare `use_sim_time` (**true** — this launch is for replay), `ekf_params_file`
   (`delivery_bot_bringup/config/ekf.yaml`), `slam_params_file` (bringup's
   `slam_mapping.yaml`), `odom_covariance_params_file`
   (`config/odom_covariance.yaml`), `tum_output_dir` (empty), `slam_mode`
   (`mapping`|`localization`), `map` (empty; required when `slam_mode:=localization`).
2. Start, all with `use_sim_time`: `odom_covariance_relay`, `ekf_filter_node`,
   `trajectory_recorder`, `slam_toolbox` (as a `LifecycleNode`, §3.1),
   `foxglove_bridge`. Start no lidar driver, no IMU node, no motors, and — the part
   that is easy to get wrong — **no `robot_state_publisher`**: the static tree arrives
   from `/tf_static` in the bag, and a live `robot_state_publisher` would be a second
   publisher of `base_footprint → base_link` and `base_link → laser`.
3. Do not start `slam_toolbox`'s lifecycle sequence until `/clock` has arrived, or the
   configure step will complain about a clock that does not exist yet. A
   `TimerAction(period=3.0)` in front of the configure event is the crude but reliable
   version; the alternative is a small node that waits on `/clock` and is not worth
   writing.
4. In `localization` mode pass `map_file_name` from the `map` argument; refuse to start
   if `slam_mode` is `localization` and `map` is empty (a `LaunchConfiguration`
   comparison in an `OpaqueFunction`, or an explicit `PythonExpression`).
5. Tell the operator which bag topics are legal, in the launch file's docstring:
   `/scan`, `/imu/data`, `/tf_static`, nothing else (§3.6).

The `ekf_params_file` argument is the IMU ablation hook (§7): point it at a variant
with `imu0_config` all false and the same bag re-runs odometry without the gyro.

**Acceptance test.** Start the launch, then play one bag:

```bash
# ekf_rf2o_only.yaml is created in the evaluation phase (§7); without the argument
# the run uses bringup's ekf.yaml and is a plain replay.
ros2 launch delivery_bot_slam slam_replay.launch.py \
  tum_output_dir:=$HOME/results/ablation-rf2o-only \
  ekf_params_file:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_slam/config/ekf_rf2o_only.yaml
ros2 bag play ~/bags/2026-10-24_room_drive --clock --topics /scan /imu/data /tf_static
```

Pass: `/odometry/filtered` follows the bag at 30 Hz; `/map` grows exactly as it did
live; no transform in the system carries a 2026 wall-clock stamp; two consecutive runs
of the same bag produce `.tum` files whose paths agree to within 1 cm over the first
metre (anything larger means a node is still using wall time or a race is seeding the
run differently).

### 4.5 `delivery_bot_bringup/launch/mapping.launch.py`

**Build path:** task 5.3 in [slam_build_path.md](slam_build_path.md).

**Contract.** Manual mapping: the base stack plus `slam_toolbox` in mapping mode. The
file's docstring already states the save procedure; the implementation only has to put
the node up and make the lifecycle work.

Steps:

1. Declare `use_sim_time` (false), `dry_run` (true), `slam_params_file`
   (`config/slam_mapping.yaml`), `map_update_interval` (`5.0`), `autostart` (true).
2. `IncludeLaunchDescription` of `base.launch.py` with `use_sim_time` and `dry_run`
   forwarded. Do not duplicate any node that file starts — in particular do not start
   rf2o or the EKF here, or §1.1's one-publisher rule breaks in the one place nobody
   looks.
3. Create the `LifecycleNode` exactly as §3.1, `executable='async_slam_toolbox_node'`,
   `name='slam_toolbox'`, parameters `[slam_params_file, {'use_sim_time': ...,
   'use_lifecycle_manager': False, 'map_update_interval': ...}]`.
4. Add the configure `EmitEvent` and the activate `RegisterEventHandler` from §3.1,
   both gated on `IfCondition(autostart)` so a run can be started unconfigured
   deliberately (needed to test the lifecycle logic itself).
5. Order the actions: `base.launch.py` include first, lifecycle node second, configure
   event last. The configure event may fire the instant it is processed — before a
   shared `/clock` is published under replay — which is why §4.4 inserts a timer
   rather than relying on ordering.
6. Do not add a `map_saver` node or a static `map_server`: saving is a deliberate,
   documented command (`map_saver_cli` plus `serialize_map`), and an automatic saver
   makes an accidental save look like a result.

**Acceptance test.**

```bash
ros2 launch delivery_bot_bringup mapping.launch.py dry_run:=true
ros2 lifecycle get /slam_toolbox                       # active [3]
ros2 run tf2_ros tf2_echo map base_footprint           # prints, does not hang
ros2 topic hz /map                                     # ~0.2 Hz with the 5.0 s interval
# push the robot by hand for 20 s, then:
ros2 topic echo /map --once                            # occupied cells trace the walls
ros2 run nav2_map_server map_saver_cli -f /tmp/smoke   # writes /tmp/smoke.pgm + .yaml
```

Pass: the PGM has a recognisable room outline and the walls are single lines, not
double lines or fans of lines. A double wall means the odometry and the scan match
disagree and the map is being written from both — check §1.1 before touching
`correlation_search_space_dimension`.

### 4.6 `delivery_bot_bringup/launch/navigation.launch.py`

**Build path:** task 6.2 in [slam_build_path.md](slam_build_path.md).

**Contract.** Delivery mode: base stack, `slam_toolbox` in localisation mode with the
saved posegraph, Nav2, and the collision monitor between controller and motors. No
AMCL, no `map_server` — the docstring says why, and the reason is that `slam_toolbox`
already supplies both `/map` and `map → odom`, so AMCL would be a second, disagreeing
position source.

Steps:

1. Declare `map` (required, no default), `use_sim_time` (false), `dry_run` (true),
   `autostart` (true), `slam_params_file` (`config/slam_localization.yaml`),
   `params_file` (`config/nav2_params.yaml`).
2. Include `base.launch.py` (same rule as §4.5 step 2).
3. Create the `LifecycleNode` with `executable='localization_slam_toolbox_node'`,
   parameters `[slam_params_file, {'use_sim_time': ..., 'use_lifecycle_manager':
   False, 'map_file_name': map, 'map_start_pose': [0,0,0]?}]` — omit
   `map_start_pose` unless the map was *saved* from a different origin; the default is
   "trust the stored pose", which is correct here because mapping started at the home
   mark.
4. Configure/activate as §3.1. Do not include `slam_toolbox`'s
   `localization_launch.py` (§3.1).
5. Include `nav2_bringup/launch/navigation_launch.py` with `params_file`,
   `use_sim_time`, `autostart`. Confirm by reading that file that it starts neither
   `amcl` nor `map_server`; if a future Jazzy point release changes that, the include
   becomes hand-written nodes.
6. Add `collision_monitor` (§4.3 step 4) — same reason: it is configured in
   `nav2_params.yaml` and would otherwise never run in the mode that drives.
7. Pass `map` through as a full path without extension; `slam_toolbox` appends
   `.posegraph` and `.data`. `ros2 launch ... map:=$HOME/ros2_ws/src/delivery_bot/delivery_bot_bringup/maps/room`
   is the canonical form.
8. `map` is required and must not silently default: launching with a stale or empty
   map is the failure mode that looks like a localisation bug for an hour.

**Acceptance test.**

```bash
MAP=$HOME/ros2_ws/src/delivery_bot/delivery_bot_bringup/maps/room
ros2 launch delivery_bot_bringup navigation.launch.py map:=$MAP dry_run:=true
ros2 lifecycle get /slam_toolbox                       # active [3]
ros2 node list | grep -E 'amcl|map_server'             # no output
ros2 topic hz /map                                     # map loaded once, then idle
ros2 run tf2_ros tf2_echo map odom                     # frozen map anchored
ros2 action list | grep navigate_to_pose
```

Then, with the robot on the floor and the map loaded, teleop it 1 m and back: the pose
in Foxglove must move with it and return to within 0.15 m of where it started. A pose
that slides relative to the walls while the robot is stationary means `map → odom` is
being fought over by two publishers.

### 4.7 `delivery_bot_description/urdf/delivery_bot.urdf.xacro`

**Build path:** task 2.2 in [slam_build_path.md](slam_build_path.md).

**Contract.** The frame tree: `base_footprint` on the floor between the wheels,
`base_link` one wheel radius above it, `laser` and `imu_link` rigid to the body. The
file describes links and fixed joints; it publishes no transform of its own.

The tree the rest of the stack assumes:

```
base_footprint           on the floor, between the wheels, no visual
  └── base_link          body origin, z = wheel_radius above the floor
        ├── laser        RPLidar A1M8, scan plane height + yaw from the box test
        └── imu_link     MPU6050, rigid to the body
```

Steps:

1. Add xacro properties: `wheel_base`, `wheel_radius`, `robot_radius`,
   `laser_x`, `laser_y`, `laser_z` (each `# MEASURE`, metres), `laser_yaw`
   (`0.0  # MEASURE`, radians), `imu_x`, `imu_y`, `imu_z` (each `# MEASURE`). Keep
   every placeholder marked until it has been
   measured with a tape; `AGENTS.md` rule 4 applies to the URDF as much as to a result.
2. Add `link name="base_footprint"` with no visual and no inertial, then a fixed joint
   `base_footprint → base_link` with `origin xyz="0 0 ${wheel_radius}"`. This is the
   link the current comment wrongly says is unnecessary (§3.3).
3. Add `link name="base_link"` with the body visual; add fixed joints
   `base_link → laser` (origin `${laser_x} ${laser_y} ${laser_z}`,
   `rpy="0 0 ${laser_yaw}"`) and `base_link → imu_link` (origin
   `${imu_x} ${imu_y} ${imu_z}`, `rpy="0 0 0"`).
4. Replace the comment block: the EKF publishes the *transform* `odom →
   base_footprint`; the URDF owns the *link* and the fixed joint to `base_link`. Keep
   the sentence, drop the wrong reason.
5. Do not add wheel joint states. The wheels stay fixed until there are encoders or
   real joint control, and a fake continuous joint with a `joint_state_publisher` would
   put a second opinion about the base into the tree.
6. Keep the `xmlns:xacro` attribute; a plain URDF will not expand under `xacro`.

Measuring `laser_yaw` (this section, on the robot, ~10 minutes): place a 50 cm box
directly ahead of the robot's intended forward axis, launch `base.launch.py`, view
`/scan` in Foxglove with the display's fixed frame set to `laser`, and read the angle
of the box's edge. Set `laser_yaw` to minus that angle and rebuild. Repeat until the
box sits at 0 rad ± 2°. The **only** valid measurement is the one taken from the
published `/scan` in the `laser` frame — a value derived from raw sensor angles is what
produced the current 180° uncertainty (§3.3).

**Acceptance test.**

```bash
xacro delivery_bot_description/urdf/delivery_bot.urdf.xacro > /tmp/robot.urdf
check_urdf /tmp/robot.urdf                       # exits 0, prints the tree
ros2 run tf2_ros tf2_echo base_footprint laser   # translation + yaw as measured
ros2 run tf2_ros tf2_echo base_link imu_link
ros2 run tf2_tools view_frames                   # one tree, no orphans
```

Pass: `check_urdf` shows `base_footprint → base_link → {laser, imu_link}`; the box test
shows 0 rad; `tf2_echo base_footprint laser` prints the values in the xacro, not zeros.

## 5. Foxglove

Panels, layouts and the bridge recipe live in
[`docs/foxglove/README.md`](foxglove/README.md); that page is the Foxglove section's and
this one does not repeat it. For SLAM work it needs three things: `/map` drawn under
`/scan` in the `map` fixed frame, `/slam/path` and `/odom/path` as two coloured lines
so drift is visible at a glance, and the lifecycle state of `/slam_toolbox` reachable
without a terminal. The box test in §4.7 is done entirely in Foxglove, in the `laser`
frame, because the Pi is headless and a printed angle is not evidence.

## 6. Autonomous mapping

Manual mapping needs a person driving for ten minutes and produces whatever the person
happened to look at. Frontier exploration replaces the person with an algorithm that
has no aesthetic judgement but does have a stopping rule.

**How it works.** A *frontier* is a free cell adjacent to an unknown cell — the
boundary between what the robot has seen and what it has not [EXP]. `explore_lite`
reads the global costmap (or `/map`), finds frontier cells, clusters them into
candidate goals, scores each cluster by the unknown area behind it divided by the path
cost to reach it (`gain_scale`, `potential_scale`, `orientation_scale`), and sends the
best centroid to Nav2 as a `NavigateToPose` goal [EXP]. When the goal succeeds or
times out (`progress_timeout`), it re-reads the map and picks again. When no cluster
larger than `min_frontier_size` remains, exploration is finished; with
`return_to_init: true` the last goal is the start pose, so the robot ends where the
map's origin is and the return-to-start error is measured without a second command
[EXP].

**Why Nav2 has to be reliable first.** `explore_lite` has exactly one actuator: the
`NavigateToPose` action. If the planner cannot produce a path through unknown-but-free
cells, or the controller oscillates at a doorway, exploration does not degrade
gracefully — it burns `progress_timeout` on the same frontier for ever, or worse,
marks a region as explored because a goal failed there. The prerequisites are the ones
in `docs/plan.md` phase 6: five goals in a row within 15 cm, no collisions, with a
human driving the goals. Only then does an algorithm get to choose them.

**Safety rules.** These are not advisory.

| Rule | Why |
| --- | --- |
| `dry_run` defaults to `true` in `explore.launch.py` | the first run of a new launch file must not move the robot; a dry run proves the graph, the goals and the costmaps without wheels |
| wheels on the floor, robot watched, hand on the motor switch | the robot starts driving as soon as the first frontier exists — there is no "arm" step and no confirmation prompt |
| pause by publishing `false` on `/explore/resume` (`std_msgs/Bool`) | stops goal generation immediately; Nav2 finishes or cancels the current goal, so treat it as "stop choosing", not "stop now". Confirm the topic type with `ros2 topic info /explore/resume` on the installed build before relying on it |
| `v_max` stays 0.15 m/s | RPP, the velocity smoother, the Collision Monitor wedge and the 0.5 s watchdog are all sized for it |
| Collision Monitor running (§4.3 step 4) | the only thing between a bad goal and a wall that does not depend on the planner being right |
| one person, one job: watch the robot, not the screen | at 0.15 m/s a mistake is slow but a doorway is narrow |

**Comparing autonomous with manual mapping.** Both runs start at the home mark with the
same map origin, the same configs and the same `slam_toolbox` version, and differ only
in who chooses the path. Record for each:

| Metric | How |
| --- | --- |
| wall-clock time | `date` before launch and after the map is saved; report both runs |
| coverage | occupied + free cells inside the tape-measured floor outline ÷ tape-measured floor area; one script over the PGM, so it is computed the same way twice |
| map dimensions | extent of occupied cells along x and y in the saved map vs the tape; report the difference in metres, not a percentage |
| return-to-start error | `ros2 run tf2_ros tf2_echo map base_footprint` at the end, distance from the map origin (the robot started there) |
| map IoU | occupied cells of map A ∩ map B ÷ union, at 5 cm, on the two saved PGMs |

A single pair of runs is an anecdote; the comparison is only worth reporting once the
repeatability runs in §7 exist. Coverage and map IoU are the ground-truth-free map
metrics of Filatov et al. [F17]; trajectory error is deliberately absent here and
belongs to §7, where `evo` compares runs [EVO].

## 7. Evaluation plan (later)

**Not now.** Nothing in this section is evaluated until P5 mapping produces a map whose
walls are straight, because every metric below measures a difference between two maps
and two maps of a broken pipeline differ for the wrong reason. The order is: fix §3.1
and §3.2, resolve OI-4, make one manual map that looks like the room, and only then
start measuring. Everything that is not the independent variable is frozen for the
whole set — same configs, same `slam_toolbox` version, same room layout [K26].

**Ground truth without a camera.** There is no camera and no motion-capture rig, so
ground truth comes from the floor. Tape four or more checkpoints (the room corners plus
the home mark), measure their coordinates from a chosen origin with a tape, and drive
the robot to each by teleop. At each checkpoint record `map → base_footprint` from TF.
Fit a 2D rigid transform (rotation + translation, no scale) from map coordinates to
tape coordinates by least squares over the checkpoints, then report the residual RMS —
with sparse checkpoints this *is* the ATE, restricted to the places where truth is
known. Return-to-start error (the pose after `return_to_init`) is reported separately
because it is the one number that needs no checkpoints. Alongside the checkpoints,
report the map-quality metrics that need no ground truth at all — occupied-cell
proportion, corner count and enclosed areas — because they show whether the room came
out complete and rectangular even where no tape mark exists [F17]. `evo` supplies the
trajectory side — APE against a run chosen as reference, RPE within a run — and with
these `.tum` files it is a two-command check, not an analysis [EVO].

**Repeatability, ~5 physical runs** [K26]. Map the same room five times from the same
start, same config. Report pairwise ATE between runs after aligning their origins, and
pairwise map IoU — the two repeatability metrics Kudriashov et al. use to separate a
system that is occasionally good from one that is reliably good [K26]. With five runs,
report median and range, not mean and standard deviation — five samples do not support
a standard deviation. A pipeline whose pairwise ATE spreads over decimetres is not
repeatable enough for a delivery robot, whatever its best run looks like.

**IMU ablation: rf2o alone vs rf2o + gyro** [M26]. The same bag is run twice through
`slam_replay.launch.py`, once with `ekf.yaml` and once with a variant
(`ekf_rf2o_only.yaml`, `imu0_config` all false), and each is measured **before** SLAM
(start-to-end drift of `/odometry/filtered` over a fixed route) and **after** SLAM
(checkpoint residual) [M26]. The two-by-two is the point: SLAM can hide a gyro that is
doing nothing, so an after-SLAM comparison alone would report that the gyro is
unnecessary when what it actually does is make the odometry good enough for scan
matching to succeed. Covariances for both variants come from calibration data collected
separately from these evaluation runs [M26].

**Cost on the Pi.** A mapping run must leave the Pi responsive; report, per run, the
CPU and RSS of `slam_toolbox`, rf2o and the EKF, plus SoC temperature. Use
`top -b -n 1 -p $(pgrep -d, -f 'slam_toolbox|rf2o|ekf_filter')` for a snapshot and
`free -m` for the whole machine, sampled once a minute into the run log;
`/sys/class/thermal/thermal_zone0/temp` is the temperature because `vcgencmd` is not
the default tool on Ubuntu here.

| Experiment | Independent variable | Metric | Command |
| --- | --- | --- | --- |
| Checkpoint accuracy | none (baseline map) | residual RMS at ≥4 tape-measured checkpoints | teleop to each, `ros2 run tf2_ros tf2_echo map base_footprint` |
| Repeatability | run number (n=5) | pairwise ATE, pairwise map IoU | `evo_ape tum runA.tum runB.tum -a`; IoU script on saved PGMs |
| Manual vs autonomous | goal source | time, coverage, dimensions, return error, IoU | §6 table; `explore.launch.py` vs `mapping.launch.py` |
| IMU ablation | `imu0_config` (on/off) | pre-SLAM drift and post-SLAM checkpoint residual | `slam_replay.launch.py ekf_params_file:=…` twice, same bag |
| Pi load | mapping vs localisation vs replay | CPU %, RSS, °C | `top`, `free -m`, thermal zone file |

**Optional later extension: removing people from scans.** A person standing in the room
is a wall that moves, and a person who stood still during mapping leaves a permanent
arc in the occupancy grid. Tracking people and removing their returns from the scan
before it reaches SLAM is the documented extension, and it is what would make a mapped
room usable while someone is in it [Y21]. It changes what "the scan" means, so it
belongs to a later version with its own evaluation, not to this section.

**Optional later extension: gyro-based scan deskewing.** At 5–7 Hz a scan takes
140–200 ms; at the 1.0 rad/s angular cap the robot turns 8–11° *during one scan*
(arithmetic from the two measured rates, not a measurement). Nothing corrects for it
today, and at 0.15 m/s the translation component is small enough to ignore, but a
turn-in-place during mapping smears the walls. A later version could rotate each beam
by the gyro-integrated angle since scan start before handing the scan to
`slam_toolbox` — which would be a new node in `delivery_bot_slam`, and a change to what
"the scan" means in every experiment, so it is not part of this section's scope.
Correction that uses range measurements alone is the alternative when no gyro is
trusted for the interval, and it is the approach worth reading before writing the node
[S23].

## 8. Interface requests to teammates

Each is a change in a file this section does not own. None is optional for the
acceptance tests above.

1. **`delivery_bot_bringup/launch/base.launch.py` (bringup owner): start rf2o behind a
   2 s `TimerAction`.** Wrap the `rf2o_laser_odometry` node in
   `TimerAction(period=2.0, actions=[rf2o_node])` so `robot_state_publisher` has
   published the static tree before rf2o's first scan. Add a launch test that fails if
   rf2o's output contains `lookupTransform`; run the launch five times, since the
   failure is a race (§3.4).

2. **Nav2 (navigation owner): be reliable before `explore.launch.py` is used.**
   `explore_lite`'s only actuator is `NavigateToPose`, so exploration inherits every
   Nav2 fault and expresses it as "the frontier could not be reached". The gate is
   `docs/plan.md` phase 6: five consecutive goals within 15 cm, no collisions, with a
   human choosing the goals. Also confirm `collision_monitor` and `velocity_smoother`
   are actually in the chain from controller to `/cmd_vel` — `navigation_launch.py`
   does not start the monitor, so someone has to.

3. **`delivery_bot_drivers` (drivers owner): confirm the IMU keeps a non-zero yaw-rate
   variance.** `drivers.yaml` already sets `gyro_var: 0.0004` and the `imu_node`
   contract writes it into `angular_velocity_covariance[8]`, with
   `orientation_covariance[0] = -1`. §3.2's fix only helps if the implemented node
   actually does that: `robot_localization` replaces a zero variance with `1e-9`, so
   an all-zero IMU covariance would take over the filter and the relay would have made
   things worse. Check with
   `ros2 topic echo /imu/data --once --field angular_velocity_covariance`.

`explore_lite` itself is pinned in `deps.repos` by this branch (commit `326cf8a`, with
`multirobot_map_merge` skipped in the build), so the bringup owner has nothing to add
for exploration.

## 9. Open items and MEASURE list

**Blocking open items**, in order: §3.1 (lifecycle) and §3.2 (covariance relay) — both
are code, both are in this section, and nothing below can be measured until they are
done. OI-4 (33–35 % echo rate) is not this section's to fix but gates it: a sparse scan
degrades both scan matching and rf2o, and a map built from one is not a baseline for
anything.

| Value | Where set | How measured | Owner |
| --- | --- | --- | --- |
| `laser_x`, `laser_y`, `laser_z` | URDF xacro properties | tape measure, lidar centre relative to `base_link` origin; z is the scan plane height, which must also clear the robot's own standoffs (otherwise `min_laser_range: 0.15` is doing geometry's job) | URDF / SLAM section |
| `laser_yaw` | URDF xacro property | 50 cm box test, read from `/scan` in Foxglove in the `laser` frame, box at 0 rad ± 2° (§4.7) | URDF / SLAM section |
| `imu_x`, `imu_y`, `imu_z` | URDF xacro properties | tape measure, MPU6050 centre relative to `base_link`; the yaw offset is not a parameter — the board must be mounted square to the body | URDF / drivers owners |
| `wheel_radius` (sets `base_footprint → base_link` z) | URDF xacro property | tape measure, loaded tyre radius, not the nominal 32.5 mm | URDF owner |
| `vx_variance` | `delivery_bot_slam/config/odom_covariance.yaml` | residual variance of rf2o `vx` against a tape-measured 2 m straight push, ten repetitions (§4.1) | SLAM section |
| `vyaw_variance` | same file | residual variance of rf2o `vyaw` against a gyro-integrated measured 360° rotation | SLAM section |
| `unused_variance` | same file | not measured — fixed at `1e3` so nothing else can be fused; a deliberate constant, not a placeholder | SLAM section |
| `min_translation_m`, `min_rotation_deg` | `trajectory_recorder` parameters | not measured — 2 cm / 2° is the resolution at which a 5 cm map cell changes; revisit only if a `.tum` file is too large for `evo` | SLAM section |
| `publish_rate_hz`, `sample_rate_hz` (recorder) | same | tuned once against CPU load; `# TUNE` | SLAM section |
| `map_update_interval` (exploration) | `explore.launch.py` argument, `2.0` | tuned: fast enough that frontier selection is not stale, slow enough that the Pi keeps up; compare CPU at 2.0 vs 5.0 | SLAM section |
| `planner_frequency`, `progress_timeout` | `delivery_bot_slam/config/explore.yaml` | `# TUNE` from the first floor run: timeouts long enough that a doorway is not abandoned, short enough that a stuck goal does not end the run | SLAM section |
| `potential_scale`, `orientation_scale`, `gain_scale` | same | `# TUNE`; defaults first, one change at a time, recorded per run | SLAM section |
| `min_frontier_size` | same | `# TUNE`; must be larger than the noise in the map's unknown/free boundary at 5 cm | SLAM section |
| map dimensions (room length, width) | `results/` and the report, not a config | tape measure along the longest occupied extent of the saved map, compared with the tape on the floor | SLAM section |
| coverage denominator (floor area inside the taped outline) | `results/` | tape measure; needed before any coverage percentage means anything | SLAM section |
| checkpoint coordinates | `results/` | tape measure from a chosen origin, ≥4 marks (§7) | SLAM section |
| return-to-start error | `results/` | distance from the map origin after `return_to_init`, one number per run | SLAM section |
| Pi CPU / RSS / temperature per mode | `results/` | `top`, `free -m`, thermal zone, sampled once a minute during a run (§7) | SLAM section |

Two markers, used consistently: `# MEASURE` means a tape or a box test on the robot
replaces it, `# CALIBRATE` means a dedicated calibration run fits it, `# TUNE` means a
value chosen by comparing runs. None of the three may appear in a results table as a
number without the run that produced it beside it.

## References

Cited inline by key, directly after the claim each one supports.

| Key | Reference | Link | What we take from it |
| --- | --- | --- | --- |
| [R25] | Ran, Xu, Tan & Luo, "A Review of 2D Lidar SLAM Research", *Remote Sensing* 17, 1214 (2025) | https://doi.org/10.3390/rs17071214 | The four SLAM categories; why graph-based SLAM, not a particle filter, for a robot without wheel encoders |
| [K26] | Kudriashov, Koszyk, Hyla & Ambroziński, "A Real-World Benchmark of Monte Carlo-Assisted EKF Odometry for Online Pose Estimation in 2D LiDAR SLAM", *Sensors* 26, 4264 (2026) | https://doi.org/10.3390/s26134264 | Precedent for rf2o + IMU -> EKF -> slam_toolbox without encoders on Jazzy; reason for no AMCL feedback; repeatability metrics (pairwise ATE, map IoU) and the fixed-parameters rule |
| [M26] | Merrick & Nandikolla, "Evaluating the Impact of Extended Kalman Filter Odometry on the Performance of 2D LiDAR SLAM Algorithms", *Sensors* 26, 5468 (2026) | https://doi.org/10.3390/s26175468 | IMU ablation design (odometry measured before and after SLAM); calibrating covariances on data separate from the evaluation |
| [J16] | Jaimez, Monroy & Gonzalez-Jimenez, "Planar Odometry from a Radial Laser Scanner. A Range Flow-based Approach" (rf2o), ICRA 2016 | https://doi.org/10.1109/ICRA.2016.7487647 | The lidar odometry method that replaces wheel encoders |
| [MJ21] | Macenski & Jambrecic, "SLAM Toolbox: SLAM for the dynamic world", *Journal of Open Source Software* 6(61), 2783 (2021) | https://doi.org/10.21105/joss.02783 | The SLAM package: pose-graph mapping, localisation mode, serialised maps |
| [H22] | Huang, Huang, Zeng & Huang, "A Robust 2D Lidar SLAM Method in Complex Environment", *Photonic Sensors* 12(4), 220416 (2022) | https://doi.org/10.1007/s13320-022-0657-6 | Wrong loop closures as a failure mode; degeneracy in featureless areas |
| [Y21] | Ye et al., "Mapping While Following: 2D LiDAR SLAM in Indoor Dynamic Environments with a Person Tracker", IEEE ROBIO 2021 | https://doi.org/10.1109/ROBIO54168.2021.9739394 | Later extension: removing people from scans; map comparison |
| [S23] | Salem et al., "Enhancing LiDAR Performance: Robust De-skewing Exclusively Relying on Range Measurements" (2023) | https://arxiv.org/abs/2303.07312 | Later extension: correcting scan distortion on slow lidars like the RPLidar A1 |
| [F17] | Filatov, Filatov & Krinkin, "2D SLAM Quality Evaluation Methods" (2017) | https://arxiv.org/abs/1708.02354 | Map quality metrics that need no ground truth (occupied-cell proportion, corners, enclosed areas) |
| [EXP] | `explore_lite` (m-explore-ros2) | https://github.com/robo-friends/m-explore-ros2 | Frontier-based autonomous mapping |
| [EVO] | Grupp, `evo`: evaluation of odometry and SLAM | https://github.com/MichaelGrupp/evo | Trajectory error tools (APE/RPE) for the evaluation phase |

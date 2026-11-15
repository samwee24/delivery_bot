# ROS 2 Jazzy MPC-style local controllers for Nav2 on a Raspberry Pi 4 (CPU only)

Scope: options to replace or sit beside `nav2_regulated_pure_pursuit_controller` (RPP, 10 Hz) and the `collision_monitor` stop polygon, for a diff-drive robot at v_max 0.15 m/s with people walking in a small room. **The compute limit is fixed:** Pi 4 (Cortex-A72, CPU only, no Jetson or offboard laptop), and the CPU is already tight with slam_toolbox, the EKF and rf2o running (the EKF misses 20 Hz when the camera runs). Researched 2026-11-03.

Budget ranking (summary, worked out in the sections below):

| Rank | Option | Fits Pi 4 budget? | Effort | Moving obstacles |
| --- | --- | --- | --- | --- |
| 1 | collision_monitor Slowdown polygon + Approach (time-to-collision) on top of RPP | **Yes**, it runs as a node that already exists | Config only | Reactive only (no prediction) |
| 2 | Vector Pursuit (`ros-jazzy-vector-pursuit-controller`) | **Yes**, 15 % of one A72 core per its README | apt install plus config | None (path tracker with collision check) |
| 3 | Graceful controller (in Jazzy Nav2) | **Yes**, a cheap control law | Config only | None |
| 4 | MPPI (Jazzy, xtensor build) with reduced settings | **Marginal**, no Pi 4 benchmark found; Jazzy is the older, slower build | Config only (binary is in Jazzy) | Costmap snapshot only, no velocity model |
| 5 | DWB | Probably yes at low sample counts; no Pi numbers found | Config only | Costmap snapshot only |
| 6 | prox_mpc (SQP/ProxQP NMPC plugin with its own lidar IMM tracker) | Unknown: x86 numbers only, no hardware validation, 6 stars | apt plus a new tracker node | **Yes, it predicts** (the only Jazzy-released option that does) |
| 7 | TEB (`ros2-master` branch, Jazzy compile fix Nov 2024) | **Likely does not fit**: g2o optimisation, no Jazzy binary, source build of TEB and costmap_converter on the Pi | Source build | Yes, through `include_dynamic_obstacles` and obstacle messages with velocities |
| 8 | mpc_local_planner, or a hand-written acados/CasADi/do-mpc node | **Does not fit** the deadline or the "our code stays thin" rule | High | Only what you build |

## 1. nav2_mppi_controller: how it works, critics, parameters, Pi/ARM compute, moving obstacles

### Takeaway
MPPI samples `batch_size` noisy control sequences of `time_steps` x `model_dt`, rolls each out through a motion model (DiffDrive), scores them with plugin critics against the costmap and path, and returns a softmax-weighted average. It sees obstacles only as the current costmap (no obstacle velocities). The Jazzy binary is the **older xtensor build**. The Eigen rewrite, which is 45-50 % faster and which the maintainer estimated at "20-30 Hz on an RPi", is in Kilted/Rolling only and will not be backported. No measured Pi 4 benchmark was found, so on this already loaded Pi, MPPI is at best marginal and needs reduced settings and a measurement.

### Cited Findings
- Defaults (Jazzy README): `batch_size` 1000, `time_steps` 56, `model_dt` 0.05 s, `iteration_count` 1, `temperature` 0.3, `vx_max` 0.5, `wz_max` 1.9, `motion_model` DiffDrive / Omni / Ackermann. The docs give `gamma` as 0.015 in the table but 0.1 in the text, so the docs are inconsistent there. — [Nav2 Jazzy MPPI README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md)
- Docs' rule of thumb: "1000 at 50 Hz or 2000 at 30 Hz seems to produce good results"; keep `iteration_count` at 1 and prefer more batches. — [Nav2 MPPI configuration (rolling)](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/controller_plugins/mppi_controller/configuring_mppic/); [Jazzy README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md)
- `model_dt` "generally should be set to the duration of your control frequency"; it may be set lower but not larger (20 Hz -> 0.05). The prediction horizon is `time_steps * model_dt`. — [Jazzy README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md); [issue #5375 (diff-drive tuning)](https://github.com/ros-navigation/navigation2/issues/5375)
- Critics in the Jazzy source tree: Constraint, Cost, GoalAngle, Goal, Mecanum, Obstacles, OmniConstraint, PathAlign, PathAngle, PathFollow, PreferForward, Twirling, VelocityDeadband (the same 13 files exist on `main`). No dynamic-obstacle critic exists in either branch. — [GitHub contents, jazzy and main, `nav2_mppi_controller/src/critics`](https://github.com/ros-navigation/navigation2/tree/jazzy/nav2_mppi_controller/src/critics)
- ObstaclesCritic "uses estimated distances from obstacles using cost and inflation parameters", which converts cost back into distance so the inflation shape matters less. CostCritic "uses inflated costmap cost directly". GoalCritic acts within `threshold_to_consider` (default 1.4 m). — [Jazzy README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md)
- Compute-saving knobs: `consider_footprint: false` (recommended "if robot is circular or low compute power"), a larger `trajectory_point_step` in the Cost/PathAlign critics, `visualize: false` (it "slows the controller"), `regenerate_noises: false`; remove the PathAlign/PathFollow/PathAngle critics if path following is not needed. — [Jazzy README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md)
- Performance claims: "50+ Hz on a modest Intel processor (4th gen i5)" (Jazzy README; a later docs page says 100+ Hz). — [Jazzy README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md); [docs.nav2.org MPPI](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/controller_plugins/mppi_controller/configuring_mppic/)
- Eigen rewrite: "approximately 45-50% increases in speed by moving to Eigen from xtensor"; 125 Hz average on an i7-1365U; 55-60 Hz on a Jetson Orin using "about half of one Jetson CPU core" with default settings. Available "in Rolling and Kilted... will not be backported" (21 Jan 2025). — [ROS Discourse: Nav2 speedups in MPPI & Smac](https://discourse.openrobotics.org/t/nav2-speedups-in-mppi-smac-planner/41667)
- The Jazzy branch's CMakeLists still uses `find_package(xtensor)` / `xsimd`, which confirms Jazzy ships the slower build. — [navigation2 jazzy CMakeLists](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_mppi_controller/CMakeLists.txt)
- Pi 4 history: issue #4380, "MPPI ARM Binaries Issue in RPi4" (Humble binaries). `controller_server` died with SIGILL in `MPPIController::configure` on a Pi 4. The cause was build-farm CPU flags (`asimdhp`, `asimddp`, `atomics`) that the A72 lacks ("we don't have any RPi hardware on the official build farm"; ARM builds run on AWS Graviton). A source build worked. The issue was closed 15 Jan 2025 with the Eigen migration, and the maintainer said it runs at "50-60hz on a Jetson Orin with only 60% of a single core" and should reach "20-30hz" on an RPi (an estimate, not a measurement). — [navigation2 #4380](https://github.com/ros-navigation/navigation2/issues/4380)
- In the same thread the maintainer flagged `batch_size: 500, time_steps: 28, vx_max: 2.0` as aggressive parameters. This is the only "reduced" config seen on ARM in the sources, and it ran on a Jetson Nano, not a Pi. — [navigation2 #4380](https://github.com/ros-navigation/navigation2/issues/4380)
- Moving obstacles: MPPI "can ... avoid dynamic obstacles very fluidly" if PathAlign is not over-weighted, but this is the costmap redrawn each cycle, not prediction. — [Jazzy README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md)

### Inferences
- On Jazzy the Pi 4 runs the xtensor build. If the maintainer's 20-30 Hz Eigen estimate holds, the xtensor build at defaults would be about 10-17 Hz on an idle Pi (from the 45-50 % speedup). On this Pi, where slam_toolbox, the EKF and rf2o already compete for the cores, expect less. Treat "MPPI at defaults" as **not fitting**.
- Proposed reduced settings for an A/B test. These are **not from any Pi report** and must be measured: `controller_frequency: 10.0`, `model_dt: 0.1`, `time_steps: 30` (3.0 s horizon, 0.45 m at 0.15 m/s), `batch_size: 300-500`, `iteration_count: 1`, `vx_max: 0.15`, `consider_footprint: false` (circular, r = 0.12 m), `visualize: false`, critics limited to Constraint, Cost, Goal, GoalAngle, PathAlign, PathFollow and PreferForward. Pass test: no "Control loop missed its desired rate" warnings, and EKF/slam rates unchanged.
- The Pi 4 SIGILL fault was reported on Humble binaries. Whether the Jazzy arm64 binary has it is unknown, so the first check is simply `ros2 launch` with MPPI on the Pi.

### Gaps
- No measured MPPI Hz or CPU % on a Pi 4 (any distro) was found in Nav2 docs, GitHub issues or Discourse.
- No source confirms whether the Jazzy arm64 MPPI binary still has the SIGILL problem.

## 2. Other Nav2 Jazzy controllers (Graceful, DWB, Rotation Shim, Vector Pursuit) and TEB / mpc_local_planner ports

### Takeaway
Graceful, DWB, Rotation Shim, RPP and MPPI all ship in the Jazzy `navigation2` release. Vector Pursuit is an apt package for Jazzy and is the only one with an A72 CPU figure (15 % of one core). TEB has a `ros2-master` branch with a Jazzy compile fix (Nov 2024) and recent bug-fix commits (Sep 2026), but there is no Jazzy binary for it or for `costmap_converter`. `mpc_local_planner` has not been pushed since 2022. None of the cheap trackers predicts people.

### Cited Findings
- The Jazzy `navigation2` release packages include `nav2_graceful_controller`, `nav2_dwb_controller`, `nav2_mppi_controller`, `nav2_regulated_pure_pursuit_controller`, `nav2_rotation_shim_controller` and `nav2_collision_monitor`. — [rosdistro jazzy/distribution.yaml](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml)
- Graceful controller: a Lyapunov-based smooth control law (Park & Kuipers) toward a `motion_target` on the path; a pose follower, not an optimiser. — [nav2_graceful_controller README (jazzy)](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_graceful_controller/README.md)
- Vector Pursuit: a Jazzy Nav2 plugin (screw theory) with "active collision detection"; "consumes 15% of a single core on an ARM cortex-A72 CPU @ 1.8GHz"; install with `sudo apt-get install ros-jazzy-vector-pursuit-controller` (release 2.0.0-1). — [vector_pursuit_controller README (jazzy)](https://github.com/blackcoffeerobotics/vector_pursuit_controller/tree/jazzy); [rosdistro jazzy](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml)
- TEB: branch `ros2-master` (package 0.9.1, depends on `costmap_converter`, `libg2o`, `nav2_core`); commits "Fix compilation for jazzy (#421)" and "g2o jazzy compatibility" (Nov 2024); issues fixed through Sep 2026 (#439-#441); the default branch is still `noetic-devel`. Its README still says "ported to ROS2 (Dashing)". — [rst-tu-dortmund/teb_local_planner (GitHub API)](https://github.com/rst-tu-dortmund/teb_local_planner/tree/ros2-master)
- TEB is not in the Jazzy rosdistro (no binary). `libg2o` is released for Jazzy (2020.5.29-6). `costmap_converter` is not in the Jazzy rosdistro; its repo has `ros2` / `humble` branches and was last pushed Jul 2026. — [rosdistro jazzy](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml); [costmap_converter](https://github.com/rst-tu-dortmund/costmap_converter)
- ROS Index shows no Jazzy entry for teb_local_planner ("No version for distro jazzy showing lunar"). — [index.ros.org teb_local_planner](https://index.ros.org/r/teb_local_planner/)
- TEB ROS 2 still declares `include_dynamic_obstacles`, `dynamic_obstacle_inflation_dist` and `weight_dynamic_obstacle_inflation`, so it can plan around moving obstacles given velocities. — [teb_config.cpp (ros2-master)](https://github.com/rst-tu-dortmund/teb_local_planner/blob/ros2-master/teb_local_planner/src/teb_config.cpp)
- mpc_local_planner: has a `ros2-master` branch, last push 2022-11-29, not in the Jazzy rosdistro. — [rst-tu-dortmund/mpc_local_planner](https://github.com/rst-tu-dortmund/mpc_local_planner)

### Inferences
- Rotation Shim + RPP (or Graceful) is a config-only option for better in-place turns, but it does nothing for people.
- TEB is the classic "predict moving obstacles" option, but here it needs a source build of TEB and costmap_converter on the Pi (2 GB swap), a g2o solve every cycle, and an obstacle publisher with velocities. That **does not fit** the CPU budget or the time to the deadline.

### Gaps
- No Pi 4 CPU figures were found for DWB, Graceful or TEB in ROS 2.
- Whether TEB `ros2-master` builds cleanly on Jazzy arm64 today was not tested.

## 3. Optimisation-based MPC for ROS 2 (acados, CasADi, do-mpc, OSQP) and plugins with dynamic-obstacle support

### Takeaway
The only Jazzy-released Nav2 MPC plugin with built-in moving-obstacle prediction found is **prox_mpc** (SQP + ProxQP, with its own 2D-lidar IMM tracker). It is very new (repo created Jun 2026, 6 stars), has been validated only in simulation on x86, and all its numbers are the authors' own. Hand-built acados/CasADi/do-mpc nodes would break the "our code stays thin" rule and are not realistic before the deadline.

### Cited Findings
- prox_mpc: "Nonlinear MPC for ROS 2 Jazzy - a Nav2 controller plugin" (Apache-2.0, created 2026-06-13, pushed 2026-11-01, 6 stars); released for Jazzy (2.0.0-1); packages include `prox_mpc_controller` and `prox_mpc_obstacle_tracker` ("an in-house 2D-lidar dynamic-obstacle detector and IMM (CV+CTRV) tracker; feeds the controller's predictive avoidance"). — [simone-contorno/prox_mpc](https://github.com/simone-contorno/prox_mpc); [rosdistro jazzy](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml)
- The authors' benchmark (kinematic plant, x86 i7-10750H, 0.5 m/s cap, 2.0 s horizon), compute p50/p95 per cycle: ProxMPC 0.30/1.02 ms; DWB 2.96/4.41; MPPI 3.11/4.05; RPP 0.23/0.36; Vector Pursuit 0.23/0.38; Graceful 0.18/0.32. Collisions over 10 obstacle cells: ProxMPC 32 % (6 % with prediction), MPPI 18 %, RPP 16 %, DWB 30 %, VP 26 %, Graceful 36 %. In dense two-mover cells its median rises to about 2.2-2.7 ms. The authors say "no physical-hardware validation yet" and that two or more simultaneous movers still need a separate safety layer. — [prox_mpc README](https://github.com/simone-contorno/prox_mpc)
- Other MPC-related Jazzy releases: `osqp_vendor` 0.2.0-4, `osqp_eigen` (source entry), `ackermann_nlmpc` 1.0.3-1 (Ackermann, not diff-drive). — [rosdistro jazzy](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml)
- No acados, CasADi or do-mpc entries exist in the Jazzy rosdistro (searched by repo name). — [rosdistro jazzy](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml)

### Inferences
- prox_mpc's per-cycle cost looks cheap enough for a Pi 4 (about 10x MPPI on x86 by its own numbers). But the tracker is an extra node working on the 7 Hz A1M8 scan, and nothing has been measured on ARM or real hardware, so the budget fit is **unknown, not proven**. It is the only "predict human motion" option that is plausible on this hardware, and it would be the stretch experiment, not the baseline.
- In the same benchmark, RPP had the fewest collisions (16 %) and almost the lowest cost. That supports keeping RPP and adding a safety layer rather than swapping controllers (single-author simulation, so weak evidence).

### Gaps
- No independent evaluation of prox_mpc was found.
- No ROS 2 Jazzy diff-drive MPC with acados/CasADi running on a Pi 4 was found.

## 4. Nav2 features for moving obstacles: collision_monitor, velocity polygons, collision_detector, dynamic layers

### Takeaway
Jazzy's collision_monitor already provides Stop, Slowdown, Limit and **Approach** (time-to-collision) actions, plus `VelocityPolygon` zones that switch with commanded speed. The Approach model uses the robot's own velocity against current sensor points, so it is reactive and has no model of people's motion. It costs almost nothing and is the best fit for this Pi.

### Cited Findings
- Models: "Slowdown model: ... slow the maximum speed for a `%S` percent, if more than `N` points will appear inside the area"; "Approach model: Using the current robot speed, estimate the time to collision to sensor data. If the time is less than `M` seconds ... the robot will slow such that it is now at least `M` seconds to collision." — [nav2_collision_monitor README (jazzy)](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/README.md)
- `VelocityPolygon`: "allow switching of polygons based on the command velocity"; the first matching sub-polygon wins. Polygons can be static or "dynamically changing via a topic interface". — [collision_monitor README (jazzy)](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/README.md)
- Purpose: it is for obstacles that "appear out of no where ... or approach the robot at such high speed"; "circle shapes are preferred for the approach behavior models" for speed. — [collision_monitor README (jazzy)](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/README.md)
- `collision_detector` "does not affect the robot's velocity"; it only publishes detections to `collision_detector_state`, which is useful for logging people incursions as an experiment metric. — [collision_monitor README (jazzy)](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/README.md)

### Inferences
- For v = 0.15 m/s, an Approach circle (r = 0.12 m) with `time_before_collision` of about 1.5-2 s plus a Slowdown ring of about 0.5 m around the existing Stop polygon gives graded behaviour near people with no new code.
- The Approach model treats each scan as static, so a person walking toward the robot is "seen" only through successive scans at 7 Hz.

### Gaps
- Exact default values for `time_before_collision`, `simulation_time_step` and `slowdown_ratio` were not retrieved (the docs.nav2.org page returned 404). Check `ros2 param list` on the Pi.
- No maintained Jazzy or Kilted Nav2 costmap layer that tracks people or uses their velocity was found in the rosdistro (searched for track, people, social, obstacle).

## 5. Lowest-effort config-only swap for an A/B experiment

### Takeaway
Ranked by effort, with everything fitting the Pi budget: (A) RPP + collision_monitor Slowdown/Approach polygons is pure YAML and adds no new compute. (B) RPP -> MPPI with the reduced settings above is still config-only, since the binary is already in Jazzy Nav2, but its CPU fit has to be measured first. (C) Vector Pursuit needs one apt install. A predictive comparison (prox_mpc) is the stretch option. TEB and custom MPC do not fit.

### Cited Findings
- MPPI, RPP, Graceful, DWB and collision_monitor are in the same Jazzy `navigation2` release, so a swap is a `controller_server` `plugin:` change. — [rosdistro jazzy](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml)
- Nav2 controller_server supports several controller plugins at once (selectable per goal), per the Vector Pursuit README's setup step. — [vector_pursuit_controller README](https://github.com/blackcoffeerobotics/vector_pursuit_controller/tree/jazzy)

### Inferences
- Suggested experiment: the same goals with a person crossing the path. Condition 1 is RPP + Stop polygon (current). Condition 2 is RPP + Slowdown + Approach. Optional condition 3 is MPPI-reduced, run only if `controller_server` holds 10 Hz with slam_toolbox and the EKF running (log `top` / `ros2 topic hz`). Metrics: minimum distance to the person, number of stops, time to goal, missed-rate warnings, and EKF rate.
- Motors are not yet driven, so any controller A/B depends on the teammate's motor bring-up.

### Gaps
- No source measures any of these on a Pi 4 together with slam_toolbox, the EKF and rf2o. Every CPU fit beyond Vector Pursuit's 15 % figure has to be measured on this robot.

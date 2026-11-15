# People detection, tracking and short-horizon prediction from a 2D lidar (+ optional USB camera) on ROS 2 Jazzy / Raspberry Pi 4

Researched 2026-11-03. Hard constraint from the user, added partway through: compute is the Pi 4 CPU only (no GPU, no Coral, no offboard compute), the sensors are the A1M8 lidar and the USB camera, and the CPU is already tight (the EKF misses 20 Hz when the camera runs). So lidar-only classical methods come first. Every neural option below has its Pi 4 CPU cost stated, or is marked as not fitting.

Distro labels used: **Jazzy-ready** (a binary or a stated Jazzy test), **Foxy/Humble-only** (ROS 2, but not stated for Jazzy), **ROS 1 only**.

## 2D lidar leg/person detectors with ROS 2 ports

### Takeaway
No maintained, Jazzy-released leg or person detector exists. The realistic classical choice is mowito's `ros2_leg_detector`, a Foxy port that has to be built from source and probably needs fixing for Jazzy. It is a port of the angusleigh leg_tracker design: clusters, an OpenCV random forest, then a Kalman/GNN tracker, and it publishes people with velocities. It was trained for 0.33° beams at 7.5–15 Hz, while the A1M8 gives about 0.34–0.5° at 7 Hz, so it may need retraining. DR-SPAAM is the accurate neural option. It does not fit the Pi 4 CPU: its paper reaches only 9.7 FPS on a Jetson AGX GPU.

### Cited Findings
- **angusleigh/leg_tracker: ROS 1 Noetic only** (branch `noetic`, catkin, Ubuntu 20.04). It detects legs with an OpenCV random forest on scan clusters and tracks them jointly with global nearest-neighbour matching and Kalman filtering (pykalman). The tracker is Python, and porting it to C++ for speed is listed as a TODO. — [angusleigh/leg_tracker](https://github.com/angusleigh/leg_tracker)
- leg_tracker was trained for 0.33° angular resolution: other resolutions "may need retraining". It is tuned only for 7.5, 10 or 15 Hz scanners. — [angusleigh/leg_tracker](https://github.com/angusleigh/leg_tracker)
- leg_tracker's compute knobs are `max_detected_clusters` (track only the N closest objects) and `max_detect_distance` (a larger value detects farther but runs slower). — [angusleigh/leg_tracker](https://github.com/angusleigh/leg_tracker)
- **mowito/ros2_leg_detector: Foxy only**. It requires OpenCV 3.4.12 and is built with colcon. Input is `/scan` and `/tf`. Output is `/people_tracked` (a `PersonArray` with positions **and velocities**) plus markers. Parameters include `cluster_dist_euclid` (0.13 m), `forest_file`, `max_std` and `publish_occluded`, and it carries the same 0.33° / 7.5–15 Hz caveats. — [mowito/ros2_leg_detector](https://github.com/mowito/ros2_leg_detector); announcement [ROS Discourse](https://discourse.ros.org/t/ros2-foxy-compatible-leg-detector/18387)
- The original wg-perception `leg_detector` (in the `people` stack) has no Humble entry on the ROS index. — [index.ros.org leg_detector](https://index.ros.org/p/leg_detector)
- `petschekr/leg_tracker` is another fork that reuses leg_detector code. It says nothing about ROS 2, so treat it as ROS 1. — [petschekr/leg_tracker](https://github.com/petschekr/leg_tracker)
- **DR-SPAAM / DROW3 (Jia et al.)**: Python + PyTorch with no TensorRT. Runtimes from Table II of the paper:
  - Laptop (RTX 2080 Max-Q + i7-9750H): DR-SPAAM runs at 59.8 FPS, and the faster DR-SPAAM* at 87.2 FPS.
  - Jetson AGX Xavier: DR-SPAAM runs at 9.7 FPS (cutout 62.0 ms, net 6.9 ms, vote 33.6 ms), and DR-SPAAM* at 22.6 FPS.
  - DROW with T=5 runs at 2.6 FPS on the AGX, which the authors call "too slow for a real-time application".
  - AP0.5 on DROW: DR-SPAAM 70.3, DR-SPAAM* 71.8, DROW (T=1) 66.6.
  
  — [DR-SPAAM, arXiv 2004.14079](https://arxiv.org/pdf/2004.14079)
- The paper's AP0.5 curves also plot the classical "Leigh detector" baseline (the leg_tracker detector), and it sits below the learned detectors. — [DR-SPAAM, arXiv 2004.14079](https://arxiv.org/pdf/2004.14079)
- DR-SPAAM is real-time on desktop and laptop GPUs but not on embedded GPUs. With 3x spatial subsampling it reaches about 26.6 FPS on a Jetson AGX, at a cost of about 1.4 % AP. — [2D vs 3D lidar person detection, arXiv 2106.11239](https://arxiv.org/pdf/2106.11239)
- The official repo has a `stride` parameter for downsampling and a `bin/demo.py --time` benchmark. No CPU-only benchmark is published. — [VisualComputingInstitute/2D_lidar_person_detection](https://github.com/VisualComputingInstitute/2D_lidar_person_detection); [SAGARobotics fork](https://github.com/SAGARobotics/2D_lidar_person_detection); [NVIDIA write-up](https://developer.nvidia.com/blog/jetson-project-of-the-month-dr-spaam-person-detector-for-2d-range-data)
- **laser_segmentation (ajtudela): Jazzy-ready.** It is tested on Jazzy / Ubuntu 24.04 and ships as the binary `ros-jazzy-laser-segmentation`. It splits a scan into segments by jump distance and publishes `slg_msgs/SegmentArray`. It does **not** classify or track. — [laser_segmentation Jazzy docs](https://docs.ros.org/en/ros2_packages/jazzy/api/laser_segmentation)

### Inferences
- **DR-SPAAM does not fit.** The AGX's GPU gives 9.7 FPS, and the cutout step alone takes 62 ms on the AGX's ARM CPU. A Pi 4 Cortex-A72 with no GPU will be slower than that. Expect well under 7 Hz, and it would starve the EKF and slam_toolbox. Treat this as an estimate: no Pi 4 measurement exists.
- **The A1M8 resolution mismatch matters.** At 7 Hz with 720–1046 beams the step is about 0.34–0.5°, against the 0.33° the forest was trained on. With 26–29 % no-echo, legs at 1–2 m get very few points. Detection recall will likely be poor without retraining.
- The cheapest Jazzy-native classical path is `laser_segmentation`, followed by a leg-size or width gate on the segments, then a tracker. The gate is a few lines of code, not estimation maths, so it stays within the thin-code rule.
- A 0.1–0.2 m lidar plane cuts people at shin height. Leg detectors are designed for this height (about knee level), so the mounting suits the leg-detector approach.

### Gaps
- No Jazzy build report for `ros2_leg_detector` was found, and its last commit date was not visible. OpenCV 3.4.12 against Ubuntu 24.04's OpenCV 4.x is a likely build snag. This is unverified.
- No published Pi 4 CPU latency was found for DR-SPAAM or for leg_tracker's Python tracker.
- No 2026 Jazzy-specific person-detector package turned up. The ROS index could not be searched directly: docs.ros.org returned a bot-protection page.

## Camera person detection on the Pi 4 CPU

### Takeaway
It is not worth it here. The only concrete figure found is YOLOv8n at 640x640 with ncnn running at about **3.1 FPS on a Pi 4**, counting inference only. It would compete with the EKF, which already misses 20 Hz when the camera merely streams.

### Cited Findings
- From the Q-engineering ncnn table (third-party, inference only, no capture or post-processing): YOLOv8n at 640 runs at 3.1 FPS on a Pi 4, 20.0 FPS on a Pi 5 and 14.5 FPS on a Jetson Nano, with 37.3 mAP. — [Qengineering/YoloV8-ncnn-Raspberry-Pi-4](https://github.com/Qengineering/YoloV8-ncnn-Raspberry-Pi-4)
- The Ultralytics docs recommend NCNN on the Raspberry Pi and benchmark YOLOv8n on the Pi 4 and Pi 5. The Pi 4 figures were not retrievable. — [Ultralytics Raspberry Pi guide (mirror)](https://huggingface.co/akswelh/Test_model1/blob/main/docs/en/guides/raspberry-pi.md)
- Q-engineering also hosts lighter Pi 4 ncnn detectors such as PP-PicoDet. Their FPS was not captured. — [Qengineering/PP-PicoDet-ncnn-Raspberry-Pi-4](https://github.com/Qengineering/PP-PicoDet-ncnn-Raspberry-Pi-4)
- From the project record: the camera streams 1280x720 at 10 fps, and the EKF logs `Failed to meet update rate` when the camera runs. — AGENTS.md / notes in this repo

### Inferences
- Even at a lower input size (320 px), a 2–5 Hz bearing-only person detection still needs lidar fusion to get range. That is extra glue, and it falls outside the thin-code rule. Drop the camera from the pipeline. At most, use it offline to label lidar data or as Foxglove evidence for the report.

### Gaps
- No verified Pi 4 numbers were found for MobileNet-SSD or for YOLO at 320 px.

## Multi-object trackers and message types in ROS 2

### Takeaway
The trackers are `kf_hungarian_tracker` (Nav2-org, Python, KF + Hungarian, no release, distro unstated), `obstacle_detector` (a KF tracker of circle obstacles with velocity, but its Jazzy status is unverified and the README looks ROS 1), and the tracker built into `ros2_leg_detector`. SPENCER is ROS 1 only and dead. If `ros2_leg_detector` builds, its built-in tracker is the thinnest option, because it already outputs velocity.

### Cited Findings
- **ros-navigation/navigation2_dynamic** describes itself as "Navigation2's dynamic obstacle detection, tracking, and processing pipelines". It contains `kf_hungarian_tracker` and `nav2_dynamic_msgs`. It has only a `master` branch, no releases, 45 commits, 22 open issues and 79 stars, and names no distro. — [navigation2_dynamic](https://github.com/ros-navigation/navigation2_dynamic)
- `kf_hungarian_tracker` uses one Kalman filter per object for position and velocity, with Hungarian association through `scipy.optimize.linear_sum_assignment`, so it is Python. Parameters include `death_threshold` (3 frames), `vel_filter` ([0.1, 2.0] m/s), `cost_filter` (1.0 m) and `height_filter`, and its frame wording suggests point-cloud or camera input. — [kf_hungarian_tracker README](https://github.com/ros-navigation/navigation2_dynamic/tree/master/kf_hungarian_tracker)
- **obstacle_detector**: lidar scans become circle and segment obstacles, and `obstacle_tracker` applies a Kalman filter and publishes `tracked_obstacles` with velocity. It needs Armadillo. The README appears to describe the ROS 1 version, and Jazzy status is unverified. — [romb-technologies/obstacle_detector](https://github.com/romb-technologies/obstacle_detector/blob/master/README.md)
- `prox_mpc_obstacle_tracker` is on the ROS index. It tracks obstacles with velocity from a LaserScan, but its details were not verified. — [index.ros.org prox_mpc_obstacle_tracker](https://index.ros.org/p/prox_mpc_obstacle_tracker/)
- **spencer_people_tracking: ROS 1 only** (Kinetic/Melodic/Noetic). The last activity was around February 2021. A 2020 ROS 2 migration attempt touched only the rviz plugin and pedsim. — [spencer-project](https://github.com/spencer-project); [spencer_tracking_rviz_plugin issue #2](https://github.com/srl-freiburg/spencer_tracking_rviz_plugin/issues/2)
- **hunav_msgs** come with HuNavSim, which is "Tested in ROS2 Humble" with no Jazzy statement. It can also publish `/people`. — [robotics-upo/hunav_sim](https://github.com/robotics-upo/hunav_sim)

### Inferences
- In a 1–2 person room, a constant-velocity KF with Hungarian or GNN association is all the tracking needed. Every candidate already implements one, so the project should not write its own (rule 2).
- Message-type choice: `people_msgs` is the type consumed by the social costmap layers. `ros2_leg_detector` outputs its own `PersonArray`. Some converter glue will probably be needed whichever pair is chosen.

### Gaps
- Whether `people_msgs` is released for Jazzy could not be confirmed. The index search was blocked.
- Whether `kf_hungarian_tracker` and `obstacle_detector` build on Jazzy could not be confirmed, and no last-commit dates were visible.

## Getting tracked people into Nav2 (costmap layers, MPPI critics)

### Takeaway
There is no maintained Jazzy people or social costmap layer, and stock MPPI has no critic for tracked-obstacle velocity. Stock MPPI simply reacts to whatever is in the costmap each cycle. The realistic options are:
- **(a)** do nothing special: people already appear in the obstacle layer from `/scan`, and MPPI replans at its rate;
- **(b)** port `social_nav2` or `nav2_social_costmap_plugin` (Foxy era);
- **(c)** publish predicted positions as a short fake PointCloud2 or scan into a standard obstacle or voxel layer. That is thin glue, but strictly it is "our code".

### Cited Findings
- **social_nav2 (jginesclavero)** is a Nav2 costmap plugin that draws Hall's proxemic zones around people. It needs the people's pose and orientation, and includes a people filter that clears people's cells from the obstacle layer. It states no Jazzy support. — [jginesclavero/social_nav2](https://github.com/jginesclavero/social_nav2)
- **social_navigation_layers** is a ROS 1 costmap_2d package with no Jazzy version on the index. — [index.ros.org social_navigation_layers](https://index.ros.org/p/social_navigation_layers/)
- **nav2_social_costmap_plugin (robotics-upo)** was built for Foxy, and a user reported trouble on Humble. — [Robotics StackExchange archive](https://answers.ros.org/question/416314/)
- Tufts SociallyAwarePathNavigation is a ROS 2 research code base with personal-space costmaps. Its Jazzy status is unverified. — [SociallyAwarePathNavigation](https://github.com/aryamanpandya99/SociallyAwarePathNavigation)
- Nav2 maintainers say MPPI is "exceptionally effective at reacting to dynamic obstacles intelligently even when not explicitly modeled as dynamic in the cost map". — [Macenski et al., arXiv 2307.15236](https://arxiv.org/pdf/2307.15236)
- The MPPI ObstaclesCritic uses distance estimated from costmap cost and inflation. The docs list no critic for tracked or predicted obstacles. — [Nav2 MPPI docs (Jazzy)](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/controller_plugins/mppi_controller/configuring_mppic/)
- Schöneberg et al. (2025) say existing Nav2 planners "primarily deal with static obstacles or react to the current position of dynamic obstacles". They propose an MPC with a stochastic VAR obstacle predictor and Mahalanobis-distance constraints, tested in Gazebo only, with no code link and no distro or compute figures. — [arXiv 2504.19193](https://export.arxiv.org/abs/2504.19193)
- **HuNavSim** simulates humans (social force model, Gazebo/Isaac/Webots wrappers) and includes a metrics evaluator. It is tested on Humble only. — [robotics-upo/hunav_sim](https://github.com/robotics-upo/hunav_sim)

### Inferences
- With v_max 0.15 m/s and people at about 1 m/s, prediction mostly buys earlier yielding rather than collision safety. The safety node (`stop_dist_m`) remains the real guard.
- A "predicted obstacle" input means putting points at p + v·t for t in about 0.5–2 s into a costmap observation source. It reuses the stock obstacle layer and MPPI unchanged. This is the smallest path, and it is fully Jazzy-native.

### Gaps
- No Jazzy fork of social_nav2 or nav2_social_costmap_plugin was found. This was not exhaustively checked.
- No published MPPI critic consuming tracked people was found.

## Removing people from slam_toolbox localisation input

### Takeaway
No packaged "remove tracked people from LaserScan" filter was found. The two partial options are social_nav2's people filter, which clears people from the *costmap*, not from the scan sent to slam_toolbox, and a few lines that mask beams falling inside tracked-person circles before republishing `/scan_filtered`. In a small room with 1–2 people, slam_toolbox scan matching is usually robust to a few leg blobs, so this may not be worth it.

### Cited Findings
- social_nav2 includes a people filter that removes people's cells from the obstacle layer before adding proxemic zones. It acts on the costmap, not on the localisation scan. — [jginesclavero/social_nav2](https://github.com/jginesclavero/social_nav2)
- The search for a ROS 2 dynamic-object scan filter returned only commercial offline tools (NavVis, FARO SCENE), not ROS packages. — [NavVis dynamic object filtering](https://knowledge.navvis.com/docs/dynamic-object-filtering); [FARO moving objects filter](https://knowledge.faro.com/Software/FARO_SCENE/SCENE/Using_the_Moving_Objects_Filter)

### Inferences
- This links to OI-8. A person walking behind the robot is one of the two remaining suspects for rf2o under-reading a push by 76 %. People affect **rf2o** (dense scan-to-scan odometry), probably more than slam_toolbox. A people mask on the scan feeding rf2o could be the useful variant. It can be tested offline on the existing bags once a detector runs.
- `laser_filters` (a standard ROS package) has box and range filters, but static ones. A dynamic per-person mask would be our own small node.

### Gaps
- `laser_filters` Jazzy release and plugin list could not be confirmed: docs.ros.org blocked the fetch.
- No study was found that measures slam_toolbox localisation error with 1–2 walking people.

## Constant-velocity prediction as baseline

### Takeaway
Strong evidence says a constant-velocity model (CVM) is good enough. On ETH/UCY at a 4.8 s horizon, the CVM beats most published neural predictors. Over a 1–2 s Nav2 horizon in a small room it is the right choice, and every candidate tracker already gives the velocity it needs.

### Cited Findings
- Schöller et al. (RA-L 2020) observe 8 steps (3.2 s) and predict 12 steps (4.8 s) at 0.4 s per step, averaged over ETH/UCY. ADE/FDE in metres:

  | Model | ADE | FDE |
  | --- | --- | --- |
  | CVM | 0.39 | 0.83 |
  | CVM-S (σ=25° noise, best of 20) | 0.28 | 0.56 |
  | S-GAN | 0.32 | 0.60 |
  | SoPhie | 0.54 | 1.15 |
  | SR-LSTM | 0.45 | 0.94 |
  | LSTM | 0.99 | 2.08 |

  — [What the Constant Velocity Model Can Teach Us…, arXiv 1903.07933](https://ar5iv.arxiv.org/html/1903.07933)
- The authors conclude that the CVM "can outperform even state-of-the-art neural models". — [fortiss summary](https://www.fortiss.org/ergebnisse/publikationen/details/what-the-constant-velocity-model-can-teach-us-about-pedestrian-motion-prediction)
- Separately, other studies note that on ETH/UCY, naive models without social inputs can outperform social models. — [Boucaud et al., arXiv 2106.15321](https://www.arxiv.org/pdf/2106.15321)
- A multi-density empirical comparison of predictors exists, but its numbers were not extracted. — [arXiv 2307.15442](https://arxiv.org/pdf/2307.15442)

### Inferences
- Error grows with horizon: 0.83 m FDE at 4.8 s, so it should be well under 0.5 m at 1–2 s. That is a rough linear scaling, not a measured figure.
- The error on this robot will be dominated by noisy velocity estimates from a 7 Hz, 29 %-dropout leg detector, not by the motion model.

### Gaps
- No CVM error figure specific to a 1–2 s horizon was found. Per-step errors would need the paper's per-horizon plots.

## Recommended pipeline (synthesis)

1. **Detect:** build `ros2_leg_detector` from source on Jazzy (Foxy port, random forest, classical) and check recall on the A1M8. The fallback is `ros-jazzy-laser-segmentation` plus a segment-width gate (about 0.05–0.25 m) as a leg-candidate filter. Do not use DR-SPAAM: it does not fit the Pi 4 CPU. Do not use the camera: YOLOv8n reaches about 3 FPS and is already CPU-bound.
2. **Track:** use `ros2_leg_detector`'s built-in KF/GNN tracker, which outputs velocity. The alternative is `kf_hungarian_tracker` (Python, no release, distro unstated).
3. **Predict:** constant velocity, p + v·t, over 0.5–2 s.
4. **Into Nav2:** either rely on stock MPPI reacting to the live obstacle layer, or publish the predicted points as an extra costmap observation source. Social layers are Foxy-era ports and optional.
5. **Localisation:** an optional scan mask. More relevant to rf2o and OI-8 than to slam_toolbox.
6. **Test without people present:** HuNavSim (Humble-tested) or bag replay.

Compute (estimated, not measured): the leg detector is a Python random forest plus KF at 7 Hz on a few clusters, which should be light on one A72 core with the camera off. This must be measured on the Pi before it is reported (rule 4).

# SLAM build path

A step-by-step path for building the SLAM section, written so each step teaches what the next one needs. Every task has: why it matters, what to do, how you know it's done, and an **explain it back** question. Don't tick a task until you can answer its question in your own words; write the answer in `docs/slam_journal.md` under the task's ID.

Related: [docs/slam.md](slam.md) (architecture, fixes, references) · [docs/plan.md](plan.md) (project phases) · [docs/test_log.md](test_log.md) (numbers).

## Rules that hold throughout

1. Push the robot by hand for stages 1–6. You don't need working motors to learn odometry and mapping, so you never wait on the driving section.
2. Record a bag of every test drive. Tuning happens on replays, never by redriving.
3. When you replay, play `/scan`, `/imu/data` and `/tf_static` only. Never the recorded `/tf`.
4. One change at a time, written in `docs/test_log.md` with the commit hash.
5. Freeze SLAM parameters before evaluation runs (stage 9).

**Tags:** *learn* = read or think, no robot · *bag* = works from a recorded bag · *robot* = needs the robot powered · *build* = you write code or config · *needs Nav2* = waits on the navigation section.

## Progress

**Stage 0: Foundations**

- [x] [0.1 ROS 2 in one picture: nodes, topics, QoS](#01-ros-2-in-one-picture-nodes-topics-qos)
- [ ] [0.2 Frames and transforms](#02-frames-and-transforms)
- [x] [0.3 What SLAM is, and which kind you're using](#03-what-slam-is-and-which-kind-youre-using)

**Stage 1: The sensor: /scan**

- [x] [1.1 Read a LaserScan by hand](#11-read-a-laserscan-by-hand)
- [x] [1.2 See the scan in Foxglove](#12-see-the-scan-in-foxglove)
- [x] [1.3 Diagnose the missing points](#13-diagnose-the-missing-points)
- [x] [1.4 Find which way the lidar faces](#14-find-which-way-the-lidar-faces)
- [x] [1.5 Record and replay your first bag](#15-record-and-replay-your-first-bag)

**Stage 2: The robot's frames**

- [ ] [2.1 Measure the robot](#21-measure-the-robot)
- [ ] [2.2 Write the URDF](#22-write-the-urdf)

**Stage 3: Odometry from scans: rf2o**

- [ ] [3.1 How rf2o works](#31-how-rf2o-works)
- [x] [3.2 Run rf2o alone and push the robot by hand](#32-run-rf2o-alone-and-push-the-robot-by-hand)
- [ ] [3.3 Break it on purpose](#33-break-it-on-purpose)
- [x] [3.4 Understand the startup race](#34-understand-the-startup-race)

**Stage 4: Fusing the gyro: the EKF**

- [ ] [4.1 Kalman filter intuition](#41-kalman-filter-intuition)
- [ ] [4.2 See the zero-covariance bug](#42-see-the-zero-covariance-bug)
- [x] [4.3 Write the covariance relay](#43-write-the-covariance-relay)
- [x] [4.4 Calibrate the variances](#44-calibrate-the-variances)
- [ ] [4.5 Show that fusion helps](#45-show-that-fusion-helps)

**Stage 5: Mapping with slam_toolbox**

- [ ] [5.1 Pose graphs and loop closure](#51-pose-graphs-and-loop-closure)
- [ ] [5.2 Lifecycle nodes, learned by breaking them](#52-lifecycle-nodes-learned-by-breaking-them)
- [x] [5.3 Write mapping.launch.py](#53-write-mappinglaunchpy)
- [ ] [5.4 Map the room](#54-map-the-room)
- [ ] [5.5 Tune on replays, then freeze](#55-tune-on-replays-then-freeze)

**Stage 6: Localisation on the saved map**

- [ ] [6.1 Mapping versus localisation](#61-mapping-versus-localisation)
- [ ] [6.2 Run localisation](#62-run-localisation)
- [ ] [6.3 Set the start pose from Foxglove](#63-set-the-start-pose-from-foxglove)
- [ ] [6.4 Wrong-start test](#64-wrong-start-test)

**Stage 7: Your Foxglove SLAM workspace**

- [x] [7.1 Write the trajectory recorder](#71-write-the-trajectory-recorder)
- [ ] [7.2 Build and commit the layout](#72-build-and-commit-the-layout)
- [ ] [7.3 Control SLAM from Foxglove](#73-control-slam-from-foxglove)

**Stage 8: Autonomous mapping**

- [ ] [8.1 How frontier exploration works](#81-how-frontier-exploration-works)
- [x] [8.2 Build explore_lite](#82-build-explore_lite)
- [ ] [8.3 Write explore.launch.py](#83-write-explorelaunchpy)
- [ ] [8.4 First supervised run](#84-first-supervised-run)
- [ ] [8.5 Compare with manual mapping](#85-compare-with-manual-mapping)

**Stage 9: Evaluation**

- [ ] [9.1 Survey floor checkpoints](#91-survey-floor-checkpoints)
- [ ] [9.2 Record evaluation runs](#92-record-evaluation-runs)
- [ ] [9.3 Write the metrics script](#93-write-the-metrics-script)
- [ ] [9.4 IMU ablation](#94-imu-ablation)
- [ ] [9.5 Measure the Pi's load](#95-measure-the-pis-load)
- [ ] [9.6 Write the SLAM section](#96-write-the-slam-section)

**Stage X: Extensions**

- [ ] [X.1 Gyro-based scan deskewing](#x1-gyro-based-scan-deskewing)
- [ ] [X.2 People in the room](#x2-people-in-the-room)
- [ ] [X.3 Map quality without ground truth](#x3-map-quality-without-ground-truth)

---

## Stage 0: Foundations

**Goal:** By the end you can explain how ROS 2 nodes, topics and transforms fit together, and what kind of SLAM you're building and why.

### 0.1 ROS 2 in one picture: nodes, topics, QoS

*Tags:* learn, robot

**Why it matters.** Every part of SLAM is a node talking over topics. If you can inspect a topic, you can debug anything that follows.

**Do:**

1. Start only the lidar on the Pi (the lidar launch from the bringup package).
2. Run `ros2 node list`, `ros2 topic list`, `ros2 topic info /scan -v`, `ros2 topic hz /scan` and `ros2 topic echo /scan --once`.
3. Write down the message type, publisher, rate and QoS of `/scan`.

**Done when:** You can state `/scan`'s type, publisher node, rate and reliability setting without looking.

**Explain it back:** *What does QoS 'durability: transient local' mean, and why is `/map` published that way? (Hint: Foxglove may connect long after the map was last published.)*

### 0.2 Frames and transforms

*Tags:* learn

**Why it matters.** SLAM is mostly about keeping frames consistent. Most SLAM bugs are frame bugs.

**Do:**

1. Read REP 105 (the short section on map, odom and base_link).
2. Draw by hand: `map → odom → base_footprint → base_link → laser, imu_link`. Next to each arrow write which node publishes it: slam_toolbox, the EKF, or the URDF via robot_state_publisher.
3. Later, once things run, compare with `ros2 run tf2_tools view_frames`.

**Done when:** Your drawing matches `view_frames` when the full stack runs.

**Explain it back:** *Why are `map → odom` and `odom → base_footprint` two separate transforms instead of one? Which one is smooth, and which one can jump?*

**Read:** [REP 105, coordinate frames for mobile robots](https://www.ros.org/reps/rep-0105.html)

### 0.3 What SLAM is, and which kind you're using

*Tags:* learn

**Why it matters.** Your report needs to justify the choice, and you need the mental model to read the pose graph later.

**Do:**

1. Read the review's sections on filter-based, scan-matching and graph-based SLAM.
2. Skim the SLAM Toolbox paper (it's two pages).

**Done when:** You can place rf2o, the EKF and slam_toolbox each in one of the review's categories.

**Explain it back:** *Why does a particle-filter SLAM like GMapping struggle without wheel encoders, and what does loop closure do in a pose graph that a filter can't?*

**Read:** [Ran et al. 2025, 2D Lidar SLAM review](https://doi.org/10.3390/rs17071214) · [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783)

---

## Stage 1: The sensor: /scan

**Goal:** By the end you understand exactly what the lidar gives you, where its gaps are, and which way it faces.

### 1.1 Read a LaserScan by hand

*Tags:* robot

**Why it matters.** Every later algorithm consumes this message. Knowing its fields makes rf2o and slam_toolbox far less magical.

**Do:**

1. `ros2 topic echo /scan --once` and find `angle_min`, `angle_max`, `angle_increment`, `range_min`, `range_max`.
2. Count the entries in `ranges` and how many are `inf`.
3. Work out the angle of `ranges[i]`: `angle_min + i * angle_increment`.

**Done when:** You can point at an object in the room and predict roughly which index in `ranges` sees it.

**Explain it back:** *What does `inf` mean in `ranges`, and why is it different from a short real reading?*

### 1.2 See the scan in Foxglove

*Tags:* robot

**Why it matters.** Foxglove is your eyes for the whole section. Get comfortable with it on the simplest data.

**Do:**

1. Connect Foxglove on your Mac to `ws://sherm-raspi.local:8765`.
2. Open a 3D panel, set the display frame to `laser`, and enable `/scan`.
3. Walk around the robot and watch yourself appear.

**Done when:** Walls show as straight lines of points and you can see your own legs.

**Explain it back:** *Why does one person show up as two small arcs?*

### 1.3 Diagnose the missing points

*Tags:* bag, build

**Why it matters.** About a third of points were missing in earlier tests. Mapping and rf2o both get worse with sparse scans, so find out why now, not in stage 5.

**Do:**

1. Record 30 s of `/scan` with the robot still: `ros2 bag record -s mcap /scan -o bags/still`.
2. Write a short Python script (or node) that reads the bag and reports the fraction of `inf` ranges and a histogram of where they fall by angle (30° bins).
3. Compare with what's around the robot: glass, black or shiny surfaces, open doorways, things beyond 8 m.

**Done when:** You can say whether the gaps come from the surfaces (normal) or from the driver (fixable), with the histogram as evidence.

**Explain it back:** *If gaps cluster at one angle range regardless of where the robot points, what does that suggest?*

### 1.4 Find which way the lidar faces

*Tags:* robot

**Why it matters.** The earlier Python test used raw RPLidar angles; the ROS driver uses its own convention. A wrong yaw makes rf2o think forward is backward.

**Do:**

1. Put a box 50 cm directly in front of the robot.
2. In Foxglove (display frame `laser`), note which axis the box lands on.
3. Box on +x: yaw 0. On +y: −90°. On −y: +90°. On −x: 180°. Write it down for 2.2.

**Done when:** After the URDF is in (2.2), the box appears on +x with the display frame set to `base_link`.

**Explain it back:** *If yaw were off by 180°, what would rf2o report when you push the robot forward?*

### 1.5 Record and replay your first bag

*Tags:* bag

**Why it matters.** Replays let you rerun the same data with different settings. Every tuning step from stage 3 on depends on this habit.

**Do:**

1. `ros2 bag record -s mcap /scan /tf_static -o bags/first` while you walk around the robot.
2. Copy the bag to your Mac and open the `.mcap` file in Foxglove.
3. Play it back on the Pi too: `ros2 bag play bags/first`.

**Done when:** The bag replays in Foxglove with the same scans you saw live.

**Explain it back:** *Why is tuning on a replayed bag more trustworthy than tuning by redriving the robot?*

---

## Stage 2: The robot's frames

**Goal:** By the end the TF tree is complete and correct, so every later node can find the lidar and IMU relative to the robot.

### 2.1 Measure the robot

*Tags:* robot

**Why it matters.** Every `# MEASURE` value is a placeholder. Wrong offsets show up as maps that smear when the robot turns.

**Do:**

1. With a tape measure, find the lidar's centre relative to the midpoint between the wheels: x forward, y left, scan-plane height z.
2. Same for the IMU, plus wheel radius and the robot's outer radius.
3. Record them in `docs/test_log.md`.

**Done when:** Every `# MEASURE` value for the laser and IMU has a measured number next to it.

**Explain it back:** *Why does a lidar mounted off-centre cause smearing only when the robot turns, not when it drives straight?*

### 2.2 Write the URDF

*Tags:* build

**Why it matters.** rf2o and slam_toolbox need `base_footprint → laser`. Without it, nothing downstream starts properly.

**Do:**

1. Define links `base_footprint`, `base_link`, `laser`, `imu_link`.
2. Joints: `base_footprint → base_link` (up by the wheel radius), `base_link → laser` (your offsets plus the yaw from 1.4), `base_link → imu_link`.
3. Validate: `xacro delivery_bot.urdf.xacro > /tmp/r.urdf && check_urdf /tmp/r.urdf`.
4. Run robot_state_publisher and check `view_frames` and the robot model in Foxglove.

**Done when:** `view_frames` shows the full chain and the box from 1.4 sits on +x in `base_link`.

**Explain it back:** *The EKF publishes `odom → base_footprint`. Why must `base_footprint` still appear in the URDF? (The skeleton comment says otherwise. It's wrong.)*

**Read:** [docs/slam.md](slam.md)

---

## Stage 3: Odometry from scans: rf2o

**Goal:** By the end you know how rf2o estimates motion from two scans, how well it does on your robot, and where it breaks.

### 3.1 How rf2o works

*Tags:* learn

**Why it matters.** rf2o replaces the wheel encoders you don't have. Its weaknesses become your robot's weaknesses.

**Do:**

1. Read the rf2o paper's abstract and method overview: range flow, dense alignment, no point matching.
2. Note the reported runtime (about 1 ms per scan) and which situations the authors call hard.

**Done when:** You can explain range flow in two sentences.

**Explain it back:** *If the robot drives along a long, smooth wall, what does rf2o see change in the ranges, and what can't it measure?*

**Read:** [Jaimez et al. 2016, rf2o](https://doi.org/10.1109/ICRA.2016.7487647)

### 3.2 Run rf2o alone and push the robot by hand

*Tags:* robot, bag

**Why it matters.** Seeing raw rf2o output before fusing anything gives you a baseline to compare every later step against.

**Do:**

1. For this experiment only, run the lidar, robot_state_publisher and rf2o with `publish_tf: true`, and no EKF.
2. Record a bag. Push the robot 1 m along a taped line, then spin it 360° by hand.
3. Read the final pose from `/odom_rf2o` and compare with the tape.

**Done when:** Distance and heading error for both moves recorded in `docs/test_log.md`.

**Explain it back:** *rf2o publishes both a pose and a velocity. Why do we fuse only its velocity in the EKF?*

**Read:** [Jaimez et al. 2016, rf2o](https://doi.org/10.1109/ICRA.2016.7487647)

### 3.3 Break it on purpose

*Tags:* bag

**Why it matters.** Knowing failure modes lets you design routes and explain bad results in the report.

**Do:**

1. Try a fast hand spin, a push along a bare wall, and someone walking past.
2. In a Foxglove Plot panel, graph `/odom_rf2o.twist.twist.angular.z` during each.

**Done when:** You've ranked the three by how badly rf2o did, with plots saved.

**Explain it back:** *Why would a 5.5 Hz lidar struggle more with fast spins than a 40 Hz one?*

**Read:** [Salem et al. 2023, lidar de-skewing](https://arxiv.org/abs/2303.07312)

### 3.4 Understand the startup race

*Tags:* learn, robot

**Why it matters.** rf2o reads the laser's position only once, on its first scan. If the URDF transform isn't there yet, rf2o runs wrong for the whole session.

**Do:**

1. Start everything at once and search rf2o's startup log for a `lookupTransform` error.
2. Ask the bringup owner to delay rf2o by about 2 s (an interface request, listed in docs/slam.md).

**Done when:** Ten consecutive launches with no transform error from rf2o.

**Explain it back:** *Why would this bug matter much more if `laser_yaw` were 180° than if it were 0°?*

**Read:** [docs/slam.md](slam.md)

---

## Stage 4: Fusing the gyro: the EKF

**Goal:** By the end you understand how the EKF weighs two sensors, you've found and fixed the bug that made it ignore the gyro, and you've shown fusion helps.

### 4.1 Kalman filter intuition

*Tags:* learn

**Why it matters.** Covariance is how the filter decides whom to trust. The bug in 4.2 only makes sense once this clicks.

**Do:**

1. Read 'How a Kalman filter works, in pictures'.
2. Read the comments in `ekf.yaml` and robot_localization's README on 2D mode and sensor configuration.

**Done when:** You can describe predict and update, and what a measurement's covariance does in the update.

**Explain it back:** *Two sensors measure yaw rate. One reports variance 0.0004, the other 0.000000001. What does the filter's output follow, and why?*

**Read:** [How a Kalman filter works, in pictures](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/) · [robot_localization source and docs](https://github.com/cra-ros-pkg/robot_localization)

### 4.2 See the zero-covariance bug

*Tags:* bag

**Why it matters.** rf2o publishes zero covariance, so the EKF treats it as perfect and ignores the gyro. Seeing it yourself is better than reading about it.

**Do:**

1. Run the EKF with `odom0: /odom_rf2o` on a spin bag.
2. `ros2 topic echo /diagnostics` and find the 'covariance … was zero' warning.
3. Plot yaw rate from `/odom_rf2o`, `/imu/data` and `/odometry/filtered` together in Foxglove.

**Done when:** Screenshot showing the filtered line sitting exactly on rf2o's line, saved for the report.

**Explain it back:** *Why does robot_localization replace a zero variance with a tiny number instead of refusing the message?*

**Read:** [robot_localization source and docs](https://github.com/cra-ros-pkg/robot_localization)

### 4.3 Write the covariance relay

*Tags:* build

**Why it matters.** A small node that copies rf2o's message and fills in realistic covariance fixes the bug without changing rf2o.

**Do:**

1. In `delivery_bot_slam`, implement `odom_covariance_relay`: subscribe `/odom_rf2o`, copy, set the twist covariance, publish `/odom_rf2o_cov`.
2. The twist covariance is a 6×6 matrix stored row by row: index 0 is vx, index 35 is yaw rate. Set the others to 1e3.
3. Point `odom0` in `ekf.yaml` at `/odom_rf2o_cov`.

**Done when:** `ros2 topic echo /odom_rf2o_cov --field twist.covariance` shows your values and the diagnostics warning is gone.

**Explain it back:** *Why is a relay node a better fix here than editing rf2o's source?*

**Read:** [docs/slam.md](slam.md)

### 4.4 Calibrate the variances

*Tags:* robot, bag

**Why it matters.** Guessed variances decide the outcome of every fusion experiment. Measure them, on data you won't evaluate on.

**Do:**

1. Robot still for 30 s: compute the standard deviation of gyro yaw rate and of rf2o's vx and yaw rate.
2. Do a separate calibration push and spin run. Compare rf2o's yaw rate with the gyro's to estimate rf2o's error.
3. Set the relay's variances; note the method in `docs/test_log.md`.

**Done when:** The variance values in `odom_covariance.yaml` have a measured source written next to them.

**Explain it back:** *Why must calibration data be kept separate from the runs you evaluate? (Merrick & Nandikolla name this as a limitation of their own study.)*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

### 4.5 Show that fusion helps

*Tags:* bag

**Why it matters.** This is your first real result: does the gyro improve heading?

**Do:**

1. Record 3 full hand spins ending where you started.
2. Replay the same bag twice: EKF with rf2o only, and with rf2o plus gyro.
3. Compare final heading errors and the yaw-rate plots.

**Done when:** A small table in `docs/test_log.md`: heading error for each configuration.

**Explain it back:** *If fusion barely changes the result on straight pushes but helps on spins, what does that tell you about where rf2o is weakest?*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468) · [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264)

---

## Stage 5: Mapping with slam_toolbox

**Goal:** By the end you have a saved map of the room, you can read the pose graph, and you've tuned the few parameters that matter, then frozen them.

### 5.1 Pose graphs and loop closure

*Tags:* learn

**Why it matters.** When the map suddenly snaps straight, that's loop closure. Understanding it turns that moment from magic into something you can debug.

**Do:**

1. Re-read the SLAM Toolbox paper and the slam_toolbox README's description of modes.
2. Look at `slam_mapping.yaml` and find the loop-closure parameters and `ceres_loss_function`.

**Done when:** You can say what a node, an edge and a loop closure are, in your robot's terms.

**Explain it back:** *What could go wrong with a loop closure in a room with two similar-looking walls, and why does Huber loss help?*

**Read:** [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783) · [Huang et al. 2022, robust 2D lidar SLAM](https://doi.org/10.1007/s13320-022-0657-6) · [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

### 5.2 Lifecycle nodes, learned by breaking them

*Tags:* robot, learn

**Why it matters.** slam_toolbox 2.8 waits to be configured and activated. Launched as a plain node it sits idle with no error, and the reference launch file has exactly this bug.

**Do:**

1. Start `async_slam_toolbox_node` as a plain node with your params.
2. `ros2 lifecycle get /slam_toolbox` shows `unconfigured`, and there's no `/map`.
3. Then: `ros2 lifecycle set /slam_toolbox configure` and `ros2 lifecycle set /slam_toolbox activate`. The map appears.

**Done when:** You've seen the node go unconfigured → inactive → active and the map appear only at the end.

**Explain it back:** *Why would a robotics framework want nodes that start idle and wait to be activated?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

### 5.3 Write mapping.launch.py

*Tags:* build

**Why it matters.** Make the lifecycle steps automatic so mapping starts with one command.

**Do:**

1. Include the base launch. Start slam_toolbox as a `LifecycleNode`.
2. Emit a configure event, then on reaching `inactive`, emit activate (the same pattern as slam_toolbox's own `online_async_launch.py`).
3. Forward `use_sim_time` so the same launch works on bags.

**Done when:** One command gives you `/map` with no manual lifecycle steps, live and on a replayed bag.

**Explain it back:** *Why does the activate step need to wait for the `inactive` state rather than firing straight after configure?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox) · [docs/slam.md](slam.md)

### 5.4 Map the room

*Tags:* robot, bag

**Why it matters.** Your first real map, and the bag you'll tune on.

**Do:**

1. Start on the taped home mark. Push slowly (or use teleop), loop the room, return to home. Record a bag.
2. Watch `/slam_toolbox/graph_visualization` in Foxglove grow, and catch the loop-closure snap.
3. Save: `map_saver_cli` for the image, and the `serialize_map` service for localisation.

**Done when:** Walls are straight, and two wall-to-wall distances on the map match the tape measure within 5 cm.

**Explain it back:** *Where in the room did the map look worst before loop closure, and why there?*

**Read:** [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783)

### 5.5 Tune on replays, then freeze

*Tags:* bag, build

**Why it matters.** Evaluation is only fair if parameters stay fixed. Do your tuning now, deliberately.

**Do:**

1. Write `slam_replay.launch.py`: robot_state_publisher, rf2o, relay, EKF, slam_toolbox, all with `use_sim_time`, no drivers.
2. Replay the 5.4 bag (only `/scan`, `/imu/data` and `/tf_static`) varying one parameter at a time: `min_laser_range` 0 vs 0.15, loop closure on vs off, `minimum_travel_distance`.
3. Pick values, commit them, and write 'frozen on <date>, commit <hash>' at the top of the config.

**Done when:** A short table of what each change did, and a frozen config commit.

**Explain it back:** *Why must you never replay the recorded `/tf` when rerunning SLAM on a bag?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [docs/slam.md](slam.md)

---

## Stage 6: Localisation on the saved map

**Goal:** By the end the robot knows where it is on the map at every start, and you know how much error it can recover from.

### 6.1 Mapping versus localisation

*Tags:* learn

**Why it matters.** In localisation the map is frozen and only `map → odom` changes. That's what navigation relies on.

**Do:**

1. Compare `slam_mapping.yaml` with `slam_localization.yaml` and list every difference.
2. Read why the plan uses slam_toolbox localisation and not AMCL fed back into the EKF.

**Done when:** You can explain each difference between the two configs.

**Explain it back:** *Kudriashov et al. found that feeding map-based corrections back into odometry hurt in repetitive spaces. Why might that happen?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [Macenski & Jambrecic 2021, SLAM Toolbox](https://doi.org/10.21105/joss.02783)

### 6.2 Run localisation

*Tags:* robot, build

**Why it matters.** Write the SLAM part of the navigation launch and check it on its own before Nav2 is added.

**Do:**

1. Start `localization_slam_toolbox_node` as a `LifecycleNode` with `map_file_name` pointing at your serialised map.
2. Place the robot on the home mark and start.

**Done when:** In Foxglove, live `/scan` points sit on the map's walls.

**Explain it back:** *Why does the robot need to start on the home mark (or be told where it is)?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

### 6.3 Set the start pose from Foxglove

*Tags:* robot

**Why it matters.** Lets you start anywhere, and is the tool for the next test.

**Do:**

1. In the 3D panel, use 'Publish pose estimate', which publishes to `/initialpose`.
2. Place the robot away from home, click its position and heading on the map.

**Done when:** Scan points snap onto the walls after you publish the pose.

**Explain it back:** *What would happen if you clicked the right position but the wrong heading?*

### 6.4 Wrong-start test

*Tags:* robot

**Why it matters.** Measures how forgiving localisation is: a direct answer to 'what if the robot isn't exactly on the tape?'.

**Do:**

1. Start the robot 10, 20, 30 cm and 5°, 10°, 15° off the home mark without telling it.
2. Push it around a little and see whether it converges.

**Done when:** A table of offsets that converged and ones that didn't.

**Explain it back:** *Why does a symmetric room make this harder?*

---

## Stage 7: Your Foxglove SLAM workspace

**Goal:** By the end you can watch and control the whole SLAM section from one saved Foxglove layout the team can open.

### 7.1 Write the trajectory recorder

*Tags:* build

**Why it matters.** slam_toolbox doesn't publish a path. Seeing the SLAM path and the odometry path side by side shows drift live, and the same node exports data for evaluation.

**Do:**

1. Implement `trajectory_recorder`: publish `/slam/path` from TF `map → base_footprint` and `/odom/path` from `/odometry/filtered`, adding a pose every 2 cm or 2°.
2. On shutdown, write both as TUM files when `tum_output_dir` is set.

**Done when:** Both paths show in Foxglove, and `evo_traj tum slam.txt odom.txt --plot` reads the files.

**Explain it back:** *When the two paths separate during a run, which one is wrong, and how do you know?*

**Read:** [evo trajectory evaluation](https://github.com/MichaelGrupp/evo)

### 7.2 Build and commit the layout

*Tags:* build

**Why it matters.** One shared layout means everyone sees the same thing and screenshots are consistent for the report.

**Do:**

1. 3D panel (frame `map`): `/map`, `/scan`, TF, robot model, `/slam_toolbox/graph_visualization`, both paths.
2. Plot panel: the three yaw rates from 4.2.
3. Export the layout to `docs/foxglove/slam_layout.json` and commit it.

**Done when:** A teammate can open the layout file and see the same view.

**Explain it back:** *Which panel would you look at first if the map started smearing, and why?*

### 7.3 Control SLAM from Foxglove

*Tags:* robot

**Why it matters.** Saving maps and pausing mapping without typing service calls over SSH.

**Do:**

1. Call Service panel: `/slam_toolbox/serialize_map`, `/slam_toolbox/save_map`, `/slam_toolbox/pause_new_measurements`.
2. Save a map from Foxglove and check the files appear on the Pi.

**Done when:** Map saved and serialised entirely from Foxglove.

**Explain it back:** *When would you pause new measurements during mapping?*

**Read:** [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox)

---

## Stage 8: Autonomous mapping

**Goal:** By the end the robot maps the room by itself and drives home, and you can compare that with mapping by hand.

> Starts once Nav2 reaches goals reliably (navigation section).

### 8.1 How frontier exploration works

*Tags:* learn

**Why it matters.** A frontier is the border between mapped free space and unknown space. The robot keeps driving to the best one until none are left.

**Do:**

1. Read the explore_lite README and its parameter list.
2. Find in `config/explore.yaml` what `min_frontier_size`, `progress_timeout` and `return_to_init` do.

**Done when:** You can predict what the robot will do first in your room.

**Explain it back:** *Why use Nav2's global costmap for frontiers rather than the raw `/map`?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.2 Build explore_lite

*Tags:* build, needs Nav2

**Why it matters.** It isn't in apt for Jazzy; it builds from the pinned source in `deps.repos`.

**Do:**

1. `vcs import` the pinned repo, then `colcon build --packages-select explore_lite_msgs explore_lite`.
2. Skip `multirobot_map_merge`; you don't need it.

**Done when:** `ros2 pkg executables explore_lite` lists `explore`.

**Explain it back:** *Why pin an exact commit rather than following the branch?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.3 Write explore.launch.py

*Tags:* build, needs Nav2

**Why it matters.** Combines mapping, Nav2 and the explorer in one supervised launch.

**Do:**

1. Base launch + slam_toolbox mapping (lifecycle, `map_update_interval: 2.0`) + Nav2 `navigation_launch.py` + the `explore` node with `explore.yaml`.
2. Keep `dry_run` defaulting to true like the other launches.

**Done when:** With `dry_run` on, frontiers appear on `/explore/frontiers` in Foxglove and Nav2 receives goals.

**Explain it back:** *explore_lite starts driving the moment it launches. How does your workflow keep that safe?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.4 First supervised run

*Tags:* robot, needs Nav2

**Why it matters.** The moment the robot maps on its own. Do it watched, with a hand near the kill switch.

**Do:**

1. Robot on home, someone at the motor switch. Launch, watch frontiers and the map grow.
2. Practise pausing: publish `false` to `/explore/resume` from Foxglove, then `true`.
3. Record a bag of the whole run.

**Done when:** Exploration completes, the robot returns home, and the map is saved.

**Explain it back:** *Where did the robot hesitate or turn back, and what was the frontier doing at that moment?*

**Read:** [explore_lite (m-explore-ros2)](https://github.com/robo-friends/m-explore-ros2)

### 8.5 Compare with manual mapping

*Tags:* bag, needs Nav2

**Why it matters.** Turns the demo into a result for the report.

**Do:**

1. Compare against your 5.4 map: time to finish, room dimensions vs tape, wall straightness.
2. Return-to-start error: the final pose against the home mark.

**Done when:** A comparison table in `docs/test_log.md`.

**Explain it back:** *Is the autonomous map better or worse, and is that because of the path the robot chose or because of SLAM?*

**Read:** [Filatov et al. 2017, 2D SLAM quality metrics](https://arxiv.org/abs/1708.02354)

---

## Stage 9: Evaluation

**Goal:** By the end you have honest numbers for how well your SLAM works, and a write-up that ties them to the papers.

> Later: only after parameters are frozen (5.5).

### 9.1 Survey floor checkpoints

*Tags:* robot

**Why it matters.** Your ground truth, with no camera needed: known positions measured with a tape.

**Do:**

1. Mark 5 crosses with heading lines around the room, including home and each seat.
2. Measure each from two walls; store them in `checkpoints.yaml`.

**Done when:** Each checkpoint measured twice, agreeing within 1 cm.

**Explain it back:** *Why measure from two walls rather than one?*

### 9.2 Record evaluation runs

*Tags:* robot, bag

**Why it matters.** Several physical runs, not one bag replayed, so results show real variation.

**Do:**

1. Five runs of the same route: stop at each checkpoint, publish its ID, end on home.
2. Keep the frozen config; note the commit hash per run.

**Done when:** Five bags with checkpoint markers, listed in `docs/test_log.md`.

**Explain it back:** *Why does replaying one bag five times measure something different from five physical runs?*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

### 9.3 Write the metrics script

*Tags:* build, bag

**Why it matters.** Turns bags into the numbers in your report.

**Do:**

1. Checkpoint error and return-to-start drift.
2. Repeatability: pairwise trajectory error between runs and map overlap (IoU), as in Kudriashov et al.
3. Use `evo` for alignment and trajectory error where it fits.

**Done when:** One command prints the metrics table for all five runs.

**Explain it back:** *What does low repeatability error tell you, and what doesn't it tell you?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [evo trajectory evaluation](https://github.com/MichaelGrupp/evo) · [Filatov et al. 2017, 2D SLAM quality metrics](https://arxiv.org/abs/1708.02354)

### 9.4 IMU ablation

*Tags:* bag

**Why it matters.** Answers 'is the gyro worth it?' with your own data.

**Do:**

1. Replay every run with two EKF configs: rf2o only, and rf2o plus gyro.
2. Measure error before SLAM (odometry alone) and after SLAM.

**Done when:** A table for both configs, before and after SLAM.

**Explain it back:** *Merrick & Nandikolla found better odometry barely changed the SLAM result. Did yours, and why might an encoder-free robot differ?*

**Read:** [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

### 9.5 Measure the Pi's load

*Tags:* robot

**Why it matters.** Running onboard a Pi 4 is a gap in the published work, so it's worth a number.

**Do:**

1. Log CPU and memory per node during mapping and localisation (for example with a small `psutil` logger).

**Done when:** Average and peak CPU and RAM recorded for each mode.

**Explain it back:** *Which node uses the most CPU, and does it matter at your speeds?*

**Read:** [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264)

### 9.6 Write the SLAM section

*Tags:* learn

**Why it matters.** Bring it together: what you built, why, what the numbers say, and what you'd do next.

**Do:**

1. Background (the review), design choices (cited), results tables, limitations.
2. Future work: deskewing, people filtering, lifelong mapping.

**Done when:** Every design decision in the write-up cites its source or says it's your own design.

**Explain it back:** *If you had one more week, which extension would you pick and why?*

**Read:** [Ran et al. 2025, 2D Lidar SLAM review](https://doi.org/10.3390/rs17071214) · [Kudriashov et al. 2026, AMCL-EKF benchmark](https://doi.org/10.3390/s26134264) · [Merrick & Nandikolla 2026, EKF odometry vs SLAM](https://doi.org/10.3390/s26175468)

---

## Stage X: Extensions

**Goal:** Optional. Each one builds on a finished core and adds a distinctive result.

> Pick at most one.

### X.1 Gyro-based scan deskewing

*Tags:* build, bag

**Why it matters.** At 5.5 Hz the robot rotates during a scan, which warps it. Correcting each point with the gyro should sharpen maps on turn-heavy routes.

**Do:**

1. Write a node that re-projects each point using the gyro's rotation at that point's time; feed the corrected scan to rf2o and slam_toolbox.
2. Compare no deskew vs gyro deskew on spin-heavy bags.

**Done when:** Before/after figure of a scan during a spin, and the heading error for each.

**Explain it back:** *Why is this effect worse on a slow lidar than a fast one?*

**Read:** [Salem et al. 2023, lidar de-skewing](https://arxiv.org/abs/2303.07312)

### X.2 People in the room

*Tags:* build, bag

**Why it matters.** A delivery robot works around people, who leave smears in maps.

**Do:**

1. Map with 0, 1 and 2 people walking; compare each map with the empty-room map.
2. Optionally filter detected legs out of the scan used by slam_toolbox only.

**Done when:** Map difference against the empty-room map for each condition.

**Explain it back:** *Why should the obstacle stop still use the raw scan, even if mapping uses the filtered one?*

**Read:** [Ye et al. 2021, mapping with a person tracker](https://doi.org/10.1109/ROBIO54168.2021.9739394)

### X.3 Map quality without ground truth

*Tags:* build

**Why it matters.** Adds objective map scores to the comparison tables.

**Do:**

1. Implement occupied-cell proportion, corner count and enclosed-area count on saved maps.

**Done when:** Scores computed for every saved map.

**Explain it back:** *Which metric best caught the bad maps you've seen?*

**Read:** [Filatov et al. 2017, 2D SLAM quality metrics](https://arxiv.org/abs/1708.02354)

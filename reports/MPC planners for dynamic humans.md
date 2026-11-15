# Keep RPP, add zones, measure MPPI

*Research synthesis, 2026-11-03, for CA3 RQ3 / E4. Sources: the four note files in `research_notes/MPC planners for dynamic humans/`, plus the repo's current `delivery_bot_bringup/config/nav2_params.yaml` and `docs/report_plan.md`. Anything marked "inference" is our own reasoning. It has not been measured on the robot, and under AGENTS.md rule 4 it must not be reported as a result.*

On a Raspberry Pi 4 that already runs slam_toolbox, the EKF and rf2o, **no MPC-style planner that predicts human motion has been shown to run, in any paper or package**. The strongest move for the CA3 deadline therefore goes in three tiers. First, keep Regulated Pure Pursuit (RPP) and add Nav2's own collision_monitor **Slowdown and Approach (time-to-collision) zones**. That is pure YAML and costs almost no CPU, and E4 should A/B it against the current stop-only wedge. Second, run a **compute-only bench** of Nav2 MPPI at reduced settings, and optionally of the new predictive `prox_mpc` plugin, with `motor_node` in dry run. That does not need motors and produces a real, citable Pi 4 number where the literature has none. Third, write **"MPPI or MPC with constant-velocity prediction of lidar-tracked legs"** up as future work. That design is backed by Schöller et al. (2020) and Poddar et al. (2023), who found that a constant-velocity model is as good as learned predictors for closed-loop MPC. TEB, hand-written acados/CasADi MPC, SICNav-style interactive MPC, DR-SPAAM and camera YOLO all fail at least one hard constraint: the Pi 4's CPU, the deadline, or the rule that our code stays thin. The most important finding for the report's safety story is a different one. The current 0.20 m stop wedge is smaller than the separation needed for a person stepping in at walking pace (inference below). That makes E4's step-in test a hazard-table result whichever controller runs.

## Nine candidates collapse to three that fit a loaded Pi 4

The Pi's budget is already spent. The EKF misses 20 Hz whenever the camera runs, and the local costmap updates at 5 Hz from a 7 Hz scan. Whatever is added must cost little, or must be measured before it is trusted. Against that limit, the Jazzy options sort cleanly ([ros2_mpc_packages notes](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml)).

| Rank | Option | Pi 4 fit | Effort before freeze | Handles moving people |
| --- | --- | --- | --- | --- |
| 1 | RPP (current) + collision_monitor **Slowdown + Approach** polygons | **Yes**: the node already runs | YAML only | Reactive: each scan is treated as static |
| 1b | RPP `use_cost_regulated_linear_velocity_scaling: true` (currently `false`) | Yes | One line | Reactive: slows near inflated cost |
| 2 | Vector Pursuit (`ros-jazzy-vector-pursuit-controller`) | **Yes**: 15 % of one A72 core per its README | apt + YAML | No prediction |
| 3 | Graceful / Rotation Shim | Yes (cheap control laws) | YAML | No prediction |
| 4 | **Nav2 MPPI, reduced** (binary already in Jazzy) | **Marginal, unmeasured** | YAML + a bench | Reacts to each costmap snapshot |
| 5 | DWB | Probably, at low sample counts | YAML | Reacts to each costmap snapshot |
| 6 | **prox_mpc** (SQP/ProxQP NMPC + its own lidar IMM tracker) | **Unknown**: x86 simulation only | apt + tracker node | **Yes: the only released Jazzy option that predicts** |
| 7 | TEB (`ros2-master`) | Likely no: g2o solve, source build of TEB and costmap_converter | Source build | Yes, given obstacle velocities |
| 8 | mpc_local_planner / own acados, CasADi, do-mpc node | No | High; breaks rule 2 | Only what we write |

Several facts settle the ranking. Nav2's collision_monitor in Jazzy already offers an **Approach model** that "using the current robot speed, estimate[s] the time to collision" and slows the robot to keep a minimum time margin. It also offers `VelocityPolygon` zones that switch with commanded speed ([collision_monitor README, Jazzy](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_collision_monitor/README.md)). Our config already publishes `collision_monitor_state`, which is what a bag-based metric needs. MPPI is the obvious "MPC" upgrade, but **Jazzy ships the older xtensor build**. The Eigen rewrite is **45–50 % faster**, and the maintainer estimated it would reach "20-30hz" on a Pi. It exists only in Kilted and Rolling and "will not be backported" ([ROS Discourse](https://discourse.openrobotics.org/t/nav2-speedups-in-mppi-smac-planner/41667); [Jazzy CMakeLists](https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_mppi_controller/CMakeLists.txt)). Humble arm64 MPPI binaries also crashed with **SIGILL on a Pi 4**. The build farm compiles for CPU features the Cortex-A72 lacks, and nobody has confirmed whether the Jazzy binary has the same fault ([navigation2 #4380](https://github.com/ros-navigation/navigation2/issues/4380)). Every published MPPI rate is for x86 or a Jetson: 50+ Hz on a 4th-gen i5 and 125 Hz on an i7-1365U ([Jazzy MPPI README](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_mppi_controller/README.md); [Discourse](https://discourse.openrobotics.org/t/nav2-speedups-in-mppi-smac-planner/41667)). None of its 13 critics models obstacle velocity, so **MPPI "avoids dynamic obstacles" only by re-reading the costmap every cycle** ([critics source](https://github.com/ros-navigation/navigation2/tree/jazzy/nav2_mppi_controller/src/critics)).

prox_mpc is the one released package that predicts. It is a Jazzy Nav2 NMPC plugin with its own 2D-lidar detector and a CV+CTRV IMM tracker. By the authors' own x86 benchmark it costs **0.30 ms p50 per cycle against MPPI's 3.11 ms**, and prediction cut its collisions from **32 % to 6 %** ([prox_mpc](https://github.com/simone-contorno/prox_mpc)). It is also five months old with six stars, has only the authors' own evaluation, and states "no physical-hardware validation yet". It earns a place as a bench measurement, not as the E4 controller. The same benchmark is a useful steelman for staying with RPP. **RPP had the fewest collisions (16 %) at almost the lowest cost**, behind MPPI at 18 %. That is weak evidence from one author in simulation, but it fits the view that a safety layer beats swapping controllers at 0.15 m/s.

## Constant-velocity prediction is the defensible upgrade path

The research case for prediction does not need heavy models. **Schöller et al. found that a constant-velocity model "can outperform even state-of-the-art neural models"**: ADE/FDE of 0.39/0.83 m on ETH/UCY at a 4.8 s horizon, against 0.54/1.15 m for SoPhie and 0.45/0.94 m for SR-LSTM ([arXiv 1903.07933](https://arxiv.org/abs/1903.07933)). Poddar et al. took this into closed loop on a real robot. **Replacing S-GAN with constant velocity inside an MPC did not change navigation safety or efficiency** ([arXiv 2303.01424](https://arxiv.org/abs/2303.01424)). The honest counterpoint is Aslam et al. (2025, preprint). A learned predictor helped in crowded scenes because its predictions were broader and more cautious, not because they were more accurate ([arXiv 2508.07079](https://arxiv.org/abs/2508.07079)). On a Pi, the cheap analogue is to inflate constant-velocity footprints as the horizon grows.

The heavier MPC-among-pedestrians line confirms that the budget, not the idea, is the limit. **SICNav runs its bilevel ORCA-in-MPC at 10 Hz on a desktop i7-9700K**. With three simulated humans it reached goals in 4.24 s, against 7.06 s for its own constant-velocity MPC baseline (MPC-CVMM) and 52.09 s for DWA, which froze 55 % of the time ([arXiv 2310.10982](https://arxiv.org/html/2310.10982v3)). MPC-CVMM is the realistic Pi-class design, and SICNav's numbers say it is far better than a DWA-style reactive planner but not collision-free at five humans. Brito et al.'s MPCC ran fully on board, but on a Jackal's PC, not a Pi ([arXiv 2010.10190](https://arxiv.org/pdf/2010.10190)). **No paper runs MPC or MPPI crowd navigation on a Raspberry Pi 4.** That gap is something the project can measure and report, rather than something to hide.

The perception half is the harder part on this hardware. **No maintained Jazzy leg detector exists.** `mowito/ros2_leg_detector` is a Foxy port that publishes people with velocities. It pins OpenCV 3.4.12 and was trained for 0.33° beams at 7.5–15 Hz ([ros2_leg_detector](https://github.com/mowito/ros2_leg_detector)). The A1M8 gives roughly 0.34–0.5° at 7 Hz with 26–29 % no-echo. DR-SPAAM manages only **9.7 FPS on a Jetson AGX GPU** ([arXiv 2004.14079](https://arxiv.org/pdf/2004.14079)), and YOLOv8n reaches **3.1 FPS on a Pi 4** for inference alone ([Q-engineering](https://github.com/Qengineering/YoloV8-ncnn-Raspberry-Pi-4)), so both are out. The Jazzy-native fallback is `ros-jazzy-laser-segmentation` with a segment-width gate ([docs](https://docs.ros.org/en/ros2_packages/jazzy/api/laser_segmentation)). Getting predictions into Nav2 then has two routes, because there is no Jazzy people or social costmap layer and no MPPI critic for tracked people. One is prox_mpc's packaged tracker. The other is publishing p + v·t points into the stock obstacle layer. **The second is glue that does prediction arithmetic, so it sits on the edge of rule 2.** Keep it as future work, or use prox_mpc so that the maths stays in a package.

A useful side link: a person walking behind the robot is one of the two remaining OI-8 suspects. A people mask on the scan that feeds rf2o, tested offline on existing bags once a detector runs, serves the localisation story as well as the planner one.

## The 0.20 m stop wedge cannot cover a step-in

The safety hook comes from speed-and-separation monitoring practice. The required protective separation adds up human motion during reaction and stopping, robot reaction distance, braking distance and a margin. When human speed is not monitored, the convention assumes **1.6 m/s** ([arXiv 1908.03046](https://arxiv.org/pdf/1908.03046), secondary). Inference, not measured: the reaction time is at least the scan period (0.14 s at 7 Hz) plus one 10 Hz control cycle, about 0.24 s. Even with zero robot braking time, a person stepping in at 1.6 m/s covers about **0.38 m**, roughly twice the current `stop` polygon's 0.20 m reach. Nor does any controller swap fix this: at v_max 0.15 m/s the human's term dominates the sum. That argues for three things. Report E4's measured stop distance next to the computed separation. Add a Slowdown ring of about 0.5 m and an Approach model with roughly 1.5–2 s `time_before_collision` (starting values to tune, not sourced defaults). And state plainly that collision_monitor on a Pi and a non-rated lidar is not an ISO 13849 safety function: the motor switch remains the kill switch (AGENTS.md rule 7). ISO 13482:2014 clauses 6.2 (robot stopping) and 6.4 (safety-related speed control) are the clause titles to cite ([ANSI preview](https://webstore.ansi.org/preview-pages/ISO/preview_ISO+13482-2014.pdf)). Normative numbers sit behind a paywall.

## A ranked plan that fits Tuesday-to-Saturday

| When | Step | Needs motors? | Output |
| --- | --- | --- | --- |
| Tue 3 – Wed 4 | **MPPI smoke test**: launch `controller_server` with MPPI on the Pi and look for a SIGILL | No | Pass/fail line in `docs/test_log.md` |
| Wed 4 – Thu 5 | **Compute bench** with `dry_run:=true`, robot stationary, goal sent: RPP vs MPPI-reduced (`controller_frequency` 10, `model_dt` 0.1, `time_steps` 30, `batch_size` 300–500, `vx_max` 0.15, `consider_footprint: false`, `visualize: false`), with slam_toolbox, the EKF and rf2o running and the camera off. Log `pidstat` on `controller_server`, `ros2 topic hz` on the controller output and the EKF, missed-rate warnings, and `vcgencmd get_throttled`. Optionally prox_mpc and its tracker on the same bench | No | **First Pi 4 MPPI loop-rate and CPU figures** (new evidence file) |
| Thu 5 | Write the Slowdown + Approach polygons as a second named config, `nav2_params_zones.yaml`. Freeze **both** configs before Fri 6 | No | Two frozen configs, one diff |
| Sat 7 | **E4-A/B**: RPP + stop-only vs RPP + stop/slowdown/approach, 5 paired runs each | **Yes** | E4 results (below) |
| Sat 7, only if the bench showed MPPI at 10 Hz with the EKF rate unchanged | Third condition MPPI-reduced + the same zones | Yes | Optional row |
| Report | Leg detection + constant-velocity prediction (prox_mpc, or a p + v·t costmap source), scan mask for rf2o/OI-8, Eigen MPPI after a distro move | — | Future-work section |

The bench in the first two rows is the cheapest way to add value. The progress checker aborts a stationary goal after `movement_time_allowance` (10 s), so either send repeated goals or raise the allowance in a bench-only copy of the params. Nav2's `controller_benchmark.cpp` times `computeVelocityCommands` offline with dummy inputs and gives a second, cleaner figure ([api.nav2.org](https://api.nav2.org/nav2-jazzy/html/controller__benchmark_8cpp_source.html)). If the motors are not driving by Saturday, the report plan's teleop fallback still exercises collision_monitor, because teleop `cmd_vel` passes through it. The zone A/B then survives without Nav2 tracking a path.

## E4-A/B: one factor, paired scripts, metrics from the bag

Change **one factor**: collision_monitor zones on or off, with the controller, costmap, inflation, velocity smoother and v_max held identical. The fairness rule comes from the evaluation literature ([Chhetri et al., arXiv 2510.22448](https://arxiv.org/html/2510.22448)). Changing the controller and the zones in one A/B would confound them. The protocol follows Pirk et al.'s scripted-scenario approach. They used **10 runs per scenario per location** with humans enacting short scenario cards ([arXiv 2204.05443](https://arxiv.org/pdf/2204.05443)). Tape a crossing lane and a step-in mark 0.6–0.8 m ahead of the path. Trigger walkers from taped lines, pace them with a metronome, and use the same people and lanes for both conditions. Order the runs ABBAABBAAB so battery, temperature and fatigue are spread across conditions. Film from a fixed tripod with a clap at bag start, and do one empty-room run per condition as the noise floor.

Record `/scan`, `/odometry/filtered`, `cmd_vel_smoothed` (the monitor's input) **and** `/cmd_vel` (its output), `collision_monitor_state`, `/plan`, `/tf` and `/rosout`. Write a `pidstat` CSV and the throttle state next to each bag. The metric set below adapts Francis et al.'s battery to a robot that cannot track people ([arXiv 2306.16740](https://arxiv.org/html/2306.16740v4)). Each distance-to-human metric becomes an explicit lidar proxy.

| Metric | Computed from | Note |
| --- | --- | --- |
| Success k/5, contacts (count) | Operator log, video | Write "0/5 contacts", never "safe" |
| Arrival error at seat and home | Tape to the mark | Compared with E1 and the empty-room baseline |
| Time to goal, path length | `/odometry/filtered` | OI-8 caveat on odometry scale |
| Minimum forward clearance | Min valid `/scan` range in a ±35° sector | **Proxy** for minimum distance to a human; includes walls, so also report it inside video-marked person windows |
| Clearance-band occupancy | % of time with forward min range < 0.45 m and < 1.2 m | Proxy for Francis et al.'s intimate and personal space compliance |
| Stalled time, failure to progress | \|v\| < 0.02 m/s with the goal not reached; no drop in distance to goal over 5 s | Report the thresholds (Francis M3) |
| Stop distance at step-in | Scan range when `/cmd_vel` reaches 0, checked on video stills | Set beside the computed separation |
| Monitor activity | Time and count in STOP / SLOWDOWN / APPROACH (`action_type` 1/2/3) | The message carries no TTC value ([msg docs](https://docs.ros.org/en/jazzy/p/nav2_msgs/msg/CollisionMonitorState.html)) |
| Override magnitude | `cmd_vel_smoothed` minus `/cmd_vel` | How much the safety layer overrode the controller |
| Smoothness | RMS acceleration and jerk of commanded and achieved velocity; cumulative heading change | HuNavSim definitions ([arXiv 2305.01303](https://arxiv.org/pdf/2305.01303)) |
| Compute | Median and p5 inter-message rate of the controller output against 10 Hz; missed-rate warnings; `controller_server` CPU %; EKF rate | The exact Jazzy warning text is unverified; check it on the Pi |

One script in `tools/analysis/` computes all of this. It needs a pytest on a synthetic trace with a known minimum range and a known stall interval, which meets the repo's definition of done. **Statistics are descriptive at n = 5.** Report every run as a strip plot, with the median, the range, the per-pair difference and Cliff's δ. A 5-vs-5 Mann-Whitney test bottoms out at p ≈ 0.008 and only with complete separation. A 5-pair Wilcoxon test **cannot reach 0.05** (its minimum is 0.0625). The Clopper-Pearson upper bound for 0 contacts in 5 runs is about 45 % (one-sided 95 %). Francis et al. suggest at least 30 real-robot samples for confirmatory claims, so call E4-A/B a pilot. Expect the trade-off HuNavSim showed in simulation: DWB passed people at 0.40 m and never stopped, while yielding planners kept 0.55–0.90 m and spent 1.0–1.8 s stopped ([arXiv 2305.01303](https://arxiv.org/pdf/2305.01303)). Zones should buy clearance and pay for it in stall time.

## Slide-ready takeaways

| Slide | Line |
| --- | --- |
| Problem | People are the obstacle that moves, and Nav2 sees them only as the latest costmap snapshot |
| Budget | No paper or package shows predictive MPC on a Pi 4; the published MPPI rates are x86 or Jetson (50–125 Hz) |
| Choice | Keep RPP and add time-to-collision and slowdown zones: zero new code, zero new compute |
| Evidence we add | First measured Nav2 MPPI loop rate and CPU on a loaded Pi 4 (bench, motors not needed) |
| Safety | A 0.20 m stop wedge covers less than one scan period of a person stepping in; the hardware switch stays the kill switch |
| Result framing | Pilot, n = 5 paired runs: medians, ranges, Cliff's δ, "0/5 contacts" |
| Future work | Leg tracking + constant-velocity prediction into MPC. Constant velocity matches learned predictors in closed loop (Poddar 2023, Schöller 2020) |

## References

Verification status: "Crossref" means the DOI resolved on 2026-11-03 and its metadata matched. "arXiv" means the abstract page was confirmed. "Unverified" means the reference came from memory or a secondary source, so check it before citing.

| # | Reference | ID | Status | Cite for |
| --- | --- | --- | --- | --- |
| 1 | Williams et al., "Aggressive driving with model predictive path integral control", ICRA 2016 | DOI 10.1109/ICRA.2016.7487277 | Crossref | MPPI origin (GPU) |
| 2 | Williams et al., "Information theoretic MPC for model-based RL", ICRA 2017 | DOI 10.1109/ICRA.2017.7989202 | Crossref | MPPI theory |
| 3 | Williams et al., "Information-Theoretic MPC: Theory and Applications to Autonomous Driving", T-RO 34(6) 2018 | DOI 10.1109/TRO.2018.2865891 | Crossref | Nav2 MPPI `gamma` |
| 4 | Macenski et al., "The Marathon 2: A Navigation System", IROS 2020 | DOI 10.1109/IROS45743.2020.9341207; arXiv 2003.00368 | Crossref | Nav2 |
| 5 | Macenski et al., "From the desks of ROS maintainers…", RAS 2023 | DOI 10.1016/j.robot.2023.104493; arXiv 2307.15236 | Crossref | Nav2 MPPI reacts to dynamic obstacles via the costmap |
| 6 | Macenski et al., "Regulated Pure Pursuit for Robot Path Tracking" | arXiv 2305.20026 | arXiv | RPP |
| 7 | Kim et al., "Smooth MPPI Control Without Smoothing", RA-L 7(4) 2022 | DOI 10.1109/LRA.2022.3192800 | Crossref | MPPI variant |
| 8 | Mohamed et al., "Log-MPPI Control Strategy", RA-L 2022 | DOI 10.1109/LRA.2022.3192772 | Crossref | MPPI variant |
| 9 | Rösmann et al., "Integrated online trajectory planning and optimization in distinctive topologies", RAS 88 2017 | DOI 10.1016/j.robot.2016.11.007 | Crossref | TEB |
| 10 | Brito et al., "MPCC for Collision Avoidance in Unstructured Dynamic Environments", RA-L 4(4) 2019 | DOI 10.1109/LRA.2019.2929976; arXiv 2010.10190 | Crossref | MPC with predicted obstacles, on board |
| 11 | Zeng, Zhang, Sreenath, "Safety-Critical MPC with Discrete-Time CBF", ACC 2021 | DOI 10.23919/ACC50511.2021.9483029; arXiv 2007.11718 | Crossref (metadata only) | MPC-CBF method |
| 12 | Jian et al., "Dynamic CBF-based MPC…", ICRA 2023 | DOI 10.1109/ICRA48891.2023.10160857 | Crossref (metadata only) | Moving-obstacle MPC-CBF |
| 13 | Zhu, Alonso-Mora, "Chance-Constrained Collision Avoidance for MAVs in Dynamic Environments", RA-L 4(2) 2019 | DOI 10.1109/LRA.2019.2893494 | Crossref | Chance-constrained MPC |
| 14 | de Groot et al., "Scenario-based motion planning with bounded probability of collision", IJRR 2025 | DOI 10.1177/02783649251315203; earlier arXiv 2103.12517 | Crossref | Scenario MPC among pedestrians |
| 15 | Samavi et al., "SICNav", T-RO 2025 | DOI 10.1109/TRO.2024.3484634; arXiv 2310.10982 | Crossref | Interactive MPC; desktop i7 at 10 Hz; MPC-CVMM baseline |
| 16 | Han et al., "DR-MPC: Deep Residual MPC for Real-World Social Navigation", RA-L 2025 | DOI 10.1109/LRA.2025.3546106; arXiv 2410.10646 | Crossref | MPC + RL residual (out of scope) |
| 17 | Schöller et al., "What the Constant Velocity Model Can Teach Us About Pedestrian Motion Prediction", RA-L 5(2) 2020 | DOI 10.1109/LRA.2020.2969925; arXiv 1903.07933 | Crossref | Constant velocity matches neural predictors |
| 18 | Poddar, Mavrogiannis, Srinivasa, "From Crowd Motion Prediction to Robot Navigation in Crowds", IROS 2023 | DOI 10.1109/IROS55552.2023.10341464; arXiv 2303.01424 | Crossref | Constant velocity = S-GAN in closed-loop MPC |
| 19 | Aslam et al., "MPC for Crowd Navigation via Learning-Based Trajectory Prediction" | arXiv 2508.07079 | arXiv, preprint | Counterpoint: caution beats accuracy |
| 20 | Trautman, Krause, "Unfreezing the robot", IROS 2010 | DOI 10.1109/IROS.2010.5654369 | Crossref | Freezing-robot problem |
| 21 | Chen et al., "Crowd-Robot Interaction" (SARL), ICRA 2019 | DOI 10.1109/ICRA.2019.8794134; arXiv 1809.08835 | Crossref | RL baseline |
| 22 | Fox, Burgard, Thrun, "The dynamic window approach…", IEEE RAM 4(1) 1997 | DOI 10.1109/100.580977 | Crossref | DWA/DWB |
| 23 | Mavrogiannis et al., "Core Challenges of Social Robot Navigation: A Survey", ACM THRI 12(3) 2023 | DOI 10.1145/3583741; arXiv 2103.05668 | Crossref | Problem framing |
| 24 | Alahi et al., "Social LSTM", CVPR 2016 | DOI 10.1109/CVPR.2016.110 | Crossref | Learned-predictor reference |
| 25 | Francis et al., "Principles and Guidelines for Evaluating Social Robot Navigation Algorithms", ACM THRI 14(2) 2025 | DOI 10.1145/3700599; arXiv 2306.16740 | arXiv + DOI from the paper page | Metric battery, thresholds, ≥ 30 samples |
| 26 | Pérez-Higueras et al., "HuNavSim", RA-L 2023 | arXiv 2305.01303 | arXiv (DOI not checked) | Metric formulas; clearance vs stall trade-off |
| 27 | Pirk et al., "A Protocol for Validating Social Navigation Policies" | arXiv 2204.05443 | arXiv | Scripted scenarios, 10 runs each |
| 28 | Gao, Huang, "Evaluation of Socially-Aware Robot Navigation", Front. Robot. AI 2022 | DOI 10.3389/frobt.2021.721317 | PMC page read | Evaluation taxonomy |
| 29 | Chhetri et al., "A short methodological review on social robot navigation benchmarking" | arXiv 2510.22448 | arXiv, preprint | Report the full configuration |
| 30 | Jia et al., "DR-SPAAM" | arXiv 2004.14079 | arXiv | 2D lidar person detection cost |
| 31 | Mavrogiannis et al., "Winding Through" | arXiv 2109.05084 | DOI **unverified** | Constant-velocity MPC, real robot |
| 32 | Kästner et al., "Arena-Bench" | arXiv 2206.05728 | DOI **unverified** | Dynamic-environment benchmark |
| 33 | Ye et al., ROBIO 2021 (RQ3 anchor [Y21]) | arXiv 2204.08163 | **Unverified** in this research pass; check `report/literature_notes.md` | People degrade SLAM |
| 34 | ISO 13482:2014; ISO 3691-4:2023 | Standards | Clause titles only (paywalled) | Hazard table |
| 35 | Nav2 collision_monitor, MPPI READMEs (Jazzy); navigation2 #4380; MPPI speedups post; prox_mpc README | URLs inline above | Read 2026-11-03 | Package facts |

## Conclusion

The question changes from "which MPC predicts people best" to "what can a loaded Pi 4 prove by Saturday", and the answers sit at different layers. Prediction is a perception problem first: no Jazzy leg detector exists, and the A1M8's resolution sits outside what the classical detectors were trained on. Control is a compute problem: MPPI is unmeasured on a Pi 4, and Jazzy carries the slow build. Safety is a geometry problem: a 0.20 m wedge against a person moving at 1.6 m/s. Only the geometry can be fixed before the freeze, and fixing it needs no new code.

That gives the report a stronger RQ3 story than a controller shoot-out would. E4 measures how people degrade the system, and the zone A/B shows the cheapest mitigation working or not working. The compute bench supplies a Pi 4 figure the literature lacks, which turns "MPPI with constant-velocity prediction" from a wish into a costed piece of future work. If the bench shows MPPI cannot hold 10 Hz beside slam_toolbox and the EKF, that is itself the finding: on a low-cost robot, the planner is limited by the localisation stack sharing its CPU, not by the planner's own design.

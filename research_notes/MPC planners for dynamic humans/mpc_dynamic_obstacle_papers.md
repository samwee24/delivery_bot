# MPC-based local planning for mobile robots among moving humans

Compiled 2026-11-03 for the CA3 report (RQ3, future-work / add-on section). Hard constraint from the user: compute is a Raspberry Pi 4 CPU only (no GPU, no offboard compute). Each entry is tagged **Pi4?** with a plausibility judgement. These tags are my inferences from the reported hardware, not measured results.

Verification method: DOIs were resolved against the Crossref API (`https://api.crossref.org/works/<DOI>`) on 2026-11-03. Title, venue, year and first authors matched the entries below. The arXiv API was rate-limited, so arXiv ids are confirmed through the arXiv abstract pages or search results where noted.

## Key Question 1: Foundational MPPI and Nav2 MPPI papers

### Takeaway
MPPI is the Williams et al. line (ICRA 2016, ICRA 2017, T-RO 2018). Nav2's MPPI controller cites the ICRA 2016 paper and the T-RO 2018 paper. The citable Nav2 papers are Macenski et al. IROS 2020 and the RAS 2023 survey. Nav2 reports CPU performance on x86 (50+ Hz on a 4th-gen i5, using AVX2 vectorisation). I found **no published Raspberry Pi 4 / ARM Cortex-A72 benchmark** for Nav2 MPPI.

### Cited Findings
- **Williams, Drews, Goldfain, Rehg, Theodorou, "Aggressive driving with model predictive path integral control", ICRA 2016. DOI 10.1109/ICRA.2016.7487277** (verified, Crossref). This is the original sampling-based MPPI paper and the one the Nav2 MPPI README cites as "the MPPI algorithm". — [Crossref](https://api.crossref.org/works/10.1109/ICRA.2016.7487277); [Nav2 MPPI README](https://github.com/ros-navigation/navigation2/blob/main/nav2_mppi_controller/README.md). **Pi4?** The original work used a GPU to sample thousands of rollouts. No (as published).
- **Williams, Wagener, Goldfain, Drews, Rehg, Boots, Theodorou, "Information theoretic MPC for model-based reinforcement learning", ICRA 2017. DOI 10.1109/ICRA.2017.7989202** (verified). — [Crossref](https://api.crossref.org/works/10.1109/ICRA.2017.7989202)
- **Williams, Drews, Goldfain, Rehg, Theodorou, "Information-Theoretic Model Predictive Control: Theory and Applications to Autonomous Driving", IEEE T-RO 34(6), 2018. DOI 10.1109/TRO.2018.2865891** (verified). The Nav2 docs cite Section 3D-2 of this paper for the `gamma` parameter. — [Crossref](https://api.crossref.org/works/10.1109/TRO.2018.2865891); [Nav2 MPPI README](https://github.com/ros-navigation/navigation2/blob/main/nav2_mppi_controller/README.md)
- **Macenski, Martín, White, Ginés Clavero, "The Marathon 2: A Navigation System", IROS 2020. DOI 10.1109/IROS45743.2020.9341207, arXiv 2003.00368** (DOI verified). This is the canonical Nav2 citation. — [Crossref](https://api.crossref.org/works/10.1109/IROS45743.2020.9341207)
- **Macenski, Moore, Lu, Merzlyakov, Ferguson, "From the desks of ROS maintainers: A survey of modern & capable mobile robotics algorithms in the robot operating system 2", Robotics and Autonomous Systems, Oct 2023. DOI 10.1016/j.robot.2023.104493, arXiv 2307.15236** (DOI verified). This survey covers the Nav2-era algorithms, including the MPPI controller, and is the best peer-reviewed citation for "Nav2 MPPI". — [Crossref](https://api.crossref.org/works/10.1016/j.robot.2023.104493)
- Nav2 MPPI facts from the README:
  - It is "measured to run at 50+ Hz on a modest Intel processor (4th gen i5)".
  - It relies on "CPU vectorization through AVX2 and MFMA".
  - Defaults: `batch_size` 1000, `time_steps` 56, `model_dt` 0.05 s, `iteration_count` 1.
  - It has a `DiffDriveMotionModel`.
  - Critics: ObstaclesCritic, CostCritic, PathAlignCritic, PathFollowCritic, GoalCritic, PreferForwardCritic and others.
  - Dynamic obstacles are handled only implicitly through the costmap. Lowering the path-align weight lets the robot "deviate from the path to get around dynamic obstacles". There is no explicit prediction of moving obstacles.
  — [Nav2 MPPI README](https://github.com/ros-navigation/navigation2/blob/main/nav2_mppi_controller/README.md)
- The Nav2 maintainers report about 45–50 % speed-up from moving xtensor to Eigen, "125hz average on i7-1365U" on CPU only, and 55–60 Hz on NVIDIA Jetson Orin (a user report from Kiwibot). — [ROS Discourse: Nav2 speedups in MPPI & Smac](https://discourse.openrobotics.org/t/nav2-speedups-in-mppi-smac-planner/41667)
- ROSCon 2023 talk "On Use of Nav2 MPPI Controller" (slides; not peer-reviewed). — [ROSCon 2023 PDF](https://roscon.ros.org/2023/talks/On_Use_of_Nav2_MPPI_Controller.pdf)
- MPPI variants relevant to smoothness and cluttered scenes:
  - **Kim, Park, Kwak, Bae, "Smooth Model Predictive Path Integral Control Without Smoothing", IEEE RA-L 7(4), 2022. DOI 10.1109/LRA.2022.3192800** (verified). Nav2 MPPI's smoothing ideas trace back to this line of work, though I did not confirm that link in the Nav2 docs. — [Crossref search result](https://api.crossref.org/works/10.1109/LRA.2022.3192800)
  - **Mohamed, Yin, Liu, "Autonomous Navigation of AGVs in Unknown Cluttered Environments: Log-MPPI Control Strategy", IEEE RA-L, Oct 2022. DOI 10.1109/LRA.2022.3192772** (verified). — [Crossref](https://api.crossref.org/works/10.1109/LRA.2022.3192772)

### Inferences
- Nav2 MPPI on a Pi 4 is **plausible but unproven**. The Cortex-A72 has NEON, not AVX2. The 50+ Hz figure is for x86. With the defaults (1000 × 56 rollouts) the Pi will likely run well below 50 Hz.
- At 0.15 m/s, a 10–20 Hz controller is likely enough. Reducing `batch_size` (for example 300–500) and `time_steps` is the obvious lever. The team must measure this on the Pi before claiming it (AGENTS.md rule 4).
- Plain Nav2 MPPI treats people as costmap obstacles at their current position. "MPPI + human-motion prediction" would therefore need either a custom critic or a costmap layer that inflates predicted positions. That is new code, so it needs a scope check against AGENTS.md rule 2.

### Gaps
- No peer-reviewed or community benchmark of Nav2 MPPI on a Raspberry Pi 4 was found.
- I did not find a stand-alone peer-reviewed paper devoted only to Nav2 MPPI. The RAS 2023 survey is the closest. I did not re-read its MPPI section this session.

## Key Question 2: MPC with dynamic obstacles / human motion prediction

### Takeaway
The main MPC-among-pedestrians line is:
- TEB (Rösmann)
- MPCC with predicted obstacles (Brito et al., RA-L 2019)
- MPC with control barrier functions (Zeng et al., ACC 2021; dynamic-CBF MPC, ICRA 2023)
- chance-constrained and scenario MPC (Zhu & Alonso-Mora 2019; de Groot et al., IJRR 2025)
- interactive bilevel MPC (SICNav, T-RO 2025)
- MPC + RL residual (DR-MPC, RA-L 2025)

Most of these run on desktop-class CPUs (i7). None that I found run on a Pi 4.

### Cited Findings
- **Rösmann, Hoffmann, Bertram, "Integrated online trajectory planning and optimization in distinctive topologies", Robotics and Autonomous Systems 88, Feb 2017. DOI 10.1016/j.robot.2016.11.007** (verified). This is the TEB paper with parallel topologies, i.e. the `teb_local_planner`. — [Crossref](https://api.crossref.org/works/10.1016/j.robot.2016.11.007). **Pi4?** Probably feasible for a single topology on a small costmap, but unmeasured. Note: TEB is not ported to ROS 2 Jazzy in Nav2 core (not verified this session).
- **Brito, Floor, Ferranti, Alonso-Mora, "Model Predictive Contouring Control for Collision Avoidance in Unstructured Dynamic Environments", IEEE RA-L 4(4), 2019. DOI 10.1109/LRA.2019.2929976, arXiv 2010.10190** (DOI verified). It runs fully on board a Clearpath Jackal: localisation, perception, planning and control. It is compared with state-of-the-art planners in static and dynamic scenes. — [Crossref](https://api.crossref.org/works/10.1109/LRA.2019.2929976); [arXiv 2010.10190](https://arxiv.org/pdf/2010.10190). **Pi4?** It uses a nonlinear solver on the Jackal's onboard PC (not a Pi). Uncertain.
- **Zeng, Zhang, Sreenath, "Safety-Critical Model Predictive Control with Discrete-Time Control Barrier Function", ACC 2021. DOI 10.23919/ACC50511.2021.9483029, arXiv 2007.11718** (DOI verified). This is the MPC-CBF formulation. — [Crossref](https://api.crossref.org/works/10.23919/ACC50511.2021.9483029)
- **Jian, Yan, Lei, Lu, et al., "Dynamic Control Barrier Function-based Model Predictive Control to Safety-Critical Obstacle-Avoidance of Mobile Robot", ICRA 2023. DOI 10.1109/ICRA48891.2023.10160857** (verified). This extends MPC-CBF to moving obstacles. — [Crossref search](https://api.crossref.org/works/10.1109/ICRA48891.2023.10160857)
- **Zhu, Alonso-Mora, "Chance-Constrained Collision Avoidance for MAVs in Dynamic Environments", IEEE RA-L 4(2), 2019. DOI 10.1109/LRA.2019.2893494** (verified). This is chance-constrained MPC with uncertain obstacle motion. It targets aerial robots, but the method is the standard citation. — [Crossref](https://api.crossref.org/works/10.1109/LRA.2019.2893494)
- **de Groot, Ferranti, Gavrila, Alonso-Mora, "Scenario-based motion planning with bounded probability of collision", IJRR, 2025. DOI 10.1177/02783649251315203** (verified). This is scenario MPC among pedestrians with probabilistic safety. An earlier version is "Scenario-Based Trajectory Optimization in Uncertain Dynamic Environments" (arXiv 2103.12517), which compared against MPCC and CADRL with pedestrians in Jackal Gazebo simulation. — [Crossref](https://api.crossref.org/works/10.1177/02783649251315203); [arXiv 2103.12517](https://arxiv.org/pdf/2103.12517)
- **Samavi, Han, Shkurti, Schoellig, "SICNav: Safe and Interactive Crowd Navigation Using Model Predictive Control and Bilevel Optimization", IEEE T-RO, 2025. DOI 10.1109/TRO.2024.3484634, arXiv 2310.10982** (verified).
  - Method: humans are modelled as ORCA agents inside a bilevel nonlinear MPC (KKT reformulation), solved with Acados-generated C++.
  - Compute: runs at **10 Hz, 2 s horizon, on an Intel i7-9700K desktop**, on a Clearpath Jackal with VICON.
  - Simulation, 3 ORCA humans, 500 scenarios: SICNav success 1.00, time 4.24 s, collisions 0.00. MPC-CVMM (constant-velocity MPC) 7.06 s. ORCA 10.26 s. SARL 27.21 s, with 0.26 freezing. DWA 52.09 s, with 0.55 freezing.
  - Simulation, 5 humans: MPC-CVMM had 0.05 collision frequency.
  - Real robot: 80 runs with 1–3 humans against MPC-CVMM.
  — [Crossref](https://api.crossref.org/works/10.1109/TRO.2024.3484634); [arXiv HTML](https://arxiv.org/html/2310.10982v3). **Pi4?** No (needs a desktop-class i7 for 10 Hz).
- **Han, Thomas, Zhang, Rhinehart, et al., "DR-MPC: Deep Residual Model Predictive Control for Real-World Social Navigation", IEEE RA-L, Apr 2025. DOI 10.1109/LRA.2025.3546106, arXiv 2410.10646** (verified). MPC path tracking is augmented with a residual DRL policy learned from fewer than 4 h of real-world data. An out-of-distribution safety component steers the robot away from likely collisions. It reports "few errors" in real crowds; the abstract gives no numbers. — [Crossref](https://api.crossref.org/works/10.1109/LRA.2025.3546106); [arXiv](https://arxiv.org/abs/2410.10646). **Pi4?** Inference plausibly could run a small policy, but training needs a desktop or GPU. Out of scope.
- **Mavrogiannis et al., "Winding Through: Crowd Navigation via Topological Invariance", arXiv 2109.05084** (published in RA-L 2023 per my recollection; DOI not verified). It uses MPC with a **constant-velocity human model** and was tested on a self-balancing robot. — [arXiv 2109.05084](https://arxiv.org/pdf/2109.05084)
- **Trautman, Krause, "Unfreezing the robot: Navigation in dense, interacting crowds", IROS 2010. DOI 10.1109/IROS.2010.5654369** (verified). This is the classic statement of the "freezing robot problem": independent prediction makes the planner see no safe path. — [Crossref](https://api.crossref.org/works/10.1109/IROS.2010.5654369)

### Inferences
- For a Pi 4, a full NMPC with pedestrian constraints (SICNav, MPCC, scenario MPC) is unlikely at useful rates without code generation (Acados), a short horizon and few humans. The easiest extension is Nav2 MPPI plus constant-velocity extrapolation of tracked people.
- SICNav's own MPC-CVMM baseline is the realistic Pi-class option. It is far better than DWA (7.06 s vs 52.09 s, 3 humans) but shows some collisions at 5 humans. That is a good quantitative argument for "MPC + CV prediction" as future work.

### Gaps
- I could not open the full Brito et al. text, so its solve time, rates and baseline numbers are not extracted.
- I did not re-read the Zeng et al. and Jian et al. contents this session. Only their metadata is verified, so cite them for the method, not for numbers.

## Key Question 3: Classic vs learning planners in crowds; constant-velocity prediction is competitive

### Takeaway
Two strong results show that a simple constant-velocity (CV) model is hard to beat:
- Schöller et al. (RA-L 2020): CV beats state-of-the-art neural predictors on open-loop prediction.
- Poddar et al. (IROS 2023): on a real robot, replacing S-GAN with CV inside an MPC did **not** change navigation safety or efficiency.

This directly justifies a CPU-only "MPC + CV prediction" design on the Pi.

### Cited Findings
- **Schöller, Aravantinos, Lay, Knoll, "What the Constant Velocity Model Can Teach Us About Pedestrian Motion Prediction", IEEE RA-L 5(2), Apr 2020. DOI 10.1109/LRA.2020.2969925, arXiv 1903.07933** (verified). The paper finds that "a simple Constant Velocity Model can outperform even state-of-the-art neural models". The networks learn environmental priors that hurt generalisation. The authors argue that motion history beyond the current velocity adds little and that pedestrian interactions are too complex to predict well. — [Crossref](https://api.crossref.org/works/10.1109/LRA.2020.2969925); [arXiv](https://arxiv.org/abs/1903.07933). **Pi4?** Yes, trivially (O(n) arithmetic per person).
- **Poddar, Mavrogiannis, Srinivasa, "From Crowd Motion Prediction to Robot Navigation in Crowds", IROS 2023. DOI 10.1109/IROS55552.2023.10341464, arXiv 2303.01424** (verified). S-GAN is plugged into an MPC on a self-balancing robot in a lab with varied crowd behaviours, and judged on safety and efficiency. S-GAN's accuracy transfers to the real world, but **the MPC performs the same with a constant-velocity model**. The authors conclude that "substantial model improvements might be needed" before crowd-navigation gains appear. — [arXiv](https://arxiv.org/abs/2303.01424); [Crossref search result](https://api.crossref.org/works/10.1109/IROS55552.2023.10341464). **Pi4?** The CV+MPC configuration is plausible; S-GAN would need more compute.
- **Aslam, Derajic, Bouzidi, Bernhard, Ringert, "Model Predictive Control for Crowd Navigation via Learning-Based Trajectory Prediction", arXiv 2508.07079 (Aug 2025, preprint, not peer-reviewed).** The paper puts a Social-Implicit predictor inside MPC and compares it with CV on the Continental Corriere robot. The predictor reduces open-loop prediction error by up to 76 % vs CV in low density. Open-loop metrics do not fully predict closed-loop performance: the learned predictor gives broader, more cautious predictions, which improve safety and smoothness in crowded scenes. — [arXiv](https://arxiv.org/abs/2508.07079). This partly qualifies Poddar et al.: a learned predictor can help in closed loop, but by changing caution, not accuracy.
- **Chen, Liu, Kreiss, Alahi, "Crowd-Robot Interaction: Crowd-Aware Robot Navigation With Attention-Based Deep Reinforcement Learning" (SARL / CrowdNav), ICRA 2019. DOI 10.1109/ICRA.2019.8794134, arXiv 1809.08835** (DOI verified). This is the standard RL crowd-navigation baseline. In SICNav's simulation SARL took 27.21 s with 0.26 freezing, against 4.24 s for SICNav. — [Crossref](https://api.crossref.org/works/10.1109/ICRA.2019.8794134); [SICNav arXiv HTML](https://arxiv.org/html/2310.10982v3)
- **Fox, Burgard, Thrun, "The dynamic window approach to collision avoidance", IEEE RA Magazine 4(1), 1997. DOI 10.1109/100.580977** (verified). This is the DWA baseline (Nav2's DWB descends from it). In SICNav's simulation DWA froze 0.55 of the time with 3 humans. — [Crossref](https://api.crossref.org/works/10.1109/100.580977); [SICNav arXiv HTML](https://arxiv.org/html/2310.10982v3)
- **Kästner et al., "Arena-Bench: A Benchmarking Suite for Obstacle Avoidance Approaches in Highly Dynamic Environments", arXiv 2206.05728** (RA-L 2022 per my recollection; DOI not verified). It benchmarks TEB, DWA, MPC, CADRL and DRL planners in dynamic simulated environments (arena-rosnav). — [arXiv](https://arxiv.org/pdf/2206.05728). I did not extract result tables.
- Dynamic Gap (arXiv 2210.05022, venue not verified): in its structured setting TEB reached 80 % and Dynamic Gap 88 % success. MPC and DWA "stalled out" in thin entryways between rooms. — [arXiv](https://arxiv.org/pdf/2210.05022)
- **Mavrogiannis, Baldini, Wang, Zhao, Trautman, Steinfeld, Oh, "Core Challenges of Social Robot Navigation: A Survey", ACM THRI 12(3), 2023. DOI 10.1145/3583741, arXiv 2103.05668** (verified). This is the survey to cite for the problem framing. — [Crossref](https://api.crossref.org/works/10.1145/3583741)
- **Alahi et al., "Social LSTM: Human Trajectory Prediction in Crowded Spaces", CVPR 2016. DOI 10.1109/CVPR.2016.110** (verified). This is the canonical learned predictor that CV is compared against. — [Crossref](https://api.crossref.org/works/10.1109/CVPR.2016.110). **Pi4?** Possible for a few agents with a small network, but unnecessary given Schöller et al.

### Inferences
- The defensible chain for the report:
  1. People degrade the system (RQ3, anchored on Ye et al.).
  2. Nav2 MPPI offers smooth reactive avoidance on CPU.
  3. CV prediction is as good as learned prediction for closed-loop MPC (Poddar et al.; Schöller et al.).
  4. So "MPPI + CV-extrapolated people" is the low-compute upgrade.
  5. Learned or interactive prediction (SICNav, DR-MPC) needs a desktop and is out of scope on a Pi 4.
- Aslam et al. is the honest counterpoint: prediction *uncertainty width* may matter more than accuracy. A cheap analogue on the Pi is to inflate CV-predicted footprints with time.

### Gaps
- Arena-Bench numeric results were not extracted.
- The Winding Through and Arena-Bench DOIs are not verified. Cite them by arXiv id only unless they are checked.

## Key Question 4: Low-cost / embedded (Raspberry Pi, Jetson) MPC navigation with people

### Takeaway
I found **no peer-reviewed paper** running MPC or MPPI crowd navigation on a Raspberry Pi 4. The closest data points are:
- Nav2 MPPI at 125 Hz on an i7-1365U, 50+ Hz on a 4th-gen i5, and 55–60 Hz on a Jetson Orin (maintainer reports).
- SICNav at 10 Hz on an i7-9700K.

Pi 4 feasibility is therefore an open question the team would have to measure. That gap can itself be stated as a contribution or future work.

### Cited Findings
- Nav2 MPPI: 50+ Hz on a 4th-gen i5 (AVX2) — [Nav2 MPPI README](https://github.com/ros-navigation/navigation2/blob/main/nav2_mppi_controller/README.md). 125 Hz average on an i7-1365U, and 55–60 Hz on a Jetson Orin — [ROS Discourse](https://discourse.openrobotics.org/t/nav2-speedups-in-mppi-smac-planner/41667).
- SICNav: 10 Hz on an i7-9700K with Acados codegen — [arXiv HTML](https://arxiv.org/html/2310.10982v3).
- Brito et al. MPCC ran fully onboard a Clearpath Jackal (onboard PC, not a Pi) — [arXiv 2010.10190](https://arxiv.org/pdf/2010.10190).
- A search for "Nav2 MPPI Raspberry Pi 4" turned up no benchmark — [docs.ros.org nav2_mppi_controller (Jazzy)](https://docs.ros.org/en/jazzy/p/nav2_mppi_controller).

### Inferences
- A Pi 4 (4× Cortex-A72 at 1.5–1.8 GHz, NEON) is roughly an order of magnitude slower than an i7-1365U on vectorised float work. This is my estimate, not sourced.
- Scaling naively from about 125 Hz with defaults, the Pi 4 might reach about 10–20 Hz with defaults, and more with a reduced `batch_size`. This is speculative. It must be measured (`ros2 topic hz /cmd_vel` with the controller's `controller_frequency`, plus Nav2's "Control loop missed its desired rate" warnings) before being stated.
- The Pi is already CPU-bound: the EKF misses its 20 Hz rate with the camera on, per AGENTS.md. Any MPPI add-on competes with slam_toolbox localisation and rf2o for CPU. That is a concrete risk to name.

### Gaps
- No Raspberry Pi MPC/MPPI crowd-navigation paper was found within my search budget (about 15 calls). A dedicated search for "embedded MPC ARM Cortex-A acados mobile robot" was not run.
- Not verified this session: **Ye et al., ROBIO 2021, arXiv 2204.08163** (the RQ3 anchor) and **Helbing & Molnár, "Social force model for pedestrian dynamics", Phys. Rev. E 51, 1995 (DOI 10.1103/PhysRevE.51.4282 from memory, UNVERIFIED)**.

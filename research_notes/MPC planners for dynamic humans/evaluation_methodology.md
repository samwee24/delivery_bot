# Evaluation methodology for an RPP vs MPPI A/B test among people (CA3 E4)

Scope: how to compare Nav2 Regulated Pure Pursuit (RPP) with Nav2 MPPI, with and without collision_monitor slowdown/approach zones, on a Raspberry Pi 4 robot at 0.15 m/s in a small room, using about 5 runs per condition and one week. **Hard constraint from the user (via coordinator):** hardware and compute are fixed (Pi 4 CPU only), there is no motion capture or external tracking, and every metric has to come from rosbag2 data the robot already records (`/scan`, `/odometry/filtered`, `/cmd_vel`, `collision_monitor_state`) plus a tape measure and phone video. CPU load and controller loop rate count as A/B metrics. State as of 2026-11-03. Items marked **[unverified]** come from memory or secondary sources and were not checked against a primary source.

## Standard social/dynamic navigation metrics (and which ones survive the no-tracking constraint)

### Takeaway
The literature agrees on a core set: success, collisions, time to goal, path length, minimum distance to humans, personal-space compliance, time stalled or failure to progress, velocity/acceleration/jerk, and minimum TTC. Francis et al. (2025) is the citable umbrella reference and HuNavSim gives the most complete metric table with formulas. Without human tracking, distance-to-human metrics have to be approximated with distance to the nearest lidar return (or a phone-video/tape check), and the report should say plainly that this is a proxy.

### Cited Findings
- Francis et al., "Principles and Guidelines for Evaluating Social Robot Navigation Algorithms", ACM THRI 14(2), art. 34, 2025, DOI 10.1145/3700599, arXiv:2306.16740. It sets out eight principles: safety, comfort, legibility, politeness, social competency, agent understanding, proactivity and contextual appropriateness — [arXiv](https://arxiv.org/abs/2306.16740), [MIT DSpace](https://dspace.mit.edu/handle/1721.1/158075)
- Francis et al. metric table, navigation tranche: Success / Success Rate; collisions split into wall, agent and human collisions (collision rate = average over episodes); Timeout; Failure to Progress (distance to goal does not drop over a window); Stalled Time (speed below a threshold); Time to Goal; Path Length; SPL — [arXiv:2306.16740v4 HTML](https://arxiv.org/html/2306.16740v4)
- Francis et al., quality/social tranche: velocity, acceleration and jerk (min/avg/max); Clearing Distance to obstacles (min/max); Space Compliance (fraction of the trajectory within a distance threshold of a human; with 0.5 m it is called Personal Space Compliance); Minimum Distance to Human; Minimum Time-to-Collision with a human, assuming linear motion — [arXiv:2306.16740v4 HTML](https://arxiv.org/html/2306.16740v4)
- Francis et al. guideline M3: many metrics depend on thresholds (distance, time, speed), and the thresholds and context have to be reported with the result. Guideline M8: report a battery of metrics plus distributions or histograms, because outliers matter for safety — [arXiv:2306.16740v4 HTML](https://arxiv.org/html/2306.16740v4)
- Francis et al. quote proxemic distances of 0.45 m (intimate) and 1.2 m (personal), and list comfort factors: keeping distance, not cutting people off, natural motion, and avoiding jitter or unacceptable speed — [arXiv:2306.16740v4 HTML](https://arxiv.org/html/2306.16740v4)
- HuNavSim (Pérez-Higueras et al., IEEE RA-L 2023, arXiv:2305.01303), Table I, 28 metrics including: time to reach goal; path length; cumulative heading changes (rad); average distance to closest person; minimum distance to people; % time in intimate/personal/social space; completed; minimum and final distance to target; robot-on-person and person-on-robot collisions; **time not moving** (s); average linear and angular speed, acceleration and jerk; social-force/social-work terms. Formulas are in the HuNavEvaluator GitHub page — [arXiv PDF](https://arxiv.org/pdf/2305.01303)
- HuNavSim worked example (simulation) comparing DWB with two social planners. Passing scenario: min distance to people 0.40 m (DWB) vs 0.90 / 0.55 m; intimate-space intrusion 3.66 % vs 0 / 0; time not moving 0.00 s vs 1.04 / 1.78 s. Crossing scenario: cumulative heading change 2.15 rad (DWB) vs 6.68 / 2.03. The yielding planner "spends more time stopped". The trade-off between clearance and stopping is what an RPP/MPPI comparison will likely show too — [arXiv PDF](https://arxiv.org/pdf/2305.01303)
- SocNavBench (Biswas et al., arXiv:2103.00047) defines path irregularity as the average absolute angle between the robot heading and the goal direction, and TTC as the minimum over pedestrians along the trajectory (per a search summary of the paper; definitions not re-read in full) — [arXiv](https://arxiv.org/pdf/2103.00047)
- Arena-Bench (arXiv:2206.05728) reports success rate, collisions, time to goal, path length and average velocity. Francis et al. list its metrics as also covering acceleration, jerk, curvature, "angle over length", roughness and clearing distance — [Arena-Bench](https://arxiv.org/pdf/2206.05728); [Francis et al.](https://arxiv.org/html/2306.16740v4)
- Gao and Huang, "Evaluation of Socially-Aware Robot Navigation", Frontiers in Robotics and AI 2022, DOI 10.3389/frobt.2021.721317. Review of 177 papers (2005-2021). Metrics are grouped as navigation performance, behavioural naturalness, human discomfort and sociability. Evaluation methods are case study, simulation/demonstration, laboratory study and field study — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8791647/)
- Chhetri et al., "A short methodological review on social robot navigation benchmarking" (arXiv:2510.22448, 85 IEEE papers 2020-2025): 52.2 % of metric-using papers gave no rationale for their metric choice; 22 of the 26 papers claiming superiority used two or fewer metrics or two or fewer algorithms. Recommends reporting the exact algorithm and its configuration parameters, not only "Nav2" — [arXiv](https://arxiv.org/html/2510.22448)

### Inferences
- A minimal metric set that is defensible under the hardware constraint, with its source in brackets:
  1. **Success** (reached seat and home within tolerance, no manual intervention) [`/odometry/filtered` + operator log]; report as k/5.
  2. **Contacts with people** [phone video, operator]; target 0. Report as a count, never as a rate from 5 runs.
  3. **Time to goal** and **path length** [`/odometry/filtered`].
  4. **Arrival error** at seat and home [tape measure to the taped mark], compared with empty-room runs (already in E4).
  5. **Minimum clearance** = min over the run of the minimum valid `/scan` range in a forward sector (proxy for "minimum distance to human"); state that it includes walls and furniture, and also report it restricted to the time windows when the person is in front (identify from video).
  6. **Clearance-band occupancy**: % of run time with forward min range < 0.45 m and < 1.2 m (proxy for Space Compliance at Francis et al.'s intimate/personal distances).
  7. **Stalled time / freeze events**: time with |v| < 0.02 m/s while the goal is not reached, and count of Failure-to-Progress windows (e.g. no drop in distance to goal over 5 s). Report the threshold values (M3).
  8. **Stop distance** when the person steps in: distance from the robot at the moment `/cmd_vel` reaches zero (scan range, cross-checked with tape on video stills).
  9. **Smoothness**: RMS linear acceleration and jerk from `/cmd_vel` (commanded) and from odometry (achieved); cumulative heading change (HuNavSim).
  10. **Collision-monitor activity**: time and count in SLOWDOWN / STOP / APPROACH from `collision_monitor_state`.
  11. **Compute**: controller loop rate achieved vs `controller_frequency`, count of missed-rate warnings, CPU % of `controller_server` (see next section).
- Social-force and social-work metrics need human poses, so they are out of scope here. TTC with a human also needs human velocity. A scan-based TTC proxy (min range / robot speed in the motion direction) is possible but is just clearance divided by speed, so it adds little and should be labelled a proxy.

### Gaps
- I did not re-read SocNavBench's full metric definitions; the path-irregularity and TTC definitions above come from a search summary.
- I did not verify whether Arena-Bench 2.0 (IROS 2025) changed its metric set.

## Computing the metrics from rosbag2 MCAP on a Pi-only setup (incl. CPU load and loop rate)

### Takeaway
Everything in the minimal set can be computed with a short Python script over the bag (rosbag2_py or the `mcap` reader + rclpy deserialisation), plus tape and video. The Nav2 message definitions confirm what `collision_monitor_state` holds. There is no official Nav2 tool that scores controller runs from bags; the official `tools/` benchmarks cover planners and smoothers, plus a dummy-input controller timing benchmark.

### Cited Findings
- `nav2_msgs/CollisionMonitorState` carries `action_type` (DO_NOTHING=0, STOP=1, SLOWDOWN=2, APPROACH=3 in Jazzy) and `polygon_name`. It does **not** carry a time-to-collision value — [Jazzy msg docs](https://docs.ros.org/en/jazzy/p/nav2_msgs/msg/CollisionMonitorState.html), [api.nav2.org](https://api.nav2.org/msgs/jazzy/collisionmonitorstate.html)
- The state topic is only published if a state topic name is set in the collision_monitor parameters, so `state_topic` must be configured before the runs or it will not be in the bag — [Jazzy collision_monitor_node.cpp source](https://api.nav2.org/nav2-jazzy/html/collision__monitor__node_8cpp_source.html)
- The APPROACH model uses the current robot speed to estimate time to collision with sensor data, and slows the robot so that it keeps at least `time_before_collision` seconds — [Humble collision monitor README](https://docs.ros.org/en/humble/p/nav2_collision_monitor/standard_docs/README.html), [Polygon API](https://api.nav2.org/nav2-humble/html/classnav2__collision__monitor_1_1Polygon.html)
- Nav2 `tools/` has benchmarking scripts for planning and smoothing but not for trajectory controllers (2022 discussion; issue #3239 to add one) — [Open Robotics Discourse](https://discourse.openrobotics.org/t/nav2-discussion-metrics-framework-for-quantitative-evaluation-of-navigation-performance/28082)
- Jazzy contains `controller_benchmark.cpp`, which times repeated `computeVelocityCommands` calls with dummy poses, velocities and paths. This is a per-call compute timing, usable offline on the Pi to compare RPP vs MPPI cost — [api.nav2.org jazzy](https://api.nav2.org/nav2-jazzy/html/controller__benchmark_8cpp_source.html)
- Community tools: Astryin (post-mortem toolkit computing path length, velocity and tracking error from navigation bags) and a ProxMPC benchmark harness that compares DWB, MPPI and RPP. Neither is part of Nav2, and I did not test either — [Astryin](https://discourse.openrobotics.org/t/project-astryin-a-post-mortem-analysis-visualization-toolkit-for-ros-2-navigation/53747), [prox_mpc_benchmark](https://index.ros.org/p/prox_mpc_benchmark/)
- HuNavEvaluator takes arrays of robot and agent poses and velocities per time step and writes final, per-step and per-behaviour metric files. It is a model for the output format, but it needs human poses — [arXiv:2305.01303](https://arxiv.org/pdf/2305.01303)

### Inferences
- Recommended extra topics to record for the A/B (cheap): `/rosout` (controller warnings), `/plan`, `/local_plan` or the MPPI optimal trajectory if enabled, `/tf`, the collision_monitor input (`cmd_vel_smoothed` or equivalent) **and** output `/cmd_vel`. Recording both shows how much the monitor overrode the controller.
- **Loop rate:** from the bag, take the inter-message interval of the controller's output velocity topic (before the collision monitor and velocity smoother), then report median and 5th-percentile rate against `controller_frequency`. Also count controller_server "missed its desired rate" warnings in `/rosout` **[unverified exact log text; check on the Pi]**.
- **CPU:** the bag cannot hold this by default. Run `pidstat -u -p <controller_server pid> 1` (sysstat) or sample `/proc/<pid>/stat` with a 10-line script to a dated CSV next to each bag, and log `vcgencmd get_throttled` and `measure_temp` at start and end. Thermal throttling on a Pi 4 would confound the A/B (this matches OI-8's under-voltage concern).
- Stop distance and arrival error need the tape as ground truth; the scan-based number is a cross-check, not a replacement, given the known rf2o/odometry issues (OI-8).
- One analysis script with a pytest on a synthetic trace (known min range, known stall interval) satisfies the repo's definition of done.

### Gaps
- No official Nav2 runtime "metrics" node for controller comparison was found as of late 2026.
- The exact Jazzy controller_server missed-rate log string was not verified.

## Making human motion repeatable without tracking, and how many runs papers use

### Takeaway
Use scripted, canonical scenarios with taped start/end marks and verbal or metronome timing, and run each scenario several times per condition. The closest real-robot protocol (Pirk et al. 2022) used 10 runs per scenario per location. Francis et al. suggest at least 30 samples for real-robot trials, so 5 per condition is explicitly a pilot or descriptive study and should be framed that way.

### Cited Findings
- Pirk et al., "A Protocol for Validating Social Navigation Policies" (arXiv:2204.05443): five canonical scenarios (frontal approach, intersection wait, intersection gesture, narrow doorway, blind corner). Each scenario is described in a short sentence with start positions, the human enacts it, and humans alternate start and end positions. They recorded **10 runs for each scenario in each of two locations**, using an iLQR MPC on the robot, and report the protocol as repeatable across runs and spaces — [arXiv PDF](https://arxiv.org/pdf/2204.05443)
- Francis et al.: scenario cards can include a "Human Behavior Playbook", a script or rubric so participants act consistently. In lab experiments both robot and human must attempt the interaction. Scenarios can serve as regression tests. Real-world studies must preserve safety with monitors or safety layers (R1) and respect consent and privacy (R2) — [arXiv:2306.16740v4](https://arxiv.org/html/2306.16740v4)
- Francis et al.: real-robot trials rule of thumb is "at least 30 samples" or a number derived from means and variances; avoid the word "significance" without proper tests; balance conditions — [arXiv:2306.16740v4](https://arxiv.org/html/2306.16740v4)
- SocNavBench authors warn that contrived scenarios can make people behave unnaturally — [arXiv:2103.00047](https://arxiv.org/pdf/2103.00047)
- Gao and Huang classify lab studies separately from case studies and demonstrations. A 5-run room test sits between case study and lab study — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8791647/)

### Inferences
- Protocol suggestion for E4-A/B:
  - Tape a walking lane for each walker (e.g. crossing the robot's home→seat path at a fixed point) and a "step-in" mark 0.6-0.8 m ahead of the robot's path, so the step-in distance is the same every run.
  - Trigger: the walker starts when the robot crosses a taped line; a phone metronome (e.g. 100 bpm, one step per beat ≈ 1 m/s **[assumed stride, measure it]**) sets the pace. The step-in person moves on a verbal "now" when the robot reaches a second line.
  - Same people, same shoes, same lanes for both controllers. Record a phone video from a fixed tripod spot covering the room, with a visible clock or a clap at bag start for synchronisation.
  - **Interleave and counterbalance**: ABBAABBAAB (or alternating A/B) rather than 5×A then 5×B, so battery level, temperature, walker fatigue and learning are spread across conditions. Charge the battery and check `vcgencmd get_throttled` before each block.
  - Pair the runs: run i of A and run i of B share the same script, so differences can be analysed per pair.
  - Log deviations (walker hesitated, wrong lane) per run, and decide before starting whether such runs are repeated or kept.
  - Before the human runs, do one empty-room run per controller as the baseline for arrival error and time to goal (E4 already plans this).
- The four conditions (RPP, MPPI, each ± collision_monitor zones) at 5 runs each mean 20 runs plus baselines; at roughly 2-3 min per delivery that is feasible in one session. If time is short, drop to RPP vs MPPI with the monitor configuration fixed. Changing two factors in a single A/B confounds them.

### Gaps
- I found no study reporting run-to-run variance of scripted human walkers in small rooms, so the metronome/tape approach is engineering judgement, not a cited method.
- I did not read Pirk et al.'s exact human instructions beyond the scenario descriptions.

## Reporting with n = 5 per condition

### Takeaway
Report every run (table plus dot or strip plot), the median and range per condition, the paired difference per scripted run, and a non-parametric effect size (Cliff's delta). Treat any p-value as descriptive. A 5-vs-5 test cannot reach small p unless the groups separate completely. Present the study as a pilot and state the number of runs needed for a confirmatory test.

### Cited Findings
- Francis et al.: report distributions or histograms, not only means; outliers matter for safety; do not claim "significance" without proper tests; real-robot rule of thumb is at least 30 samples — [arXiv:2306.16740v4](https://arxiv.org/html/2306.16740v4)
- Kitchenham and Madeyski (Empirical Software Engineering 29(6), art. 137, 2024): in simulations of small-sample experiments, the probability of superiority p̂ and Cliff's d had negligible small-sample bias, and they recommend p̂ as a low-risk choice for small randomised experiments — [supplement PDF](https://madeyski.e-informatyka.pl/download/KitchenhamMadeyskiRAMASSSEsupplement.pdf) (secondary summary via search; main paper not read)
- Commonly cited Romano et al. (2006) thresholds for |Cliff's δ|: < 0.147 negligible, < 0.33 small, < 0.474 medium, otherwise large — [MetricGate docs](https://metricgate.com/docs/cliff-delta-effect-size-ci) (secondary source)
- Bootstrap CIs on effect sizes can be unreliable or fail at very small n — [rcompanion cliffDelta docs](https://rdrr.io/cran/rcompanion/man/cliffDelta.html)

### Inferences
- Arithmetic: for a 5-vs-5 Mann-Whitney test there are C(10,5) = 252 rank arrangements, so the smallest possible two-sided exact p is 2/252 ≈ 0.008 (complete separation). One overlap already pushes p to about 0.016, and a couple more push it past 0.05. With n = 5 a "no difference" result is uninformative, which should be stated explicitly.
- For a paired design, the Wilcoxon signed-rank test with 5 pairs has a minimum two-sided p of 2/32 = 0.0625, so it **cannot** reach 0.05. This is a strong argument for reporting effect sizes and individual pairs, not p-values.
- Binary safety outcomes: with 0 contacts in 5 runs, the exact Clopper-Pearson upper bound on the per-run contact rate is 1 − 0.05^(1/5) ≈ 0.45 (one-sided 95 %), or 1 − 0.025^(1/5) ≈ 0.52 (two-sided 95 %). Write "0/5 contacts", never "safe".
- Suggested wording: "This is a pilot comparison (n = 5 per condition). We report medians, ranges and Cliff's δ. Differences larger than run-to-run spread in the empty-room baseline are noted as indicative. A confirmatory test would need roughly N runs (state a power estimate from the observed spread)."
- Use the empty-room baseline spread as a noise floor: a controller difference smaller than the empty-room range on the same metric should not be claimed.

### Gaps
- I did not find a robotics paper that models n = 5 reporting with Cliff's δ; the method recommendation comes from general small-sample statistics literature.

## Evidence comparing RPP / DWB vs MPPI in Nav2 (and running MPPI on a Pi 4)

### Takeaway
I found no peer-reviewed head-to-head with numbers for RPP vs MPPI among moving people. Published MPPI performance figures are for x86 and Jetson. There is a documented SIGILL crash of MPPI binaries on the Raspberry Pi 4 (Humble), fixed only by building from source or by the post-Jan-2025 Eigen rewrite, which is not in Jazzy. **First check on the Pi: does MPPI from Jazzy binaries even configure, and what loop rate does it reach?**

### Cited Findings
- Nav2 MPPI docs: runs at 50+ Hz on a modest Intel CPU (4th-gen i5); default `batch_size` 1000 and 1 iteration (Iron docs) — [docs.ros.org Jazzy MPPI](https://docs.ros.org/en/jazzy/p/nav2_mppi_controller), [Iron](https://docs.ros.org/en/iron/p/nav2_mppi_controller) (via search summary; the page blocked direct fetch)
- Macenski's "Speedups in MPPI & Smac Planner" post: Eigen rewrite gives 45-50 % speedup, > 120 Hz CPU-only (125 Hz average on an i7-1365U), 55-60 Hz on Jetson Orin (Kiwibot), about half a Jetson core at defaults, little benefit beyond about 50 Hz. The MPPI change is in Rolling/Kilted and "will not be backported"; Jazzy gets only the Smac speedup — [Open Robotics Discourse](https://discourse.openrobotics.org/t/nav2-speedups-in-mppi-smac-planner/41667)
- navigation2 issue #4380 "MPPI ARM Binaries Issue in RPi4": on Humble arm64 binaries, `controller_server` died with SIGILL in `MPPIController::configure` on a Raspberry Pi 4, because the build farm (AWS Graviton) compiled with CPU features the Cortex-A72 lacks. Building from source fixed it; the xtensor→Eigen migration (PR #4621, Jan 2025) is the permanent fix, not backported to Humble. The issue was closed Jan 15, 2025 — [GitHub issue #4380](https://github.com/ros-navigation/navigation2/issues/4380)
- Macenski et al., "Regulated Pure Pursuit for Robot Path Tracking" (arXiv:2305.20026): RPP regulates linear velocity for safety in constrained, partially observable spaces — [arXiv](https://arxiv.org/abs/2305.20026v1), [Jazzy RPP docs](https://docs.ros.org/en/jazzy/p/nav2_regulated_pure_pursuit_controller)
- A CTU thesis compares five Nav2 controllers including MPPI and RPP on a high-dynamics robot and recommends Vector Pursuit as the most balanced; MPPI and GC suit some scenarios (RPP numbers not seen) — [CTU dspace](https://dspace.cvut.cz/handle/10467/122559)
- Formula Student ROS 2 paper (arXiv:2311.14276): `regulated_pure_pursuit` gave a 0.7 s average lap-time improvement over their custom pure pursuit (no MPPI) — [arXiv](https://arxiv.org/pdf/2311.14276)
- HuNavSim simulation shows DWB passing closest to people (min 0.40 m vs 0.90 m for a social-cost-layer planner) with zero stalled time. This is evidence that a non-human-aware local controller trades clearance for progress — [arXiv:2305.01303](https://arxiv.org/pdf/2305.01303)
- A vendor guide (MyBotShop) states RPP's performance diminishes in close proximity or dynamic environments. This is a qualitative opinion — [MyBotShop docs](https://docs.mybotshop.de/projects/project_digital_twin_safety/html/comb_3.html)

### Inferences
- Jazzy was released before the Jan 2025 Eigen migration and did not receive it, so Jazzy's MPPI is likely still the xtensor build. Whether Jazzy arm64 binaries hit the same SIGILL on a Pi 4 is **[unverified]**. Test it in 5 minutes (launch controller_server with MPPI in dry run) before committing to the A/B. If it crashes, building `nav2_mppi_controller` from source on the Pi (2 GB swap present) is the documented workaround but may take a long time.
- Expect a lower loop rate on a Pi 4 than the x86 figures. Reduce `batch_size` (e.g. 1000→300-500) and/or `time_steps` and set `controller_frequency` to what is achieved (e.g. 10-20 Hz). At 0.15 m/s the robot moves 1.5 cm per 10 Hz cycle, so a 10 Hz loop is physically adequate. Report the tuned parameters in the A/B (Chhetri et al.'s reproducibility point).
- Fairness: both controllers should use the same costmap, inflation, velocity limits (v_max 0.15), velocity smoother and collision_monitor configuration. Otherwise the A/B measures the configuration, not the controller.
- Neither RPP nor default MPPI predicts human motion. In Nav2 both react to people only through costmap obstacles, so a large difference in social metrics is not guaranteed; the clearest differences may be in smoothness, stall behaviour and compute.

### Gaps
- No published RPP vs MPPI numbers among moving people were found.
- No published Raspberry Pi 4 MPPI loop-rate figure was found.
- Not verified whether Jazzy arm64 MPPI binaries crash on a Pi 4.

## Safety-standard hooks for the hazard table (ISO 13482, ISO 3691-4)

### Takeaway
ISO 13482:2014 (personal care robots, including mobile servant robots) has dedicated clauses on robot stopping, operational-space limits and safety-related speed control. ISO 3691-4:2023 (driverless industrial trucks) gives the clearest stop-distance logic: the robot must stop within the personnel-detection field, sized as reaction distance + braking distance + margin. Both are paywalled, so the student report should cite clause titles and the general principle, not quote numbers from vendor summaries as normative.

### Cited Findings
- ISO 13482:2014 table of contents includes 6.2 Robot stopping, 6.3 Limits to operational spaces, 6.4 Safety-related speed control; scope is limited to earthbound personal care robots — [ANSI preview PDF](https://webstore.ansi.org/preview-pages/ISO/preview_ISO+13482-2014.pdf), [VDE proceedings overview](https://www.vde-verlag.de/proceedings-en/453601102.html)
- ISO 3691-4:2023 covers driverless industrial trucks and their systems — [ANSI blog](https://blog.ansi.org/ansi/iso-3691-4-2023-driverless-industrial-trucks/)
- Vendor summaries of ISO 3691-4 (secondary, not normative): personnel detection is usually a safety-rated laser scanner; test pieces are a vertical cylinder 200 mm diameter × 600 mm and a lying cylinder 70 mm × 400 mm, and the truck must stop before contact; 0.3 m/s is the speed limit while detection is muted (e.g. docking); braking must stop the truck within the detection range for the given speed, floor, gradient and load; safety functions typically need ISO 13849-1 PL d — [Fabrico blog](https://www.fabrico.io/blog/iso-3691-4-driverless-industrial-trucks/), [TÜV Rheinland AGV whitepaper 2021](https://tuv.com/content-media-files/master-content/services/industrial-services/pdf/tuv-rheinland-automated-guided-vehicle-whitepaper-2021.pdf) **[secondary; check against the standard before quoting]**
- Speed-and-separation monitoring (ISO/TS 15066 practice, from arm cobots): full speed when the human is far, reduced speed when closer, stop in the inner zone. The protective separation distance sums human motion during the reaction and stopping time, robot reaction distance, robot stopping distance, intrusion distance and position uncertainty; human speed defaults to 1.6 m/s when it is not monitored — [arXiv:1908.03046](https://arxiv.org/pdf/1908.03046) and related search results **[secondary summary]**

### Inferences
- Hazard-table hook: S_required = v_h·(t_r + t_s) + v_r·t_r + d_brake + C. With v_r = 0.15 m/s, an assumed t_r ≈ 0.1 s (scan period 0.14 s at 7 Hz plus a 20 Hz control cycle — **measure it**), a measured d_brake, and v_h = 1.6 m/s for a person stepping in, the human term dominates. This argues the measured "stop distance" in E4 should be reported alongside a computed required separation, and that the collision_monitor STOP polygon should be at least that size.
- collision_monitor zones map onto the SSM idea: SLOWDOWN polygon = "reduced speed" zone, STOP polygon = protective field, APPROACH = time-based separation. Say in the report that Nav2's collision_monitor is a software layer on a non-safety-rated lidar and Pi, so it does not meet ISO 13849 PL d. The kill switch remains the hardware motor switch (AGENTS.md rule 7).
- At 0.15 m/s the robot is already below the 0.3 m/s muted-detection figure from ISO 3691-4 summaries. That comparison can be cited as context but not as compliance.

### Gaps
- Normative ISO 13482 and ISO 3691-4 numbers (speed limits, stopping distances) could not be verified because the standards are paywalled.
- I did not find whether the Nav2 docs carry an explicit "not safety-certified" statement for collision_monitor (the docs page could not be fetched).

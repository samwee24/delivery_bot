# CA3 report: detailed outline (plan C+)

**Tentative title.** Re-evaluating EKF-Fused 2D LiDAR SLAM on a Low-Cost Indoor Delivery Robot: Repeatability, Inertial Contribution and the Effect of Dynamic Human Obstacles

**Fallback title** (use if E1 to E4 do not run in time). Localisation and Safety Lessons for Autonomous Vehicles from a Low-Cost Indoor Delivery Robot

**Framing.** Re-evaluation against published baselines, not replication: E3 partially
replicates [K26], E2 is an analogue of [M26], E4 extends [Y21]. Comparisons are directional.

Plan, schedule and experiment table: [`../docs/report_plan.md`](../docs/report_plan.md)
(being written in parallel; if a link there disagrees with this file, the plan wins).
Brief: one group report, NTULearn template is a formatting reference only, no length
limit, due end of Week 13. Rubric: content 40 %, conclusions 25 %, presentation 20 %,
peer 15 %. The slides follow the same section order.

## Writing rules

- **Provenance label on every number**: *brief default*, *measured*, *fitted* or
  *target* (AGENTS rule 4). A MEASURE value is not a result until measured on the robot.
- **Numbers travel with the command that produced them** (AGENTS rule 6): give the test
  log row or note, with the date and commit, beside the number.
- **Pending results** are written `RESULT: pending E1` (or E2, E3, E4) and nothing else.
  No estimate, no "about", no expected value.
- **Citation keys** are those in [`../docs/slam.md`](../docs/slam.md) References: [R25],
  [K26], [M26], [J16], [MJ21], [H22], [Y21], [S23], [F17], [EXP], [EVO]. Do not cite
  anything not in that table until it is added there. Product facts and standards
  (SOTIF, ISO 13482) are "to check" until a source is found.
- Plain prose, British spelling (localisation, characterisation). Links relative to this
  file. Every slide headline and every section end carries a claim, not a topic.
- Owners: Sherman (SLAM, localisation, lidar and IMU), motor teammate (drive, Nav2 goals,
  delivery script), A and B (placeholders: background, products, hazard table, people runs).

## Abstract

- **Purpose**: five sentences a marker can quote: problem, the robot as a scaled AV,
  which published results were re-evaluated, the main finding, what it means for real AVs.
- **Rubric**: content 40 %, conclusions 25 %.
- **Goes in**: write last. Sentence 4 states the finding that the data supports, including
  "did not transfer" if E2 or E3 say so. Every number in it carries a pointer to section 5.
- **Evidence**: sections 5 to 8 of this report.
- **Owner**: A (draft), Sherman (check numbers).

## 1 Introduction

- **Purpose**: frame indoor delivery as an AV problem, state the RQs and contributions.
- **Rubric**: content 40 % (in-depth thinking), presentation 20 % (logical flow).
- **Goes in**:
  - Last-metre delivery robots and full-size AVs share one loop: sense, localise, map,
    plan, act, stay safe. One paragraph, sources "to check".
  - The question: published 2D SLAM results were measured under conditions a cheap
    delivery robot never sees (replay, better sensors, wheel encoders, no people). Do
    they hold, and what changes? (slide hook.)
  - RQ1 repeatability on a cheap lidar and a Raspberry Pi 4 [K26]; RQ2 IMU contribution
    [M26]; RQ3 people in the room [Y21]; RQ4 the delivery mission (home to seat to home, 5
    runs in a row, within 15 cm, no human touch; *target*, phase 7 in
    [`../docs/plan.md`](../docs/plan.md)).
  - Contributions, in one list: a live re-evaluation on low-cost hardware with tape-measured
    ground truth (which [K26] lacks), the before/after-SLAM IMU test, an extension to people,
    an open record of failures (OI-4, OI-8), a working integrated robot.
  - Scope: what is out (camera localisation, wheel encoders, multi-room maps) goes to
    section 8.
  - **Contribution table per member** (Sherman: lidar, IMU, rf2o, EKF, slam_toolbox,
    localisation, E2, E3; motor teammate: motors, Nav2 goals, delivery script, E1; A, B:
    products, hazard table, E4, background). Peer assessment (15 %) reads this table.
- **Evidence**: [`../docs/CA3.md`](../docs/CA3.md) decisions D5, D7, D8;
  [`../docs/plan.md`](../docs/plan.md); [`../docs/slam.md`](../docs/slam.md) References.
- **Owner**: A, with Sherman and the motor teammate for their rows.

## 2 Background and state of the art

- **Purpose**: show the research effort and place the work against papers and products.
- **Rubric**: content 40 % ("extensive research effort").
- **Goes in**:
  - 2.1 2D lidar SLAM families: filter, graph, learned. Why graph SLAM suits a small
    room [R25]; the package we used [MJ21]; wrong loop closures as a failure mode [H22].
  - 2.2 Scan-matching odometry for sparse scans: range flow [J16], de-skewing for slow
    lidars [S23].
  - 2.3 Published baselines, stated precisely: what [K26] measured and how, what [M26]
    measured and how (IMU ablation design), what [Y21] adds (people). For each, a row
    "their setup / their metric / their finding / what we copy / what differs". Fill
    from [`literature_notes.md`](literature_notes.md), which corrects two assumptions:
    [K26] compares AMCL feedback on/off (IMU fused in both), mostly by offline replay of
    an Ouster OS-1 cut to 2D, with no ground truth (its "ATE" is run-to-run spread);
    [M26] ablates wheel odometry vs wheel odometry + IMU yaw on the MIT Stata dataset.
    So E3 replicates K26's "AMCL off" condition; E2 is an analogue of M26, not a copy.
    Our 9.1 checkpoints give the ground truth K26 lacks: say so as a contribution.
  - 2.3b How the field evaluates 2D SLAM, critically: pairwise ATE without ground truth,
    offline replay instead of live runs, covariances fitted on the evaluation data
    ([M26] lists this as its own limitation). One paragraph ending in an **Our take**.
  - 2.4 Evaluation tools and metrics: APE and RPE with [EVO], map quality without ground
    truth [F17].
  - 2.5 AV localisation in industry (HD-map lidar matching, camera-led, GNSS/INS plus
    wheel odometry): sources to find, one short paragraph each, no unsourced claims.
  - 2.6 **Product comparison** (table below), with one paragraph on what each product
    simplifies about its world (mapped site, fixed routes, slow speed, remote operator).
    Aethon TUG is a hospital cart robot; Amazon Scout was shut down in 2022. Both are
    *to check* before they are written as facts.
- **Product table skeleton** (every cell "to check" except our robot):

| Product | Setting | Main sensors | Localisation approach | Price class | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Pudu BellaBot | to check | to check | to check | to check | to check | to check |
| Keenon (delivery models) | to check | to check | to check | to check | to check | to check |
| Aethon TUG | to check | to check | to check | to check | to check | to check |
| Starship | to check | to check | to check | to check | to check | to check |
| Amazon Scout | to check | to check | to check | to check | to check (plan notes a 2022 shutdown) | to check |
| Our robot | one small indoor room, taped home mark | RPLidar A1M8, MPU6050 gyro, USB camera (not used for localisation) | rf2o scan odometry + IMU in a `robot_localization` EKF, `slam_toolbox` on a saved map | consumer parts (cost: to sum from the build) | research build, motors pending (see 5.1) | [`../docs/system/01_hardware.md`](../docs/system/01_hardware.md) |

- **Evidence**: [`../docs/slam.md`](../docs/slam.md) References and its literature
  sections; [`../docs/system/07_ros_stack.md`](../docs/system/07_ros_stack.md) for the
  stack choice (D5, D7 in [`../docs/CA3.md`](../docs/CA3.md)).
- **Owner**: A (2.5, 2.6 products), B (2.6 products, split with A), Sherman (2.1 to 2.4).

## 3 System

- **Purpose**: a reader can rebuild the robot and see what is ours and what is bought.
- **Rubric**: content 40 %, presentation 20 %.
- **Goes in**:
  - Hardware: Raspberry Pi 4B, RPLidar A1M8, MPU6050, L298N and TT motors, USB camera;
    power split and kill switch (motor switch, not software).
  - ROS 2 Jazzy stack: `rplidar_ros`, `rf2o_laser_odometry` (`publish_tf: false`),
    `robot_localization` (sole publisher of `odom to base_footprint`), `slam_toolbox`,
    Nav2. We write only the motor node, IMU node, URDF and delivery script (D5, D7).
  - One diagram of the TF tree and topic graph (reuse
    [`../docs/img/pipeline-flow.png`](../docs/img/pipeline-flow.png) if it is current;
    otherwise redraw).
  - Safety design as structure: motors only through the watchdog (`stop_dist_m`,
    `watchdog_s`, SIGINT zeroes PWM), `dry_run` default, `v_max` 0.15 m/s (*brief default*).
    Describe it; do not design motor code (motor teammate owns it).
  - Operations: Foxglove for live view and buttons, rosbag2 MCAP for every run, config
    YAML copied back per run.
  - Discussion hook for section 6: buy the estimation maths, write only the glue.
- **Evidence**: [`../docs/system/01_hardware.md`](../docs/system/01_hardware.md),
  [`../docs/system/04_architecture.md`](../docs/system/04_architecture.md),
  [`../docs/system/05_config_reference.md`](../docs/system/05_config_reference.md),
  [`../docs/system/07_ros_stack.md`](../docs/system/07_ros_stack.md),
  [`../docs/wiring.md`](../docs/wiring.md), [`../docs/CA3.md`](../docs/CA3.md) D5 to D7.
- **Owner**: Sherman (sensing, SLAM, TF), motor teammate (drive, safety node), B (diagram).

## 4 Method

- **Purpose**: make E1 to E4 repeatable and show exactly where we differ from [K26] and [M26].
- **Rubric**: content 40 %.
- **Goes in**:
  - The shared driven protocol: five tape-measured checkpoints (slam_build_path Stage 9.1),
    config frozen on one date, commit hash recorded per run, battery charged before each
    run (the Pi read `throttled=0x50005` on 2026-11-02, measured, test log).
  - E1 delivery mission: 5 runs, home to seat to home. Metrics: success %, arrival error
    at checkpoints, time.
  - E2 IMU ablation: E1 bags replayed with the EKF with and without the IMU, plus one
    live run each. Metrics: ATE, RPE, heading error with [EVO]. Calibrate variances on a
    run that is not used for evaluation [M26].
  - E3 repeatability: the same five runs, pairwise ATE and map IoU [K26].
  - E4 people in the room: 5 runs with 1 to 2 people walking, plus one person stepping
    in front. Metrics: arrival error against E1, localisation failures, stop distance,
    contacts.
  - S hazard table: 6 to 8 hazards, mitigation, the test that proves it.
  - Differences from [K26] and [M26] in a table: lidar (A1M8, 7.05 Hz, 26 to 29 % no-echo,
    *measured*), no wheel encoders, Pi 4, room size, human presence, run count.
  - Threats to validity: ruler-and-eye ground truth in the early tests, hand-pushed
    runs, five runs only, one room.
  - Optional: echo rate by material with `tools/probe_echo_rate.py` (first to drop if
    time runs out).
- **Evidence**: [`../docs/slam_build_path.md`](../docs/slam_build_path.md) Stage 9;
  [`../docs/slam.md`](../docs/slam.md) evaluation sections;
  [`../docs/plan.md`](../docs/plan.md) phase 7; [`../tools/analysis/`](../tools/analysis/);
  [`../docs/system/05_config_reference.md`](../docs/system/05_config_reference.md).
- **Owner**: Sherman (E2, E3, metrics), motor teammate (E1 protocol), B (E4, hazard table).

## 5 Results

- **Purpose**: present measured results only, each with its provenance.
- **Rubric**: content 40 %.
- **Goes in**: 5.1 to 5.7 below. Figures carry the commit hash and bag name in the caption.
  Where nothing is measured yet, write the `RESULT: pending` line and keep the table.

### 5.1 Platform characterisation (already measured)

- Lidar: A1M8 at 7.05 Hz; 26 to 29 % no-echo on this Pi; gaps follow the room, not the
  lidar. *measured.* Figure:
  [`../evidence/lidar/2026-10-21_composite_20revs.png`](../evidence/lidar/2026-10-21_composite_20revs.png).
  Source: OI-4 in [`../docs/CA3.md`](../docs/CA3.md) and the P1 row of
  [`../docs/test_log.md`](../docs/test_log.md).
- IMU at rest: 100 Hz, gyro z std 0.00175 rad/s. *measured*, 2026-10-30,
  [`../docs/test_log.md`](../docs/test_log.md) and [`../notes/notes.md`](../notes/notes.md).
- Gyro on a hand-turned full turn reads 360.2 degrees against a true 360. *measured*,
  2026-10-31 (3.2 in [`../docs/test_log.md`](../docs/test_log.md)).
- Power: `throttled=0x50005` (under-voltage) read on 2026-11-02 and 2026-11-03.
  *measured*; see [`../docs/system/06_troubleshooting.md`](../docs/system/06_troubleshooting.md).
- Motors and drive: RESULT: pending motor teammate (motors due 2026-11-04 per the plan).

### 5.2 Scan odometry and its failure (already measured)

- rf2o by hand on 2026-10-31: turn read 352.9 degrees for 360 (-2 %), 1 m push read
  0.962 m (-3.8 %). *measured*, 3.2 in [`../docs/test_log.md`](../docs/test_log.md).
- OI-8: two pushes on 2026-11-01 read about 24 % of true travel (-76 %). *measured*;
  cause open. Leads: scan format (`angle_compensate`), a person behind the robot.
  Offline rig results in the 2026-11-02 and 2026-11-03 test log rows (replay is
  not repeatable and is not yet a clean control). State this as open unless Tuesday's
  live pushes close it.
- Figure: rf2o distance per run, good bag against bad bag (script in
  [`../tools/analysis/`](../tools/analysis/)).

### 5.3 Mapping and localisation on the saved map (already measured)

- First room map and frozen `slam_mapping.yaml` (5.4, 5.5 in the test log). Figure:
  [`../results/maps/2026-10-31_room2.png`](../results/maps/2026-10-31_room2.png).
- Wrong-start recovery: a 30 cm / 20 degree wrong start recovers after a push; 31 degrees
  does not (6.4, 2026-11-01). *measured, ruler-and-eye truth.* Figure:
  [`../results/maps/2026-11-01_room2_home_pose.png`](../results/maps/2026-11-01_room2_home_pose.png).
  Gives the convergence basin; one case per angle, so state that.

### 5.4 E3 Repeatability (RQ1)

RESULT: pending E3. Table skeleton: run pair, ATE, map IoU, against [K26] value
(to check from the paper).

### 5.5 E2 IMU contribution (RQ2)

RESULT: pending E2. Table skeleton: EKF with IMU / without IMU, ATE, RPE, heading error,
measured **before SLAM (`/odometry/filtered`) and after SLAM (map pose)**. [M26] found the
EKF cut translational APE RMSE by 60–75 % before SLAM but changed it by only −2.6 to +1.6 %
after SLAM with SLAM Toolbox ([`literature_notes.md`](literature_notes.md)): test whether the
same holds here. Fallback if OI-8 is not closed: run offline on the good
2026-10-31 bag and say so.

### 5.6 E4 People in the room (RQ3)

RESULT: pending E4. Table skeleton: condition (empty, 1 to 2 walking, step-in), arrival
error, localisation failures, stop distance, contacts.

### 5.7 E1 Delivery mission (RQ4) and hazard table

RESULT: pending E1. Table skeleton: run 1 to 5, success, arrival error at each checkpoint,
time. Hazard table skeleton: hazard, mitigation (structural), test, pass or fail,
RESULT: pending S. Hazard framing from SOTIF (ISO 21448) and ISO 13482: to check before citing.

- **Evidence**: [`../docs/test_log.md`](../docs/test_log.md),
  [`../notes/notes.md`](../notes/notes.md), [`../results/`](../results/),
  [`../evidence/`](../evidence/), [`../tools/analysis/`](../tools/analysis/),
  [`../docs/CA3.md`](../docs/CA3.md) OI-4, OI-6, OI-8.
- **Owner**: Sherman (5.1 to 5.5), motor teammate (5.7 E1, drive), B (5.6, hazard table).

## 6 Discussion

- **Purpose**: compare ours with the papers per RQ, say why, state limits.
- **Rubric**: content 40 % (in-depth thinking), conclusions 25 %.
- **Goes in**: one subsection per RQ, then limits. Each subsection: what we found, what
  the paper found, the most likely reason for any gap, then the Our take box. Write the
  box as a hypothesis until the experiment has run, then keep it, revise it or replace it
  with what the data said.
- **Limits**: five runs, one room, hand ground truth in early tests, cheap lidar, Pi
  under-voltage, motor timing.

### 6.1 RQ1 Repeatability

> **Our take.** *Hypothesis:* the [K26] result transfers to our stack in rank order
> (small run-to-run spread) but not in absolute value, because a 26 to 29 % no-echo rate
> and 7 Hz scans give rf2o less to match. *Confirmed by:* E3 pairwise ATE and map IoU
> within a stated factor of [K26]. *Killed by:* spread much larger than [K26], or
> repeatability that depends on who pushes, not on the stack.
> RESULT: pending E3.

### 6.2 RQ2 IMU contribution

> **Our take.** *Hypothesis:* the gyro earns its place mainly in heading, not position,
> because the hand-turned gyro read is close to truth (360.2 degrees, *measured*) while
> rf2o's turn read is further off (352.9 degrees, *measured*). *Confirmed by:* E2 heading
> error clearly lower with the IMU and position error about equal. *Killed by:* no
> difference, or the IMU making position worse (bias, variance fit).
> RESULT: pending E2.

### 6.3 RQ3 People

> **Our take.** *Hypothesis:* the customer is the obstacle: people in the scan degrade
> localisation and are the main safety hazard, and the safety stop matters more than the
> localiser. *Confirmed by:* E4 arrival error and localisation failures clearly worse than
> E1, with contacts or near-misses only in the step-in case. *Killed by:* no change from
> E1, in which case a person behind the robot is also unlikely to explain OI-8.
> RESULT: pending E4.

### 6.4 RQ4 Mission

> **Our take.** *Hypothesis:* the robot succeeds because the world is simplified (taped
> home mark, mapped room, 0.15 m/s), not because the localiser is strong; the limiting
> factor is integration (motors, power, start-up), not algorithms. *Confirmed by:* E1
> failures traced to power, start-up or calibration rather than pose error. *Killed by:*
> failures traced to localisation drift.
> RESULT: pending E1.

- **Evidence**: section 5; [`../docs/CA3.md`](../docs/CA3.md) OI-4, OI-6, OI-8;
  [`../docs/system/06_troubleshooting.md`](../docs/system/06_troubleshooting.md);
  [`../docs/slam_journal.md`](../docs/slam_journal.md).
- **Owner**: Sherman (6.1, 6.2), B (6.3), motor teammate (6.4), A (limits, edit).

## 7 Our position

- **Purpose**: 3 to 5 opinions, each backed by data, for the "your unique thoughts" criterion.
- **Rubric**: content 40 %, conclusions 25 %.
- **Goes in**: each position as a short paragraph (claim, the data behind it, the
  real-AV consequence) followed by an Our take box. A position without a measurement
  behind it is deleted, not softened.

> **Our take (how 2D SLAM should be evaluated).** *Hypothesis:* pairwise ATE and replay
> hide errors that live runs against ground truth show. *Confirmed by:* E3 checkpoint
> error against pairwise ATE; live E2 runs against replays (RESULT: pending E2, E3).
> *Killed by:* both metrics tell the same story.

> **Our take (transfer gap).** *Hypothesis:* results from [K26] and [M26] transfer to
> a lidar with a much lower echo rate only for the ranking of methods, not for absolute
> accuracy. *Confirmed by:* E3 and E2 (RESULT: pending E2, E3). *Killed by:* absolute
> numbers within the papers' range.

> **Our take (the customer is the obstacle).** *Hypothesis:* people are both the
> localisation problem and the safety problem; real AVs and delivery robots should
> spend their redundancy there. *Confirmed by:* E4 (RESULT: pending E4). *Killed by:* no
> degradation with people present.

> **Our take (redundancy earns its cost).** *Hypothesis:* the IMU bought a measurable
> heading improvement; wheel encoders or a camera would buy the next step, because
> scan-only odometry failed on 2026-11-01 (OI-8, *measured*). *Confirmed by:* E2 plus the
> OI-8 outcome. *Killed by:* IMU gives no gain, or OI-8 is traced to a setting, not to
> the method.

> **Our take (simplify the world).** *Hypothesis:* delivery robots ship indoors because
> the world is simplified (mapped site, home mark, slow speed), which is why the same
> approach stalls on pavements. *Confirmed by:* E1 failures that disappear when the world
> is simpler, plus sourced product facts from section 2 (to check). *Killed by:* E1
> failures that are algorithmic.

> **Our take (integration is the hard part).** *Hypothesis:* the faults that cost most
> time were integration faults that looked like sensor faults: OI-8, the lidar start hang
> (OI-6), under-voltage. (Two transform publishers spinning the map is a risk we designed
> out with rf2o `publish_tf: false`, not a fault we hit; cite it as prevention only.) *Confirmed by:* a
> tally of lost hours by cause from [`../notes/notes.md`](../notes/notes.md) and
> [`../docs/system/06_troubleshooting.md`](../docs/system/06_troubleshooting.md) (to
> compile). *Killed by:* most time lost to genuine algorithm limits.

- **Evidence**: sections 5 and 6; [`../docs/system/06_troubleshooting.md`](../docs/system/06_troubleshooting.md);
  [`../notes/notes.md`](../notes/notes.md).
- **Owner**: all; Sherman and A write, B and the motor teammate review their rows.

## 8 Conclusions and future work

- **Purpose**: numbered findings tied to results, then a costed roadmap and trends.
- **Rubric**: conclusions 25 % (explains conclusions and elaborates on future work).
- **Goes in**:
  - 3 to 5 numbered conclusions, one per RQ, each citing the table or figure in section
    5. If a result contradicts a paper, it is a conclusion, not a footnote.
    RESULT: pending E1 to E4.
  - Honest status: what was not done and why (named blockers, e.g. Nav2, OI-8).
  - Future work roadmap (table below). Option F (camera localisation against lidar) is
    the best idea and was dropped for timing; say so.
  - Trends: solid-state lidar cost, learned SLAM, fleet map sharing, people-aware SLAM
    [Y21]. Sourced or marked "to check".
- **Costed roadmap skeleton**:

| Item | Fixes which failure | Rough cost | Effort |
| --- | --- | --- | --- |
| Wheel encoders as a third EKF input | scan-only odometry failure (OI-8) | to check | to estimate |
| Camera fusion (option F: camera localisation vs lidar) | low echo rate (OI-4), glass and dark surfaces | to check | to estimate |
| People filtering in the scan [Y21] | people degrading rf2o and the map | to check | to estimate |
| Simulation regression (Gazebo) | integration faults found late | to check | to estimate |
| Higher-rate or higher-echo lidar | 7.05 Hz, 26 to 29 % no-echo (*measured*) | to check | to estimate |
| Stable power (battery, regulator) | under-voltage, lidar start hang (OI-6) | to check | to estimate |
| Global relocalisation | wrong start beyond about 30 degrees (6.4, *measured*) | to check | to estimate |

- **Evidence**: [`../docs/CA3.md`](../docs/CA3.md) open issues; [`../docs/plan.md`](../docs/plan.md);
  section 5 results; [`../docs/test_log.md`](../docs/test_log.md).
- **Owner**: A (draft), Sherman (SLAM rows), motor teammate (drive and power rows).

## References

One consistent style, as the NTULearn template asks. Start from the keys in
[`../docs/slam.md`](../docs/slam.md) (R25, K26, M26, J16, MJ21, H22, Y21, S23, F17, EXP,
EVO). Add datasheets (A1M8, MPU6050), package documentation (`rplidar_ros`,
`robot_localization`, Nav2) and product and standards sources only once each is found
and checked. Owner: A.

## Appendix

- A. Test log extract, with the command per row: [`../docs/test_log.md`](../docs/test_log.md).
- B. Frozen config YAML: `delivery_bot_bringup/config/` and
  `delivery_bot_drivers/config/` as run, plus
  [`../docs/system/05_config_reference.md`](../docs/system/05_config_reference.md).
- C. Open issues table (OI-1 to OI-8): [`../docs/CA3.md`](../docs/CA3.md).
- D. Hazard table in full; per-member contribution detail.
- E. Repository link (public as of 2026-11-01, OI-7) and commit hash of each reported run.
- Owner: Sherman (A to C, E), B (D).

---

Figures go in [`figures/`](figures/); one line per figure in `captions.md`, matching CA2's
convention, each with the bag name and commit hash.

# CA3 report: detailed outline (plan H, people as the axis, live runs)

**Main question.** A cheap delivery robot works in an empty room. What happens when people
move around it, which part breaks, and what defends against it?

**Tentative title.** The Customer Is the Obstacle: Localisation and Safety of a Low-Cost Delivery Robot Among People

**Fallback title** (use if driving fails). Localisation and Safety Lessons for Autonomous Vehicles from a Low-Cost Indoor Delivery Robot

**Framing.** Every method runs live on the robot, in an empty room and with people walking.
Published results anchor one question each: [Y21] for the impact of people (RQ1), [M26] for
odometry (RQ2, analogue: no encoders), [K26] for the localiser (RQ3); RQ4 (safety stop) rests
on our own hazard analysis. Comparisons with papers are directional. OI-8 (a person behind the
robot cut rf2o to a quarter) is the discovery the questions grew from.
RQ numbers changed twice on 2026-11-09; this file follows plan H in [`../docs/report_plan.md`](../docs/report_plan.md) §3.

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
- **Pending results** are written `RESULT: pending E1` (or E2 to E4) and nothing else.
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
  - RQ1 how much do people hurt the robot ([Y21], OI-8); RQ2 which part breaks: scan
    odometry vs the IMU, 4 configs ([M26] analogue); RQ3 which localiser holds up: AMCL vs
    `slam_toolbox` ([K26]); RQ4 does it stay safe when a person steps in. Each is measured
    empty against people. E1, the delivery demo (home to seat to home; *target* 5/5 within
    15 cm, phase 7 in [`../docs/plan.md`](../docs/plan.md)), shows the system works end to end.
  - Contributions, in one list: live, closed-loop tests of odometry configs and localisers on
    low-cost hardware with tape-measured ground truth (which [K26] lacks), each in an empty
    room and among people; the OI-8 discovery and its mechanism; a step-in safety test against
    the stop zone; an open record of failures (OI-4, OI-6, OI-8); a working integrated robot.
  - Scope: what is out (camera localisation, wheel encoders, multi-room maps) goes to
    section 8.
  - **Contribution table per member** (Sherman: lidar, IMU, rf2o, EKF, slam_toolbox,
    localisation, live switches, E2, E3; motor teammate: motors, Nav2 goals, delivery
    script, E1; A, B: products, hazard table, people protocol, E4, background). Peer assessment (15 %) reads this table.
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
    measured and how (IMU ablation design), what [Y21] adds (people); AMCL as the
    particle-filter alternative that [K26] switches on and off. For each, a row
    "their setup / their metric / their finding / what we copy / what differs". Fill
    from [`literature_notes.md`](literature_notes.md), which corrects two assumptions:
    [K26] compares AMCL feedback on/off (IMU fused in both), mostly by offline replay of
    an Ouster OS-1 cut to 2D, with no ground truth (its "ATE" is run-to-run spread);
    [M26] ablates wheel odometry vs wheel odometry + IMU yaw on the MIT Stata dataset.
    So E3 contains K26's "AMCL off" condition and adds AMCL as a standalone localiser;
    E2 is an analogue of M26, not a copy.
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

- **Purpose**: make every live run repeatable and show exactly where we differ from [K26] and [M26].
- **Rubric**: content 40 %.
- **Goes in**:
  - The design: methods (odometry: rf2o + IMU, rf2o only, IMU only, none; localiser:
    `slam_toolbox`, AMCL) × condition (empty room, 1–2 people walking), every cell a live run,
    3 runs per cell, every run bagged. Methods switch by launch argument, config frozen per
    method before the session, commit hash per run.
  - People protocol: 1–2 people at normal pace on two fixed taped paths (one crossing the
    route, one behind the start), nobody touches the robot, walkers start with the robot.
  - Ground truth: five tape-measured checkpoints (slam_build_path 9.1) and the 1 m tape line;
    heading from floor marks. Battery charged before each block (`vcgencmd get_throttled` =
    `0x0`; the Pi read `0x50005` on 2026-11-02, *measured*).
  - E2 odometry configs (RQ2): each EKF config live, timed `cmd_vel` 1 m straight ×3 and
    360° spin ×3 per condition; error before SLAM (`/odometry/filtered`) and after SLAM
    (map pose from `slam_toolbox` localisation). Variances calibrated on runs not used for
    evaluation [M26].
  - E3 localiser (RQ3): Nav2 drives the same checkpoint loop with each localiser steering
    its own run (AMCL with `map_server` on the same map), 3 loops per condition; stop error
    at each checkpoint, pairwise ATE between loops [K26] from the bags with [EVO]; wrong starts
    at 10/20/30/40 cm and 10/20/30/40°.
  - E4 step-in (RQ4): a person steps in front of the moving robot at walking pace, 3–5
    times, collision monitor active; stop distance, contacts.
  - Logged on every run: failure onset (drift, jump, lost), recovery once people leave,
    failure position against people's positions.
  - E1 delivery demo: Nav2 home to seat to home, 5 runs; arrival error labelled "rough gains".
  - S hazard table: 6 to 8 hazards, mitigation, the test that proves it.
  - Differences from [K26] and [M26] in a table: lidar (A1M8, 7.05 Hz, 26 to 29 % no-echo,
    *measured*), no wheel encoders, Pi 4, room size, people, live closed loop vs replay,
    run count, motor vibration on the IMU in driven runs.
  - Threats to validity: three runs per cell, one room, people's paths repeatable only
    roughly, rough motor gains, hand-pushed fallback runs if driving fails.
- **Evidence**: [`../docs/report_plan.md`](../docs/report_plan.md) §4;
  [`../docs/slam_build_path.md`](../docs/slam_build_path.md) Stage 9;
  [`../docs/slam.md`](../docs/slam.md) evaluation sections; [`../TASKS.md`](../TASKS.md) §3;
  [`../docs/system/05_config_reference.md`](../docs/system/05_config_reference.md).
- **Owner**: Sherman (E2, E3, metrics), motor teammate (E1), B (people protocol, E4, hazard table).

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
- OI-8: two pushes on 2026-11-01 read about 24 % of true travel (-76 %). *measured*.
  Closed 2026-11-03: the scan format is cleared by live pushes with nobody in the scan;
  a person walking behind the robot pulled rf2o to 25 to 28 % of the real push
  (`evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`, test log 2026-11-03). This is
  the discovery the questions grew from (RQ1, RQ2) and the signature slide.
- Figure: rf2o distance per run, good bag against bad bag (script in
  [`../tools/analysis/`](../tools/analysis/)).

### 5.3 Mapping and localisation on the saved map (already measured)

- First room map and frozen `slam_mapping.yaml` (5.4, 5.5 in the test log). Figure:
  [`../results/maps/2026-10-31_room2.png`](../results/maps/2026-10-31_room2.png).
- Wrong-start recovery: a 30 cm / 20 degree wrong start recovers after a push; 31 degrees
  does not (6.4, 2026-11-01). *measured, ruler-and-eye truth.* Figure:
  [`../results/maps/2026-11-01_room2_home_pose.png`](../results/maps/2026-11-01_room2_home_pose.png).
  Gives the convergence basin; one case per angle, so state that.

### 5.4 RQ1 Impact of people

RESULT: pending E2, E3. One table pulling the empty-vs-people difference out of E2 and E3:
method, error empty, error with people, change, localisation failures. Plus the room figure:
where failures happened against the people's paths. Already measured: OI-8 (5.2).

### 5.5 E2 Odometry configs (RQ2)

RESULT: pending E2. Table skeleton: config (rf2o + IMU, rf2o only, IMU only, none) ×
condition (empty, people), distance and heading error vs tape, **before SLAM
(`/odometry/filtered`) and after SLAM (map pose)**. [M26] found the EKF cut translational
APE RMSE by 60–75 % before SLAM but changed it by only −2.6 to +1.6 % after SLAM with SLAM
Toolbox ([`literature_notes.md`](literature_notes.md)): test whether that holds here, and
whether it still holds with people.

### 5.6 E3 Localiser (RQ3)

RESULT: pending E3. Tables: (a) localiser × condition: checkpoint stop error, pairwise ATE
between loops against [K26] (~0.20–0.23 m, to check from the paper), lost yes/no; (b)
wrong-start grid (offset × angle), recovered yes/no per localiser. `slam_toolbox` baseline
already measured in 5.3. Failure-mode table: onset (drift, jump, lost) per localiser.

### 5.7 E4 Step-in safety (RQ4) and hazard table

RESULT: pending E4. Table: step-in run, robot speed, stop distance, contact yes/no, against
the 0.20 m stop zone. Hazard table skeleton: hazard, mitigation (structural), test, pass or
fail, RESULT: pending S. Hazard framing from SOTIF (ISO 21448) and ISO 13482: to check before
citing. Zone sizing at walking pace: `reports/MPC planners for dynamic humans.md` (inference,
not measured).

### 5.8 E1 Delivery demo

RESULT: pending E1. Table skeleton: run 1 to 5, success, arrival error at each checkpoint
(labelled "rough gains"), time.

- **Evidence**: [`../docs/test_log.md`](../docs/test_log.md),
  [`../notes/notes.md`](../notes/notes.md), [`../results/`](../results/),
  [`../evidence/`](../evidence/), [`../tools/analysis/`](../tools/analysis/),
  [`../docs/CA3.md`](../docs/CA3.md) OI-4, OI-6, OI-8.
- **Owner**: Sherman (5.1 to 5.6), B (5.7, hazard table), motor teammate (5.8 E1, drive).

## 6 Discussion

- **Purpose**: compare ours with the papers per RQ, say why, state limits.
- **Rubric**: content 40 % (in-depth thinking), conclusions 25 %.
- **Goes in**: one subsection per RQ, then limits. Each subsection: what we found, what
  the paper found, the most likely reason for any gap, then the Our take box. Write the
  box as a hypothesis until the experiment has run, then keep it, revise it or replace it
  with what the data said.
- **Limits**: five runs, one room, hand ground truth in early tests, cheap lidar, Pi
  under-voltage, motor timing.

### 6.1 RQ1 Impact of people

> **Our take.** *Hypothesis:* the customer is the obstacle: with people walking, checkpoint
> error and localisation failures grow for every method, because scan matching assumes a
> static world and a person is a moving wall (OI-8: rf2o at 25 to 28 % of a push with a
> person behind, *measured*). *Confirmed by:* RQ1 table, error clearly larger with people.
> *Killed by:* error with people about equal to empty for most methods. RESULT: pending E2, E3.

### 6.2 RQ2 Odometry

> **Our take.** *Hypothesis:* the IMU matters most when the scan is worst. In an empty room
> SLAM hides the odometry, as [M26] found; with people it cannot, and the gyro carries the
> heading (hand turn: gyro 360.2°, rf2o 352.9°, *measured*). *Confirmed by:* E2 after-SLAM
> gain from the IMU larger with people than empty. *Killed by:* the same gain in both
> conditions, or none. RESULT: pending E2.

### 6.3 RQ3 Localiser

> **Our take.** *Hypothesis:* the two localisers fail differently among people: AMCL's
> particles spread and drift, `slam_toolbox`'s scan graph holds then jumps. A product should
> ship the one with the smaller error among people, not the one that wins in an empty room.
> *Confirmed by:* E3 different failure onsets or a ranking that flips between conditions.
> *Killed by:* the same behaviour in both. Compare pairwise ATE with [K26] directionally.
> RESULT: pending E3.

### 6.4 RQ4 Safety

> **Our take.** *Hypothesis:* the stop zone, not the localiser, is the safety-critical part:
> a person stepping in at walking pace gets closer than the 0.20 m zone allows for, even when
> localisation is fine. *Confirmed by:* E4 stop distances near or under 0.20 m. *Killed by:*
> stops with a wide margin. RESULT: pending E4.

### 6.5 E1 Delivery demo

> **Our take.** *Hypothesis:* the robot succeeds because the world is simplified (taped
> home mark, mapped room, 0.15 m/s), not because the localiser is strong; the limiting
> factor is integration (motors, power, start-up), not algorithms. *Confirmed by:* E1
> failures traced to power, start-up or calibration rather than pose error. *Killed by:*
> failures traced to localisation drift. RESULT: pending E1.

- **Evidence**: section 5; [`../docs/CA3.md`](../docs/CA3.md) OI-4, OI-6, OI-8;
  [`../docs/system/06_troubleshooting.md`](../docs/system/06_troubleshooting.md);
  [`../docs/slam_journal.md`](../docs/slam_journal.md).
- **Owner**: Sherman (6.1 to 6.3), B (6.4), motor teammate (6.5), A (limits, edit).

## 7 Our position

- **Purpose**: 3 to 5 opinions, each backed by data, for the "your unique thoughts" criterion.
- **Rubric**: content 40 %, conclusions 25 %.
- **Goes in**: each position as a short paragraph (claim, the data behind it, the
  real-AV consequence) followed by an Our take box. A position without a measurement
  behind it is deleted, not softened.

> **Our take (how 2D SLAM should be evaluated).** *Hypothesis:* pairwise ATE and replay
> hide errors that live runs against ground truth show. *Confirmed by:* E3 checkpoint
> error against pairwise ATE (E3); live runs against replays (RESULT: pending E2, E3).
> *Killed by:* both metrics tell the same story.

> **Our take (empty-room results mislead).** *Hypothesis:* published results transfer to
> a cheap lidar in an empty room, at least in ranking, but the ranking of methods changes once
> people walk around the robot, so empty-room benchmarks pick the wrong method for delivery.
> *Confirmed by:* E2 or E3 rankings that differ between conditions (RESULT: pending E2, E3).
> *Killed by:* the same ranking in both conditions.

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
  - 4 numbered conclusions, one per RQ, plus one line on E1, each citing the table or
    figure in section 5. If a result contradicts a paper, it is a conclusion, not a
    footnote. RESULT: pending E1 to E4.
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
| Higher-rate or higher-echo lidar; lidar-degradation study (dropped from this study) | 7.05 Hz, 26 to 29 % no-echo (*measured*) | to check | to estimate |
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

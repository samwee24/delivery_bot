# CA3 report and presentation plan

**Tentative, agreed 2026-11-03; revisit after OI-8 is closed and after the E1 runs.**
Decision D8 in [CA3.md](CA3.md). Report outline: [../report/CA3_report.md](../report/CA3_report.md).
Slides: [../report/slides_outline.md](../report/slides_outline.md). Sources:
[../report/literature_notes.md](../report/literature_notes.md). Robot phases: [plan.md](plan.md);
SLAM tasks: [slam_build_path.md](slam_build_path.md) Stage 9.

Every number in this file is a **target**, not a result, until a dated row in
[test_log.md](test_log.md) says otherwise (AGENTS rule 4).

## 1. The brief and how this plan scores

MA4890 group project: an oral presentation and the CA3 written report, both due at the end
of Week 13. Presentation estimated Thu 2026-11-12, 9:30–12:30 (**to check on NTULearn**).

| Item | Brief | How this plan meets it |
| --- | --- | --- |
| Presentation (40 % of module) | 10–15 min + 5 min Q&A; videos ≤ 2 min; each student presents their own contribution | 15-min script, one experiment block per presenter, clips under 120 s |
| Report (20 %) | One per group; NTULearn template for format only; any type; no length limit | Experimental study with results, in template order |
| Expected content | Topic overview, state of the art, product comparison, technical information, future trends | Background section, product table, system section, roadmap and trends |
| "Most importantly" | Own insights and unique thoughts | Original data compared with published results; a labelled **Our take** per question; an "Our position" section |

| Rubric line | Weight | Top band | How we reach it |
| --- | --- | --- | --- |
| Content | 40 % | Excellent material, extensive research, in-depth thinking | Re-evaluate published results ([K26], [M26], [Y21]) on our robot, live, with ground truth; critique how they were measured |
| Conclusions | 25 % | Explains conclusions and elaborates future work | Numbered findings tied to results; costed roadmap |
| Presentation | 20 % | Collaboration and logical flow | One thread: mission → requirements → evidence → verdict; claim headlines; rehearsed handoffs |
| Peer assessment | 15 % | Each member contributes | Every member owns an experiment or section and one "Our take" |

## 2. Options considered

| Option | What | Verdict |
| --- | --- | --- |
| A. Survey | Papers only | Rejected: throws away our only unique asset, original data |
| B. Build report | "We built a delivery robot", demo | A lab report with little research depth; its demo is kept inside C+ |
| **C. Re-evaluation against published baselines** | Test [K26]/[M26] findings on our robot (E3 partial replication, E2 analogue), extend to people [Y21], delivery as the application | **Chosen core** |
| D. Mission matrix | Eight mission experiments | Too wide and shallow for 9 days |
| E. Safety case | SOTIF / ISO 13482 analysis + tests | Too narrow alone; kept as a one-page hazard table |
| F. Lidar vs camera | Add camera localisation and compare | Strongest idea, worst timing (new build); goes to future work |

**C+** = C, plus B's delivery demo, plus E's hazard table. It is academic by construction (a
published method, our data, a direct comparison); every gap between our data and the paper
is a defensible insight; four experiments done well beat eight done thinly; and the SLAM
half (E2, E3) still works from hand-pushed runs if driving slips.

## 3. Title and research questions

**Title (tentative):** *Re-evaluating EKF-Fused 2D LiDAR SLAM on a Low-Cost Indoor Delivery Robot: Repeatability, Inertial Contribution and the Effect of Dynamic Human Obstacles*
**Fallback** (if E1–E4 do not run in time): *Localisation and Safety Lessons for Autonomous Vehicles from a Low-Cost Indoor Delivery Robot*
**Slide hook:** "Published 2D SLAM results were measured under conditions a cheap delivery robot never sees. What changes?"

**Framing word:** *re-evaluation against published baselines*, not "replication". E3 is a
partial replication of [K26]'s "AMCL off" condition (same stack, but live, cheap lidar, with
ground truth); E2 is an analogue of [M26] (no wheel encoders). Every comparison is
**directional** (same trend or not, and why), backed by a "differences from the paper"
table in the Method section.

| RQ | Question | Anchor |
| --- | --- | --- |
| RQ1 Repeatability | Does the [K26] "AMCL off" stack (rf2o + IMU → `robot_localization` EKF → `slam_toolbox`, no wheel encoders, Jazzy) reach comparable run-to-run repeatability on an A1M8 (7.05 Hz, 26–29 % no-echo, measured) and a Pi 4? | [K26] |
| RQ2 IMU | Does fusing the MPU6050 gyro improve the odometry, and does that gain survive SLAM? [M26] (wheel odometry ± IMU) saw a large gain before SLAM and almost none after | [M26], analogue |
| RQ3 People | How much do people in the room degrade localisation, delivery and safety? | [Y21] |
| RQ4 Mission | Home → seat → home, 5 runs in a row, within 15 cm, no human touch? | [plan.md](plan.md) phase 7 |

## 4. Experiments

| # | Experiment | Protocol | Metrics | Target (not a result) | Build path | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Delivery mission | 5 driven runs home → seat → home | Success %, arrival error at checkpoints, time | 5/5, ≤ 15 cm | 9.2 | Motor teammate |
| E2 | IMU ablation | EKF with and without the IMU on the E1 runs: one live run per config, plus **≥ 3 replays per config per bag** | ATE, RPE, heading error ([EVO]), before and after SLAM | Compare with [M26]: 60–75 % gain before SLAM, −2.6 to +1.6 % after | 9.4 | Sherman |
| E3 | Repeatability | The same 5 runs | Pairwise ATE, map IoU; plus checkpoint error (ground truth K26 lacks) | Compare with [K26]: SLAM Toolbox pairwise ATE about 0.20–0.23 m | 9.3 | Sherman |
| E4 | People in the room | 5 runs with 1–2 people walking; one person stepping in front | Arrival error vs E1, localisation failures, stop distance, contacts | Zero contacts | 9.7 | B |
| S | Hazard table | 6–8 hazards → mitigation → the test that proves it | Pass / fail | All pass | — | B or C |
| opt | Echo rate by material | Black, glass, white, fabric at fixed range and angle, `tools/probe_echo_rate.py` | Return % | — | — | Anyone, ~2 h |

**What the papers actually test** (verified in [literature_notes.md](../report/literature_notes.md)):
[K26] compares AMCL feedback on/off with the IMU fused in both, mostly offline replay of an
Ouster OS-1 cut to 2D, no ground truth; its "AMCL off" condition is our stack, so E3 is a
replication. [M26] ablates wheel odometry vs wheel odometry + IMU on the public MIT Stata
dataset; we have no encoders, so E2 is an analogue. [Y21]: GMapping corridor map error 5.90 cm
with people filtered vs 80.24 cm unfiltered; E4 is their unfiltered case.

**Why ≥ 3 replays in E2:** on 2026-11-03 three identical replays of one bag read 0.679, 0.592
and 0.531 m (spread about 12 %, [notes](../notes/notes.md)). A single replay per condition
cannot separate the two configs; report the mean and the spread, and lean on the live runs.

### Shared protocol

| Rule | Detail |
| --- | --- |
| Ground truth | 5 tape-measured checkpoints (home + seats), [Stage 9.1](slam_build_path.md#91-survey-floor-checkpoints) |
| Frozen config | One parameter set for every condition, frozen before **2026-11-06**; commit hash per run ([K26] rule, see [slam.md](slam.md)) |
| Bags | `~/bags/YYYY-MM-DD_<exp>_run<N>`; one `test_log.md` row per run with command and hash |
| Metrics | `evo` APE/RPE [EVO]; map IoU per [K26] |
| Power | Charged battery every run; check `vcgencmd get_throttled` is `0x0` first |
| Safety | Motors only through the motor node watchdog; first live test with wheels raised; kill switch in reach |

## 5. Roles

| Person | Owns | Presents | Own "Our take" |
| --- | --- | --- | --- |
| Sherman | SLAM stack, E2, E3, analysis with `evo` | Re-evaluation block | RQ1, RQ2 |
| Motor teammate (TBD) | Motors, calibration, Nav2, delivery script, E1 | System + mission block | RQ4 |
| A (TBD) | Background, product table, trends, roadmap | Opening and closing | Industry comparison |
| B (TBD) | E4, hazard table | People + safety block, "Our position" | RQ3 |
| C (TBD, if any) | Hazard table, report editing, references | Shared with B | Safety |

Each person owns at least one experiment or section and writes one "Our take" (peer
assessment is 15 %).

## 6. Schedule

| Day | Robot | Others |
| --- | --- | --- |
| Tue 3 Nov | Charge battery (Pi read `0x50005`); close OI-8 (push with `angle_compensate:=false`, with and without a person in the scan); tape checkpoints | Read [K26], [M26], [Y21]; start the product table |
| Wed 4 | Motors in; first live test wheels raised; calibration (dead zone, per-side gain, 1 m straight) | Background draft |
| Thu 5 | Nav2: 5 goals within 15 cm; delivery script | Hazard table draft |
| Fri 6 | **Freeze config.** E1 runs (also E3 data); E2 live runs | Report skeleton in the template |
| Sat 7 | E4 runs, safety-stop test, all video clips | Slide skeleton |
| Sun 8 | `evo` analysis, E2 replays, figures | Sections 1–3 |
| Mon 9 | Results, discussion, "Our take" boxes | Edit, check references |
| Tue 10 | Full draft; slides done | Rehearsal 1 |
| Wed 11 | Fixes | Rehearsal 2, Q&A drill |
| Thu 12 | Present | — |
| End of Week 13 | Submit report, slides, peer assessment | — |

| Risk | Fallback |
| --- | --- |
| OI-8 not fixed by Wed | E2 on the good 2026-10-31 bag (several replays); report OI-8 as a finding about rf2o's static-scene assumption |
| Nav2 unreliable by Fri | Teleop on taped routes for E2–E4; E1 reported as partial with the named blocker |
| Under-voltage, lidar start hang (OI-6) | Charged battery; wait 20 s before a lidar restart |
| Results contradict the papers | Best slide: explain why |
| Time | Drop the echo-rate test first, then E4's step-in half |

## 7. Candidate insights

Hypotheses until the data decides. Never present one as a finding before its experiment ran.

| Insight | Confirmed by | Killed by |
| --- | --- | --- |
| The [K26]/[M26] results transfer (or do not) to a lidar with a much lower echo rate | E3 spread close to (or far from) K26; E2 gain close to (or far from) M26 | — (either way is a result; name the reason) |
| "The customer is the obstacle": people degrade localisation and are the main safety hazard | E4 arrival error and failures clearly above E1 | E4 ≈ E1 |
| Redundancy earns its cost | E2 shows the IMU lowers error after SLAM, not only before | E2 gain vanishes after SLAM, as in [M26]: then "SLAM hides odometry quality; the IMU matters only when the map can't correct", also a take |
| Delivery robots win by simplifying their world | Product table (markers, mapped rooms, slow speed) + E1 success | E1 fails for reasons a simpler world would not fix |
| Published 2D SLAM evaluation misses what matters for deployment (no ground truth in [K26]; covariances fitted on test data in [M26]; replay not live) | Our checkpoint error disagrees with what pairwise ATE alone suggests, or live differs from replay | Checkpoint error and pairwise ATE tell the same story |
| Integration, not algorithms, was the hard part | Failure log: OI-8, lidar start hang (OI-6), power | Most failures trace to the algorithms themselves |

## 8. Deliverables

- [ ] Slides (claim headlines, "Our take" marker, paper keys in footers)
- [ ] Video clips ≤ 120 s total, offline copies
- [ ] Report in the NTULearn template (download it)
- [ ] References checked against [literature_notes.md](../report/literature_notes.md)
- [ ] Q&A answers (8 questions) drafted and drilled
- [ ] Two full rehearsals with timing per presenter
- [ ] Peer assessment submitted by each member
- [ ] Final title chosen after E2/E3

# CA3 report and presentation plan

**Revised 2026-11-09 (evening): plan H, people as the axis, live runs as the results (§2).** Every method runs live on the robot in an empty room and with people walking; replay of existing bags is background only. Plan G of the same morning (method × condition matrix with offline replays and a lidar-degradation axis) is kept in §2 for the record. OI-8 closed 2026-11-03: the scan format is cleared; a person walking behind the robot pulled rf2o to 25–28 % of the real push ([notes](../notes/notes.md), `evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`). That is the first measured data point for RQ1 (people).
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
| G. Method × condition matrix (2026-11-09 morning) | C widened: compare alternatives (4 odometry configs, 2 localisers, degraded lidar) under conditions (empty, people), mostly by offline replay | Superseded by H the same evening: replay is not the robot, and the degradation axis was simulated and tied to nothing we discovered |
| **H. People as the axis, live** (2026-11-09 evening) | G's methods (odometry configs, localisers), run **live on the robot**, each in an empty room and with people walking; plus a step-in safety test. Lidar degradation goes to future work | **Chosen**: OI-8 (a person behind the robot cut rf2o to a quarter) is our one real discovery, and customers standing around the robot is the most delivery-specific condition; live closed-loop runs measure the robot, not a replay that reads ~71 % of live |

**H** keeps C+'s parts (delivery demo, hazard table) and C's papers; each paper anchors one
question; every result slide shows the same comparison, empty against people.

**C+** (2026-11-03) = C, plus B's delivery demo, plus E's hazard table. It is academic by construction (a
published method, our data, a direct comparison); every gap between our data and the paper
is a defensible insight; four experiments done well beat eight done thinly; and the SLAM
half (E2, E3) still works from hand-pushed runs if driving slips. (2026-11-09: driven runs are now the main method, hand-pushing the fallback, §4.)

## 3. Title and research questions

**Main question (plan H):** *A cheap delivery robot works in an empty room. What happens when people move around it, which part breaks, and what defends against it?*
**Title (tentative):** *The Customer Is the Obstacle: Localisation and Safety of a Low-Cost Delivery Robot Among People*
**Fallback** (if driving fails): *Localisation and Safety Lessons for Autonomous Vehicles from a Low-Cost Indoor Delivery Robot*
**Slide hook:** "Published 2D SLAM results were measured in empty rooms or on replayed data. Our robot's customers walk around it. What breaks?"

**Storyline** (slides and report): gap (hook) → field and products → what we built →
the discovery (OI-8: a person behind the robot) → four findings, each *empty vs people → paper
→ gap → why → Our take* → our position → future work → verdict.

**Framing word:** *re-evaluation against published baselines* stays: K26, M26 and Y21 each
anchor one question; comparisons with them are directional, backed by a "differences from
the paper" table. Numbering changed twice on 2026-11-09; `report/` follows plan H.

| RQ | Question | Point it can make (hypothesis) | Anchor |
| --- | --- | --- | --- |
| RQ1 Impact | How much do people hurt the robot? Checkpoint error and localisation failures, empty room against 1–2 people walking, for every method below | The headline number: "the customer is the obstacle" | [Y21] (5.90 vs 80.24 cm map error, people filtered vs not); OI-8 |
| RQ2 Odometry | Which part breaks? Scan odometry against the IMU: rf2o + IMU, rf2o only, IMU only, none (scan matching alone), empty vs people | OI-8 says rf2o breaks; does the IMU hide it, or does SLAM? [M26]'s "the gain vanishes after SLAM" may hold only in an empty room | [M26], analogue (no encoders) |
| RQ3 Localiser | Which localiser holds up? `slam_toolbox` localisation against AMCL, each steering its own Nav2 loop, empty vs people; plus wrong starts | A particle filter and a scan graph should fail differently around moving bodies; which a product should ship | [K26] (AMCL on/off, ~0.20–0.23 m pairwise ATE) |
| RQ4 Safety | Does it stay safe? Stop distance and contacts when a person steps in front, against the 0.20 m stop zone | The stop zone, not the localiser, is the safety-critical part | `reports/MPC planners for dynamic humans.md` (zone too small at walking pace, inference) |
| E1 demo | Home → seat → home, driven: proof the system works end to end, and the video | Not a research question | [plan.md](plan.md) phase 7 |

**Also logged on every run, no extra cost:** how each failure starts (slow drift, sudden
jump, lost), whether the robot recovers once people leave, and where in the room it happens
against where people were (failure-mode table and a room figure).

## 4. Experiments

**The matrix (plan H).** Every cell is a **live run on the robot**, recorded as a bag.
Three runs per cell (live runs are slow; report effect sizes and the spread, not
significance).

| Method ↓ / condition → | Empty room | 1–2 people walking |
| --- | --- | --- |
| Odometry: rf2o + IMU · rf2o only · IMU only · none | E2 → RQ2, RQ1 | E2 → RQ2, RQ1 |
| Localiser: `slam_toolbox` · AMCL | E3 → RQ3, RQ1 | E3 → RQ3, RQ1 |
| Safety stop | — | E4 step-in → RQ4 |

| # | Experiment | Protocol (live) | Metrics | Target (not a result) | Build path | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Delivery demo | Nav2 home → seat → home, 5 runs | Success %, arrival error at checkpoints (tape), time; labelled "rough gains" | 5/5, ≤ 15 cm | 9.2 | Motor teammate |
| E2 | Odometry configs (RQ2) | Each EKF config loaded live (`ekf_params_file`, or no EKF); timed `cmd_vel` 1 m straight ×3 and 360° spin ×3 per config per condition; `slam_toolbox` localisation on the saved map running alongside for the after-SLAM pose | Distance and heading error vs tape and floor marks, from `/odometry/filtered` (before SLAM) and the map pose (after SLAM) | Compare with [M26]: 60–75 % gain before SLAM, −2.6 to +1.6 % after | 9.4 | Sherman |
| E3 | Localiser (RQ3) | Nav2 drives the same checkpoint loop, once per localiser (`slam_toolbox` localisation, AMCL with `map_server` on the same map), 3 loops per localiser per condition, rf2o + IMU odometry; wrong starts at 10/20/30/40 cm and 10/20/30/40° per localiser, empty room | Stop error at each checkpoint (tape), pairwise ATE between loops (from bags, [EVO]), lost or not, recovery yes/no | Compare with [K26]: ~0.20–0.23 m pairwise ATE; `slam_toolbox` baseline 30 cm / 20° recovers, 31° not (2026-11-01, hand-pushed) | 9.3 | Sherman |
| E4 | Step-in safety (RQ4) | One person steps in front of the moving robot at walking pace, 3–5 times; Nav2 collision monitor active | Stop distance, contacts, near-misses | Zero contacts | 9.7 | B |
| S | Hazard table | 6–8 hazards → mitigation → the test that proves it | Pass / fail | All pass | — | B or C |

**People protocol** (the same every run, so "people" is one condition): 1–2 people walk at
normal pace on two fixed paths taped on the floor, one crossing the route and one behind the
robot's start; nobody touches the robot; the walker starts when the robot starts.

**Runs:** E2 4 configs × 2 conditions × 6 = 48 short runs; E3 2 × 2 × 3 = 12 loops plus
2 × 8 wrong starts; E4 3–5; E1 5. About 4–5 h of robot time with battery swaps.

**Live switches to build first:** `base.launch.py` takes `ekf_params_file` and `ekf:=false`
(static identity `odom → base_footprint`); `navigation.launch.py` takes `localizer:=slam|amcl`
(AMCL plus `map_server` on `2026-10-31_room2.yaml`; the driving default stays `slam`); EKF
variants in `delivery_bot_bringup/config/ekf_variants/`; a run-sheet script that starts one
cell, records the bag and prints the test_log row. Motor safety fixed first ([`slam_build_path.md`](slam_build_path.md) R.1).

**Dropped to future work:** lidar degradation (old RQ1/E5): simulated cuts are cleaner than a
real cheap lidar, the runs are expensive, and it tied to nothing we discovered.

**What the papers actually test** (verified in [literature_notes.md](../report/literature_notes.md)):
[K26] compares AMCL feedback on/off with the IMU fused in both, mostly offline replay of an
Ouster OS-1 cut to 2D, no ground truth; E3 runs live with checkpoint truth. [M26] ablates
wheel odometry vs wheel odometry + IMU on the public MIT Stata dataset; we have no encoders,
so E2 is an analogue. [Y21]: GMapping corridor map error 5.90 cm with people filtered vs
80.24 cm unfiltered; our people condition is their unfiltered case, on localisation.

### Data status (checked 2026-11-09, `ssh robot@100.83.14.99 'ls -1t ~/bags'`)

The bags on the Pi (10-31 to 11-03: hand pushes, a hand turn, two map bags) are **background
only**: the OI-8 story and the replay-noise caveat (three replays of one bag 0.679 / 0.592 /
0.531 m). Every plan-H result comes from the driven session, which has not happened yet.
Every live run is also bagged, so offline replays of the driven bags stay possible later.

### Shared protocol

| Rule | Detail |
| --- | --- |
| Ground truth | 5 tape-measured checkpoints (home + seats), [Stage 9.1](slam_build_path.md#91-survey-floor-checkpoints) |
| Frozen config | One parameter set per method, frozen before the driven session (2026-11-10); commit hash per run ([K26] rule, see [slam.md](slam.md)) |
| Bags | `~/bags/YYYY-MM-DD_<exp>_run<N>`; one `test_log.md` row per run with command and hash |
| Metrics | Primary: tape-measured error at checkpoints and on the 1 m line; secondary: `evo` APE/RPE from the bags [EVO] |
| Power | Charged battery every run; check `vcgencmd get_throttled` is `0x0` first |
| Safety | Motors only through the motor node watchdog; first live test with wheels raised; kill switch in reach |

## 5. Roles

| Person | Owns | Presents | Own "Our take" |
| --- | --- | --- | --- |
| Sherman | SLAM stack, live switches, run sheet, E2, E3, analysis | Odometry and localiser block | RQ1, RQ2, RQ3 |
| Motor teammate (TBD) | Motors, calibration, Nav2, delivery script, E1 | System + mission block | E1 |
| A (TBD) | Background, product table, trends, roadmap | Opening and closing | Industry comparison |
| B (TBD) | People protocol, E4, hazard table (uses `reports/MPC planners for dynamic humans.md`) | OI-8, safety block, "Our position" | RQ4 |
| C (TBD, if any) | Hazard table, report editing, references | Shared with B | Safety |

Each person owns at least one experiment or section and writes one "Our take" (peer
assessment is 15 %).

## 6. Schedule

**Reset 2026-11-09 (plan H).** Results come from one driven session; everything before it
is build and safety work.

| Day | Robot | Others |
| --- | --- | --- |
| Mon 9 Nov | Motor safety fixes (dry run back, lidar stop, `/cmd_vel` type); live switches (`ekf_params_file`, `ekf:=false`, `localizer:=amcl`); run sheet; tape checkpoints and people paths | Report §1–4, product table, hazard table draft, slide skeleton |
| Tue 10 | **Driven session.** Wheels raised, then a 1 m straight with the switch in reach. Freeze config. E2 (48 short runs), E3 (12 loops + 16 wrong starts), E4 step-ins, E1, video clips | People for the people condition |
| Wed 11 | Morning: re-runs of failed cells. Then tape numbers into tables, `evo` on bags, figures, Our take per RQ; rehearsal 1 | Rehearsal 1 and 2 |
| Thu 12 | Present (morning) | — |
| End of Week 13 | Report with the full results; submit report, slides, peer assessment | — |

| Risk (plan H) | Fallback |
| --- | --- |
| Motor safety not fixed by Tue | No driven runs; E2 by stick-pushing (nobody behind the robot except in people runs); E3 and E1 reported as partial with the named blocker |
| Driving fails on the floor | Same fallback; the existing bags and OI-8 carry RQ1 and RQ2 qualitatively |
| AMCL bring-up not ready | E3 becomes `slam_toolbox` empty vs people only; AMCL to future work |
| 4–5 h of robot time does not fit | Cut E2 spins in the people condition first, then E3 wrong starts to 10/20/30°, then E2's "none" config |
| Motor vibration reaches the IMU | Compare driven with driven only; list it in "differences from the paper" |
| Under-voltage, lidar start hang (OI-6) | Charged battery, spare; wait 20 s before a lidar restart |

Original schedule (2026-11-03):

| Day | Robot | Others |
| --- | --- | --- |
| Tue 3 Nov | Charge battery (Pi read `0x50005`); ~~close OI-8~~ (done: person behind the robot); tape checkpoints | Read [K26], [M26], [Y21]; start the product table |
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
| People near the robot during hand-pushed fallback runs (fallback only, 2026-11-09) | Push with a stick or string, nobody within the scan; OI-8 showed a person behind cuts rf2o to about a quarter |
| Nav2 unreliable by Fri | Teleop on taped routes for E2–E4; E1 reported as partial with the named blocker |
| Under-voltage, lidar start hang (OI-6) | Charged battery; wait 20 s before a lidar restart |
| Results contradict the papers | Best slide: explain why |
| Time | Drop the echo-rate test first, then E4's step-in half |

## 7. Candidate insights

Hypotheses until the data decides. Never present one as a finding before its experiment ran.

| Insight | Confirmed by | Killed by |
| --- | --- | --- |
| "The customer is the obstacle": people degrade localisation and are the main safety hazard | RQ1: checkpoint error and failures clearly larger with people for every method. Early evidence: OI-8, rf2o read 0.242 of 0.862 m and 0.307 of 1.222 m with a person behind (measured, 2026-11-03) | Error with people ≈ empty for most methods |
| The IMU matters most when the scan is worst | RQ2: the IMU's gain (rf2o + IMU vs rf2o only) larger with people than empty, after SLAM too | Gain the same in both conditions; or none, as [M26] found after SLAM |
| SLAM hides bad odometry, until people arrive | RQ2: after-SLAM error equal across configs when empty, spread apart with people | Configs differ after SLAM even when empty |
| Graph matching and a particle filter fail differently among people | RQ3: different failure modes (drift vs jump) or error sizes for `slam_toolbox` and AMCL with people | Both behave the same |
| The stop zone, not the localiser, is the safety-critical part | RQ4: step-in stop distance close to or under the 0.20 m zone, while localisation error stays small | Stops with a wide margin |
| The [K26]/[M26] results transfer (or do not) to a cheap lidar, live | E3 loop spread close to (or far from) K26; E2 gain close to (or far from) M26 | — (either way is a result; name the reason) |
| Delivery robots win by simplifying their world | Product table (markers, mapped rooms, slow speed) + E1 success | E1 fails for reasons a simpler world would not fix |
| Published 2D SLAM evaluation misses what matters for deployment (no ground truth and no people in [K26]; replay not live) | Our live checkpoint error with people disagrees with what empty-room or replay numbers suggest | They tell the same story |
| Integration, not algorithms, was the hard part | Failure log: OI-8, lidar start hang (OI-6), power, motor safety | Most failures trace to the algorithms themselves |

## 8. Deliverables

The deliverables checklist is in [`slam_build_path.md`](slam_build_path.md) Progress, section D (2026-11-09).

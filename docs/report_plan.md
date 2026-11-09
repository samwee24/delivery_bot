# CA3 report and presentation plan

**Revised 2026-11-09: method-by-condition comparison (option G, §2).** The 2026-11-03 plan checked one number per paper; it is widened to compare alternatives (odometry sources, localisers, lidar quality) under conditions (empty room, people, degraded scans). Schedule reset in §6: no E1–E4 bags existed on 2026-11-09. OI-8 closed 2026-11-03: the scan format is cleared; a person walking behind the robot pulled rf2o to 25–28 % of the real push ([notes](../notes/notes.md), `evidence/lidar/2026-11-03_oi8_bad_bags_pushwall.txt`). That is a first measured data point for E4.
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
| **G. Method × condition matrix** (2026-11-09) | C widened: compare alternatives (4 odometry configs, 2 localisers, degraded lidar) under conditions (empty, people), papers as reference points inside the matrix | **Chosen**: C's single-number checks gave yes/no answers with little room for insight; most cells are offline replays of bags, YAML switches only |

**G** keeps C+'s parts (delivery demo, hazard table) and C's papers, but each paper becomes
one reference point in a comparison instead of the whole question.

**C+** (2026-11-03) = C, plus B's delivery demo, plus E's hazard table. It is academic by construction (a
published method, our data, a direct comparison); every gap between our data and the paper
is a defensible insight; four experiments done well beat eight done thinly; and the SLAM
half (E2, E3) still works from hand-pushed runs if driving slips. (2026-11-09: driven runs are now the main method, hand-pushing the fallback, §4.)

## 3. Title and research questions

**Main question (2026-11-09):** *What does a cheap delivery robot need to localise reliably in a real room with people in it, and where do published 2D SLAM results stop applying?*
**Title (tentative):** *Published SLAM Meets a Cheap Robot and Real People: What Holds, What Breaks, and What a Delivery Robot Needs*
**Formal title (report):** *Odometry, Localiser and LiDAR Quality Under Dynamic Human Obstacles: A Comparative Study on a Low-Cost Indoor Delivery Robot*
**Fallback** (if live runs slip): *Localisation and Safety Lessons for Autonomous Vehicles from a Low-Cost Indoor Delivery Robot*
**Slide hook:** "Published 2D SLAM results were measured under conditions a cheap delivery robot never sees. What changes?"

**Storyline** (slides and report): gap (hook) → field and products → what we built →
four findings, one per presenter, each *our result → paper → gap → why → Our take* →
OI-8 as the signature slide → our position → conclusions and future work.

**Framing word:** *re-evaluation against published baselines*, not "replication". E3 is a
partial replication of [K26]'s "AMCL off" condition (same stack, but live, cheap lidar, with
ground truth); E2 is an analogue of [M26] (no wheel encoders). Every comparison is
**directional** (same trend or not, and why), backed by a "differences from the paper"
table in the Method section.

RQ numbers changed on 2026-11-09. Old → new: RQ1 repeatability → part of RQ3; RQ2 IMU →
RQ2 (widened); RQ3 people → RQ4; RQ4 mission → E1 demo. `report/CA3_report.md` and
`report/slides_outline.md` still use the old numbers until they are rewritten.

| RQ | Question | Point it can make (hypothesis) | Anchor |
| --- | --- | --- | --- |
| RQ1 Lidar spec | How cheap can the lidar be? Degrade the scans offline (fewer beams, lower rate, shorter range) and find where each method breaks | The minimum sensor spec for a delivery robot, from data | Our A1M8 (7.05 Hz, 26–29 % no-echo, measured) against [K26]'s Ouster cut to 2D |
| RQ2 Odometry | Which odometry matters, and when? rf2o only, rf2o + IMU, IMU heading only, none (`slam_toolbox` scan matching alone), in an empty room and with people | [M26]'s "the IMU gain vanishes after SLAM" may hold only in easy conditions | [M26], analogue (no encoders) |
| RQ3 Localiser | Particle filter or graph matching on a cheap lidar? AMCL against `slam_toolbox` localisation: checkpoint error, run-to-run repeatability, wrong-start recovery | Which localiser a low-cost product should ship | [K26] (AMCL on/off; ~0.20–0.23 m pairwise ATE) |
| RQ4 People | What do people do to it? The RQ2/RQ3 comparisons with people walking, plus stop distance and contacts | "The customer is the obstacle": people are the main localisation fault (OI-8) and the main hazard | [Y21] (5.90 vs 80.24 cm map error, filtered vs unfiltered) |
| E1 demo | Home → seat → home, driven: proof the system works end to end, and the video | Not a research question | [plan.md](plan.md) phase 7 |

## 4. Experiments

**The matrix (2026-11-09).** Every method runs on the same bags, offline, **≥ 3 replays per
cell**. Methods are YAML switches; AMCL runs as a separate offline config only
(`nav2_params.yaml` for driving keeps AMCL removed).

| Method ↓ / condition → | Empty room | People walking | Degraded lidar (beams / rate / range) |
| --- | --- | --- | --- |
| Odometry: rf2o only · rf2o + IMU · IMU heading only · none | RQ2 | RQ2, RQ4 | RQ1 |
| Localiser: `slam_toolbox` · AMCL | RQ3 | RQ3, RQ4 | RQ1 |

| # | Experiment | Protocol | Metrics | Target (not a result) | Build path | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Delivery demo | Driven runs home → seat → home (5 if motors allow) | Success %, arrival error at checkpoints, time | 5/5, ≤ 15 cm | 9.2 | Motor teammate |
| E2 | Odometry comparison (RQ2) | 4 EKF configs replayed on every bag: the existing 1 m tape pushes and 360° turn, plus **driven** 1 m straights and 360° spins (timed `cmd_vel`, nobody nearby, tape as truth) and the driven checkpoint loop for route scale. Compare driven bags only with driven bags: motor vibration reaches the IMU | ATE, RPE, heading error ([EVO]), before and after SLAM; distance ratio vs tape | Compare with [M26]: 60–75 % gain before SLAM, −2.6 to +1.6 % after | 9.4 | Sherman |
| E3 | Localiser comparison (RQ3) | Record **driven** loops through the checkpoints (×3, Nav2 waypoints or teleop on the taped route), then replay `slam_toolbox` localisation and AMCL offline on the same bags, so neither is judged on a route the other steered. Wrong starts at 10/20/30/40 cm and 10/20/30/40°: place the robot, then drive a short move or spin to recover | Checkpoint error, pairwise ATE between loops, recovery yes/no per wrong start | Compare with [K26]: ~0.20–0.23 m pairwise ATE; our `slam_toolbox` baseline: recovers 30 cm / 20°, not 31° (2026-11-01, hand-pushed) | 9.3 | Sherman |
| E4 | People (RQ4) | Offline: 11-01 (person behind) vs 11-03 (nobody) push bags through E2's configs; **driven**: the E3 loop again with 1–2 people walking (clean split: nobody pushes, so empty means empty), and one person stepping in front | Error vs empty room per method, localisation failures, stop distance, contacts | Zero contacts | 9.7 | B |
| E5 | Lidar degradation (RQ1) | Replay every bag with scans cut to 1/2, 1/3, 1/4 of the beams, every 2nd/3rd scan, range capped at 4/3/2 m (range cut from PR 25), through E2's and E3's methods | Error vs degradation level per method; the knee where each method breaks | — | — | Sherman |
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

### Data status (checked 2026-11-09, `ssh robot@100.83.14.99 'ls -1t ~/bags'`)

| Bags on the Pi | Ground truth | Serves | Can start |
| --- | --- | --- | --- |
| `2026-10-31_push_195343`, `2026-10-31_turn_194945` | 1 m tape (0.962 m live), hand-turned 360° | E2, E5 short range | **Now, offline** |
| `2026-11-01_push_225752`, `_230535` (person behind) | wall-range change (`pushwall.py`) | E4 offline, E2 | **Now, offline** |
| `2026-11-03_*_push_actrue`, `_acfalse` (nobody in scan) | 1 m tape | E4 control, E2, E5 | **Now, offline** |
| `2026-10-31_map_200132`, `_200956` | none (map closure only) | E5 mapping, E3 map | Now, closure only |
| — | — | Driven straights/spins (E2), loops and wrong starts (E3), people loop and step-in (E4), E1 | **Needs one driven session** (motors in, rough gains) |
| — | — | E1, E4 driven step-in | **Needs motors** and PR 29 merged |

Push bags answer "does odometry hold over 1 m?", not "does localisation hold over a
route?". The driven session must record the checkpoint loop; those bags then serve E2, E3
and E5 at route scale. Arrival error in E1 is labelled "rough gains" (motor gains are not
tuned); the other experiments take truth from the tape and checkpoints, not from the command.

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
| Sherman | SLAM stack, replay matrix, E2, E3, E5, analysis with `evo` | Comparison block | RQ1, RQ2, RQ3 |
| Motor teammate (TBD) | Motors, calibration, Nav2, delivery script, E1 | System + mission block | E1 |
| A (TBD) | Background, product table, trends, roadmap | Opening and closing | Industry comparison |
| B (TBD) | E4, hazard table (uses `reports/MPC planners for dynamic humans.md`: stop wedge vs step-in) | People + safety block, "Our position" | RQ4 |
| C (TBD, if any) | Hazard table, report editing, references | Shared with B | Safety |

Each person owns at least one experiment or section and writes one "Our take" (peer
assessment is 15 %).

## 6. Schedule

**Reset 2026-11-09.** The 2026-11-03 schedule (kept below for the record) slipped: no
E1–E4 bags exist and PR 29 (Nav2 glue) and PR 30 (explore) are open. Replays run near real
time on the Pi, so the matrix is a compute job: start it first and let it run.

| Day | Robot / compute | Others |
| --- | --- | --- |
| Mon 9 Nov | Build the replay matrix (E2 configs, E5 degradation, AMCL offline config) and start it on the existing bags | Slide skeleton on the new storyline; product table |
| Tue 10 | **One driven session**, charged battery. First wheels raised, then one 1 m straight with the motor switch in reach. Then: driven 1 m straights and 360° spins (E2), checkpoint loop ×3 and wrong starts (E3), loop with people walking and one step-in (E4), E1 runs. If driving fails: hand-pushed with a stick, nobody behind the robot (fallback) | Background, hazard table drafts |
| Wed 11 | Replay the new bags; `evo`; figures; Our take per RQ; rehearsal 1 | Report sections 1–3; rehearsal 1 |
| Thu 12 | Present (morning) | — |
| End of Week 13 | Report finished with the full matrix; submit report, slides, peer assessment | — |

| Risk (2026-11-09) | Fallback |
| --- | --- |
| Driving fails on Tue (first floor run of the motors) | Fall back to hand-pushing with a stick, nobody behind the robot; E1 partial with the named blocker. If no live session at all: E2, E4-offline and E5 on existing bags only; E3 becomes "baseline wrong-start result + AMCL as future work" |
| Driven IMU data differs from hand-pushed (motor vibration) | Compare driven with driven only; list it in "differences from the paper" |
| Nav2 steers with `slam_toolbox`, biasing E3 | Replay both localisers offline on the same recorded loops, or drive the loop by teleop |
| Motors not in | E1 reported as partial with the named blocker; E4 driven step-in dropped, stop-wedge argument stays as analysis |
| Replays too slow on the Pi | Cut replays per cell to 3 and degradation levels to 2 per axis; or run them on the Mac in Docker |

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
| The [K26]/[M26] results transfer (or do not) to a lidar with a much lower echo rate | E3 spread close to (or far from) K26; E2 gain close to (or far from) M26 | — (either way is a result; name the reason) |
| "The customer is the obstacle": people degrade localisation and are the main safety hazard | E4 arrival error and failures clearly above E1. Early evidence: OI-8, rf2o read 0.242 of 0.862 m and 0.307 of 1.222 m with a person behind (measured, 2026-11-03) | E4 ≈ E1 on driven runs |
| Redundancy earns its cost | E2 shows the IMU lowers error after SLAM, not only before | E2 gain vanishes after SLAM, as in [M26]: then "SLAM hides odometry quality; the IMU matters only when the map can't correct", also a take |
| Delivery robots win by simplifying their world | Product table (markers, mapped rooms, slow speed) + E1 success | E1 fails for reasons a simpler world would not fix |
| Published 2D SLAM evaluation misses what matters for deployment (no ground truth in [K26]; covariances fitted on test data in [M26]; replay not live) | Our checkpoint error disagrees with what pairwise ATE alone suggests, or live differs from replay | Checkpoint error and pairwise ATE tell the same story |
| A cheap lidar sets a hard floor, and the localiser choice moves it (2026-11-09) | E5 shows a clear knee, at a different level for AMCL and `slam_toolbox` | No knee within the tested range, or both methods break at the same level |
| The IMU matters most when the scan is worst (2026-11-09) | E2 gain from the IMU larger with people (E4) or degraded scans (E5) than in the empty room | Gain the same in every condition |
| Integration, not algorithms, was the hard part | Failure log: OI-8, lidar start hang (OI-6), power | Most failures trace to the algorithms themselves |

## 8. Deliverables

The deliverables checklist moved to [`../TASKS.md`](../TASKS.md) §2 on 2026-11-09.

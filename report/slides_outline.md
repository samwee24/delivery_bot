# CA3 presentation: slide outline (tentative)

Status: **tentative**, plan "H" (people as the axis, live runs) of 2026-11-09 evening, replacing "G" of the same morning and "C+" of 2026-11-03. Slot: 15 min + 5 min Q&A, videos 2 min in total, each student presents their own contribution. Date and slot to confirm on NTULearn (estimated Thu 2026-11-12).

Companions, both being written in parallel (links may not resolve yet):
- Research plan: [`../docs/report_plan.md`](../docs/report_plan.md)
- Written report: [`CA3_report.md`](CA3_report.md)

Rules that bind this file (AGENTS.md): no value is shown as a result until measured on the robot; each number carries its command and provenance; no live motor commands on slides; nothing about products or papers that is not sourced (write "to check"). Presenters: **A**, **B**, **MT** (motor teammate), **S** (Sherman). Names to fill in.

Claims written as `[if E2 shows X] ... / otherwise ...` are placeholders until the data exists (E1 to E4 and RQ1 to RQ4 as defined in the plan §3–4; all results from the driven session Tue 2026-11-10).

**Storyline:** gap (hook) → field and products → what we built → the discovery (OI-8) → four findings, each *empty vs people → paper → gap → why → Our take* → our position → future work → verdict.

## 1. Slide table

| # | Time | Who | Claim headline | Visual | Speaker notes | Handoff |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0:00-0:45 | A | Published 2D SLAM results were measured in empty rooms. Our robot's customers walk around it. What breaks? | Clip V1 (20 s): robot leaves home mark, stops at a seat, returns (or hand-pushed loop if motors slip). Title text only | - State the main question, then the answer in one line at the end (slide 15)<br>- What we built: Raspberry Pi 4B, RPLidar A1M8, MPU6050, no wheel encoders<br>- The four questions, one line each: how much people hurt, which part breaks, which localiser holds, does it stay safe | "To judge a cheap robot we first need to know what the real ones do." |
| 2 | 0:45-1:15 | A | Indoor delivery is an AV problem in miniature: localise, plan, avoid people | Three-box diagram (localise / plan / avoid). Style of [`../docs/img/pipeline-simple.png`](../docs/img/pipeline-simple.png) | - Why a room is a fair scale model of a road problem<br>- Scope: one mapped room, 0.15 m/s, home mark | "Who is already doing this, and what do they simplify?" |
| 3 | 1:15-2:30 | A | Delivery robots that ship today succeed by simplifying their world | Product table: Pudu, Keenon, Aethon TUG, Starship, Amazon Scout (shut down 2022), ours. Sourced cells only, rest "to check" | - Two patterns: mapped indoor space, low speed, human-run exceptions<br>- Sidewalk delivery is harder (Scout as cautionary case; source to check)<br>- **Our take:** [if sources confirm] "indoor ships because the world is made simpler, not because the robots are smarter" | "We copied that simplification on a student budget. Here is the machine." |
| 4 | 2:30-3:30 | MT | Our robot is a scaled AV with one safety rule: motors only move through a watchdog | Hardware photo plus stack diagram; stream frame [`../results/2026-11-02_av_stream_frame.jpg`](../results/2026-11-02_av_stream_frame.jpg) if usable | - Hardware list, v_max 0.15 m/s (brief default)<br>- Safety is structural: `stop_dist_m`, `watchdog_s`, SIGINT zeroes PWM; kill switch is the motor switch<br>- Standard ROS 2 packages; we wrote only motor node, IMU node, URDF, delivery script (D7) | "Does it do the job?" |
| 5 | 3:30-4:30 | MT | [if E1 passes] It completed N of 5 deliveries within 15 cm. / [else] It completed N of 5; the blocker was X | Clip V2 (40 s): one delivery run. Table: success, arrival error, time | - Home to seat to home, config frozen, commit hash per run<br>- Report misses plainly<br>- **Our take:** what the count proves and what it does not | "It works, in an empty room. Then we found what happens when someone walks behind it." |
| 6 | 4:30-5:15 | S | A person walking behind the robot made its odometry read a quarter of the real distance | Chart: 0.962 m of 1.000 m with nobody near (2026-10-31) against 25-28 % of the push with a person behind (2026-11-01; closed 2026-11-03). Source [`../docs/test_log.md`](../docs/test_log.md) | - OI-8: four days of debugging; scan format cleared by live pushes with nobody in the scan<br>- rf2o assumes the scene is static; a person is a moving wall<br>- **Our take:** integration faults look like broken sensors | "So we tested every part of the stack twice: empty, and with people." |
| 7 | 5:15-5:45 | S | Every method ran live on the robot, once in an empty room and once with people walking | The test design: rows odometry configs and localisers, columns empty / people; photo of the taped people paths | - Live closed loop, 3 runs per cell, tape ground truth; [K26] used replay without ground truth<br>- People protocol: 1-2 walkers on two taped paths, same every run | "First: how much do people cost?" |
| 8 | 5:45-7:00 | S | [if RQ1 shows a gap] People cost every method X cm of accuracy and caused N losses. / [if not] With people walking, localisation held | Empty vs people bars per method; room figure with failure positions against the people's paths. Clip V3 (30 s): robot passes a walking person | - Extends [Y21] (5.90 vs 80.24 cm map error, filtered vs unfiltered) from mapping to localisation<br>- How failures start: drift, jump or lost<br>- **Our take:** "the customer is the obstacle" only if data supports it | "Which part breaks?" |
| 9 | 7:00-8:15 | S | [if E2 shows the IMU gain only with people] The IMU is invisible in an empty room and decisive with people. / [if not] The IMU behaves as [M26] found: big gain before SLAM, gone after | E2 bars: 4 configs × (empty, people), before and after SLAM, with spread | - Timed 1 m straights and 360° spins, each config loaded live; hand-turn context: gyro 360.2°, rf2o 352.9° (measured)<br>- [M26]: 60-75 % gain before SLAM, about zero after<br>- **Our take:** when redundancy earns its cost | "Which localiser should a cheap robot ship?" |
| 10 | 8:15-9:30 | S | [if E3 rankings flip] The localiser that wins in an empty room loses among people. / [else] X wins in both conditions | Left: checkpoint error per localiser × condition, [K26] value as a line. Right: wrong-start grid, recovered yes/no | - Each localiser steered its own Nav2 loop; baseline `slam_toolbox` recovers 30 cm / 20°, not 31° (2026-11-01)<br>- **Our take:** benchmark among people, not in empty rooms | "Localisation is one failure. Safety is the other." |
| 11 | 9:30-10:30 | B | [if E4 stops are tight] A person stepping in gets within X cm: the stop zone, not the localiser, is the weak part. / [else] It stopped with a wide margin every time | Step-in table: speed, stop distance, contact, against the 0.20 m zone. Clip V4 (20 s): person steps in, robot stops | - Zone sizing at walking pace from `reports/MPC planners for dynamic humans.md` (inference)<br>- **Our take:** what the stop zone should be | "Here is everything that can go wrong, and what we did about it." |
| 12 | 10:30-11:30 | B | Every hazard we listed has a mitigation, and we tested the ones we could | Hazard table (6-8 rows) | - SOTIF (ISO 21448), ISO 13482: check clauses before showing<br>- 2D lidar sees one plane only<br>- **Our take:** what is still unmitigated | "Putting that together, here is what we think." |
| 13 | 11:30-12:45 | B | Our position: three data-backed opinions | Three cards, each pointing to its evidence slide: (1) the customer is the obstacle, (2) empty-room benchmarks pick the wrong method for delivery, (3) cheap robots win by simplifying their world | - Each card cites a result slide; drop any the data does not support<br>- Contradicting a paper is allowed and valued | "And where does this go next?" |
| 14 | 12:45-13:30 | A | The roadmap is ordered by what the data exposed, not by what is fashionable | Costed list: people filtering in the scan [Y21], a larger or predictive stop zone, wheel encoders, camera fusion, de-skew [S23], lidar-degradation study | - Camera vs lidar was the best idea but needs a new build<br>- Trends: sourced items only<br>- Limits: one room, 3 runs per cell, people paths repeatable only roughly | "Last: the verdict." |
| 15 | 13:30-14:15 | A | Verdict: [one sentence answering the main question, from the data] | One sentence, large type; RQ1-RQ4 answers as ✓ / ✗ / partial | - Answer each question in a breath<br>- Close on the claim, not a thank-you | Thank you; questions. |
| 16 | Q&A | all | Backup: stack, config and the matrix in full | TF tree, frozen YAML with provenance, every cell's numbers | Used only if asked | n/a |
| 17 | Q&A | all | Backup: raw numbers | All runs with commands and commit hashes | Used only if asked | n/a |

Timing check: slides 1-15 end at 14:15, leaving 45 s of slack. Per presenter: A 0:00-2:30 plus 12:45-14:15 (4 min), MT 2:30-4:30 (2 min), S 4:30-9:30 (5 min), B 9:30-12:45 (3 min 15 s). B owns the people protocol and can co-present slide 8. Rebalance if a fifth member joins. Slides 16 and 17 do not count toward the 15 min.

## 2. Video budget (total <= 120 s)

| Clip | Slide | Seconds | Source (film on) |
| --- | --- | --- | --- |
| V1 hook: robot leaves home, serves a seat, returns | 1 | 20 | Tue 2026-11-10, cut from an E1 run (stick-pushed loop if driving fails) |
| V2 delivery run | 5 | 40 | Tue 2026-11-10 (E1 runs; screen-record Foxglove side by side if clean) |
| V3 robot passes walking people | 8 | 30 | Tue 2026-11-10 (E3 people loop) |
| V4 step-in stop | 11 | 20 | Tue 2026-11-10 (E4 step-in) |
| **Total** | | **110** | 10 s spare |

All clips are pre-recorded, muted or with voiceover by the presenter, stored as local files. Only record live motion under the existing safety rules; the clips are not shown from a live run.

## 3. "Our take" markers

Format: every result slide ends with one line in a fixed box at the bottom, accent colour, prefix "Our take:". Never more than 20 words. Wording below is a draft and depends on data.

| Slide | Our take (draft) |
| --- | --- |
| 3 | Indoor ships because the world is simplified. [pending sources] |
| 5 | [pending E1] What the count of runs proves, and what it does not. |
| 6 | Integration faults look like broken sensors. (OI-8, measured) |
| 8 | [pending RQ1] People are the obstacle, or they are not. |
| 9 | [pending E2] The IMU earns its cost when people are around, or it does not. |
| 10 | [pending E3] Benchmark localisers among people, not in empty rooms. |
| 11 | [pending E4] What the stop zone should be. |
| 12 | What the lidar cannot see is the main residual hazard. |

## 4. Q&A prep (draft answers use repo facts only)

| # | Question | Draft answer | Depends on pending result |
| --- | --- | --- | --- |
| 1 | Why no camera? | The brief and budget gave us a 2D lidar and a Pi 4, and a camera localisation stack would have been a new build with nine days left; the USB camera only streams to Foxglove (1280x720, 10 fps). Lidar against camera is the best extension and is in the roadmap. | No |
| 2 | Is five runs enough? | No, a few runs show whether a failure exists, not its rate; we report spread and ranges, not significance, and replay each bag ≥ 3 times because replay itself varies about 12 %. Config is frozen and the commit hash recorded per run so the study can be repeated. | Yes, run counts |
| 3 | How does this compare to Waymo? | We do not claim comparability: a room at 0.15 m/s with a map and a home mark, against open roads with 3D sensing, which we have not measured. What transfers is the structure: localise against a prior map, plan, and stop for people. | No (Waymo specifics: do not quote without a source) |
| 4 | Why use packages, not your own code? | Decision D7 (2026-10-22) supersedes D4: the brief permits packages, and we only wrote motor node, IMU node, URDF and the delivery script. Our own EKF and planner remain a documented fallback in `docs/system/07_ros_stack.md`. | No |
| 5 | What if your results contradicted the paper? | That is a finding, not a failure: we would report the gap and name the differences (26-29 % no-echo pings, 7.05 Hz, no encoders, Pi 4) we can support with data. We would not tune until the numbers match. | Yes, E2 and E3 |
| 9 | Were your people runs repeatable? | Roughly: the same 1-2 walkers on the same two taped paths at normal pace, starting with the robot; we report the spread over 3 runs per cell and treat "people" as one condition, not a controlled trajectory. | Yes, run spread |
| 10 | Each localiser steered its own run: isn't that unfair? | It is the real comparison: a product drives on its own localiser, so closed-loop error is what a customer sees. The bags also let us replay both localisers on the same run afterwards. | Yes, E3 |
| 6 | What would you do differently? | Keep people out of the scan during every odometry test from day one (OI-8 cost four days and turned out to be a person behind the robot), tape the checkpoints on day one, and fix the bag-recording protocol earlier, because replay was not repeatable. Pick the comparison questions before building, not after. | No |
| 7 | Is a 2D lidar safe around people? | Not on its own: it sees one plane, so low and overhanging objects are invisible, and its no-echo rate is 26-29 % on this unit. Our mitigations are 0.15 m/s, `stop_dist_m`, watchdog and a physical kill switch, and the hazard table lists what remains. | Yes, safety test |
| 8 | What does it cost? | Cost per part is in the hardware docs (`docs/system/01_hardware`) and should be summed from our own bill of materials, not from catalogue guesses. We do not compare against commercial robots until their prices are sourced. | Yes, BOM total to check |

## 5. Rehearsal checklist

- Timing: 3 full run-throughs (Tue 10, Wed 11, one extra before the slot). Targets: A about 4 min 15 s, MT about 2 min 15 s, S about 4 min 30 s, B about 3 min 30 s; total <= 14 min 30 s with a stopwatch per presenter.
- Handoffs: say the handoff sentence from the table verbatim; no silence over 3 s.
- Clicker with spare batteries; one person owns advancing slides, or each presenter owns their own slides (decide and keep).
- Backup video files on two USB sticks and a laptop, offline, played from local disk, not from a link; test the room projector audio.
- **No live demo.** Recommendation: pre-recorded only, because the robot needs a taped room, a charged battery (the Pi read `throttled=0x50005` on 2026-11-02) and a lidar that sometimes hangs at start (OI-6).
- Fallback if a clip fails: freeze frame on the slide and continue with the speaker note; the run table carries the numbers.
- Q&A drill: each presenter answers the questions in section 4 that touch their slides; the rest stays short.
- Pending numbers: every bracketed claim is replaced or deleted before rehearsal 2; no `[if ...]` text may reach the final slides.

## 6. Design notes

- One idea per slide; the headline is the claim, the visual is its evidence, notes carry the rest.
- Headlines are sentences that state a point. Max two lines at 32 pt or larger; body text at 20 pt or larger.
- Fixed "Our take" box on every result slide (accent colour, same position) so the audience sees where the insight is.
- Figures show spread and n, with the command and commit in a small line under the figure.
- Provenance tags on every number: *measured*, *fitted*, *brief default* or *target*.
- Cite on the slide footer by key, as listed in [`../docs/slam.md`](../docs/slam.md) References: [R25] 2D lidar SLAM review, [K26] repeatability benchmark, [M26] IMU ablation, [Y21] people in scans, [S23] de-skew. Slide 7 cites K26, slide 8 Y21, slide 9 M26, slide 10 K26, slide 14 Y21 and S23, slide 3 any product source.
- Colour-blind-safe palette; no sound-only information in clips (captions on every clip).

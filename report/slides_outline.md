# CA3 presentation: slide outline (tentative)

Status: **tentative**, agreed plan "C+" of 2026-11-03. Slot: 15 min + 5 min Q&A, videos 2 min in total, each student presents their own contribution. Date and slot to confirm on NTULearn (estimated Thu 2026-11-12).

Companions, both being written in parallel (links may not resolve yet):
- Research plan: [`../docs/report_plan.md`](../docs/report_plan.md)
- Written report: [`CA3_report.md`](CA3_report.md)

Rules that bind this file (AGENTS.md): no value is shown as a result until measured on the robot; each number carries its command and provenance; no live motor commands on slides; nothing about products or papers that is not sourced (write "to check"). Presenters: **A**, **B**, **MT** (motor teammate), **S** (Sherman). Names to fill in.

Claims written as `[if E2 shows X] ... / otherwise ...` are placeholders until the data exists (E1 to E4 as defined in the plan; E1 to E3 run Fri 2026-11-06, E4 Sat 2026-11-07).

## 1. Slide table

| # | Time | Who | Claim headline | Visual | Speaker notes | Handoff |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0:00-0:45 | A | Published 2D SLAM results were measured under conditions a cheap delivery robot never sees. Do they hold? | Clip V1 (20 s): robot leaves home mark, stops at a seat, returns. Title text only | - State the question, then the answer in one line at the end (slide 16)<br>- Say what we built: Raspberry Pi 4B, RPLidar A1M8, MPU6050, no wheel encoders<br>- Name the four RQs on one line each | "To judge a cheap robot we first need to know what the real ones do." |
| 2 | 0:45-1:30 | A | Indoor delivery is an AV problem in miniature: localise, plan, avoid people | Simple three-box diagram (localise / plan / avoid). Reuse style of [`../docs/img/pipeline-simple.png`](../docs/img/pipeline-simple.png) | - Why a room is a fair scale model of a road problem<br>- Scope: one mapped room, 0.15 m/s, home mark<br>- Link to course topic (localisation and safety in AVs) | "Who is already doing this, and what do they simplify?" |
| 3 | 1:30-3:00 | A | Delivery robots that ship today succeed by simplifying their world | Product table: Pudu, Keenon, Aethon TUG, Starship, Amazon Scout (shut down 2022), ours. Columns only from sourced facts, rest "to check" | - Pick two patterns: mapped indoor space, low speed, human-run exceptions<br>- Say why sidewalk delivery is harder (Scout is the cautionary case; source to check)<br>- **Our take:** [if sources confirm] "indoor ships because the world is made simpler, not because the robots are smarter" | "We copied that simplification on a student budget. Here is the machine." |
| 4 | 3:00-4:15 | MT | Our robot is a scaled AV with one safety rule: motors only move through a watchdog | Hardware photo plus TF/stack diagram ([`../docs/img/pipeline-simple.png`](../docs/img/pipeline-simple.png)); stream frame [`../results/2026-11-02_av_stream_frame.jpg`](../results/2026-11-02_av_stream_frame.jpg) if usable | - Hardware list and v_max 0.15 m/s (brief default)<br>- Safety is structural: `stop_dist_m`, `watchdog_s`, SIGINT zeroes PWM; kill switch is the motor switch<br>- Standard ROS 2 packages; we wrote only motor node, IMU node, URDF, delivery script (D7) | "With the safety layer in place, did it complete the job?" |
| 5 | 4:15-5:15 | MT | [if E1 passes] The robot completed N of 5 delivery runs within 15 cm. / [else] It completed N of 5; the blocker was X | Clip V2 (40 s): one delivery run, sped up if needed. Table of 5 runs: success, arrival error, time | - Protocol: home to seat to home, 5 runs, config frozen, commit hash per run<br>- Report misses plainly<br>- **Our take:** one line on what the number does and does not prove | "That is the mission. Now I'll test whether the localisation behind it matches the papers." |
| 6 | 5:15-6:00 | S | What the papers measured, and what they could not: replay, better sensors, no ground truth, no people | Two-column card: [K26] repeatability; [M26] IMU contribution. Footer cites both | - K26: its "AMCL off" condition is our stack (rf2o + IMU to EKF to slam_toolbox, no encoders, Jazzy); repeatability by replay, no ground truth<br>- M26: wheel odometry ± IMU on a public dataset; EKF gain large before SLAM, about zero after. Ours is an analogue (no encoders)<br>- Our differences: A1M8 with 26-29 % no-echo pings at 7.05 Hz (measured, test_log), Pi 4, hand-built chassis<br>- Same frozen config for every run | "First promise: the stack repeats." |
| 7 | 6:00-7:30 | S | [if E3 shows pairwise ATE near K26's] The stack repeats on a cheap lidar. / [if it does not] Repeatability breaks on a cheap lidar, and here is why | Pairwise ATE across 5 runs; map overlay or IoU. Existing map as context: [`../results/maps/2026-10-31_room2.png`](../results/maps/2026-10-31_room2.png) | - Metric: pairwise ATE, map IoU (as K26)<br>- Command and commit hash on the figure<br>- Say what differs from K26 and by how much<br>- **Our take:** name the cause we can support with data | "Second promise: does the gyro earn its place?" |
| 8 | 7:30-9:00 | S | [if E2 shows IMU lowers ATE] The MPU6050 gyro bought a measurable gain. / [if no gain] On our robot the gyro bought nothing measurable, and that contradicts M26 | E1 bags replayed with and without IMU: ATE, RPE, heading error (evo). Bar chart with spread | - Same bags, EKF with vs without IMU, plus one live run each<br>- Show spread, not a single bar (n = 5)<br>- Price figure only if sourced, else drop it<br>- **Our take:** cost of redundancy against what it bought | "One lead found a surprise on the way: rf2o itself." |
| 9 | 9:00-9:45 | S | Integration, not algorithms, was the hard part: rf2o read 24 % of a hand push on one day and 96 % on another | Chart of the two pushes: 0.962 m of 1.000 m (2026-10-31) against 24 % of 1.222 m (2026-11-01) from [`../docs/test_log.md`](../docs/test_log.md). Replay not repeatable: 0.679 / 0.592 / 0.531 m | - OI-8 stays open unless closed by 2026-11-04; say so<br>- Leads: scan format, a person behind the robot; replay controls do not match live yet<br>- Two TF publishers would spin the map: a known risk we designed out (`publish_tf: false`), not a fault we hit<br>- **Our take:** [if OI-8 closed] state cause; [if open] "a static-scene assumption we could not clear" | "Which brings us to the thing rf2o dislikes: people." |
| 10 | 9:45-11:15 | B | [if E4 shows larger errors] People degrade delivery by X cm and the robot copes only because it is slow. / [if no effect] With 1-2 people walking, delivery did not degrade measurably | E4 vs E1 arrival error, localisation failures, count of runs. Clip V3 (30 s): robot passes a walking person | - Protocol: 5 runs with 1-2 people walking; extends [Y21] (people tracker for SLAM)<br>- n = 5, so state effect size not significance<br>- **Our take:** "the customer is the obstacle" only if data supports it | "Localisation is one failure. Safety is the other." |
| 11 | 11:15-12:15 | B | Every hazard we listed has a mitigation, and we tested the ones we could | Hazard table (6-8 rows): hazard, mitigation, test, pass/fail. Clip V4 (20 s): person steps in front, robot stops, stop distance shown | - Frame by SOTIF (ISO 21448) and ISO 13482; check clause references before showing<br>- 2D lidar sees one plane only: say which hazards it cannot see<br>- **Our take:** what the table says is still unmitigated | "Putting that together, here is what we think." |
| 12 | 12:15-13:15 | B | Our position: three data-backed opinions | Three cards, each with its evidence slide number: (1) integration over algorithms, (2) redundancy earns its cost only if E2 says so, (3) the customer is the obstacle | - Each opinion cites a result slide, no new claims<br>- Drop any card whose data does not support it<br>- Contradiction with the papers is allowed and valued | "And where does this go next?" |
| 13 | 13:15-14:00 | A | The roadmap is ordered by what the data exposed, not by what is fashionable | Costed list: wheel encoders, camera fusion (lidar vs camera comparison), people filtering [Y21], simulation regression, de-skew [S23]. Cost cells "to estimate" | - Camera fusion was the best idea but needs a new build, so it is future work<br>- Trends: placeholder, only sourced items<br>- Limits: one room, n = 5, one robot | "Last: the verdict." |
| 14 | 14:00-14:30 | A | Verdict: [if results hold] a low-cost sensor stack is enough indoors, if the world is simplified. / [if not] it is not, and here is the one thing that failed | One sentence, large type, plus RQ1 to RQ4 answers as ticks (✓/✗/partial) | - Answer each RQ in a breath<br>- Do not use a cost figure unless sourced from our BOM<br>- Close on the claim, not a thank-you | Thank you; questions. |
| 15 | Q&A | all | Backup: stack and config | TF tree, frozen YAML table with provenance column | Used only if asked | n/a |
| 16 | Q&A | all | Backup: raw numbers | Table of all runs with commands and commit hashes | Used only if asked | n/a |

Timing check: slides 1-14 end at 14:30, leaving 30 s of slack. Per presenter: A 0:00-3:00 plus 13:15-14:30 (about 4 min 15 s), MT 3:00-5:15 (2 min 15 s), S 5:15-9:45 (4 min 30 s), B 9:45-13:15 (3 min 30 s). Rebalance if a fifth member joins. Slides 15 and 16 do not count toward the 15 min.

## 2. Video budget (total <= 120 s)

| Clip | Slide | Seconds | Source (film on) |
| --- | --- | --- | --- |
| V1 hook: robot leaves home, serves a seat, returns | 1 | 20 | Fri 2026-11-06, cut from an E1 run |
| V2 delivery run | 5 | 40 | Fri 2026-11-06 (E1 runs; screen-record Foxglove side by side if clean) |
| V3 robot passes walking people | 10 | 30 | Sat 2026-11-07 (E4 runs) |
| V4 step-in stop | 11 | 20 | Sat 2026-11-07 (safety-stop test) |
| **Total** | | **110** | 10 s spare |

All clips are pre-recorded, muted or with voiceover by the presenter, stored as local files. Only record live motion under the existing safety rules; the clips are not shown from a live run.

## 3. "Our take" markers

Format: every result slide ends with one line in a fixed box at the bottom, accent colour, prefix "Our take:". Never more than 20 words. Wording below is a draft and depends on data.

| Slide | Our take (draft) |
| --- | --- |
| 3 | Indoor ships because the world is simplified. [pending sources] |
| 5 | [pending E1] What the count of runs proves, and what it does not. |
| 7 | [pending E3] The cause of any gap to K26, tied to the A1M8 echo rate only if the data supports it. |
| 8 | [pending E2] What the IMU bought for what it costs. |
| 9 | [pending OI-8] Integration faults look like broken sensors. |
| 10 | [pending E4] People are the obstacle, or they are not. |
| 11 | What the lidar cannot see is the main residual hazard. |

## 4. Q&A prep (draft answers use repo facts only)

| # | Question | Draft answer | Depends on pending result |
| --- | --- | --- | --- |
| 1 | Why no camera? | The brief and budget gave us a 2D lidar and a Pi 4, and a camera localisation stack would have been a new build with nine days left; the USB camera only streams to Foxglove (1280x720, 10 fps). Lidar against camera is the best extension and is in the roadmap. | No |
| 2 | Is five runs enough? | No, five runs show whether a failure exists, not its rate; we report spread and the ranges, not significance. The plan keeps config frozen and records commit hash per run so the study can be repeated. | Yes, E1 to E4 counts |
| 3 | How does this compare to Waymo? | We do not claim comparability: a room at 0.15 m/s with a map and a home mark, against open roads with 3D sensing, which we have not measured. What transfers is the structure: localise against a prior map, plan, and stop for people. | No (Waymo specifics: do not quote without a source) |
| 4 | Why use packages, not your own code? | Decision D7 (2026-10-22) supersedes D4: the brief permits packages, and we only wrote motor node, IMU node, URDF and the delivery script. Our own EKF and planner remain a documented fallback in `docs/system/07_ros_stack.md`. | No |
| 5 | What if your results contradicted the paper? | That is a finding, not a failure: we would report the gap and name the differences (26-29 % no-echo pings, 7.05 Hz, no encoders, Pi 4) we can support with data. We would not tune until the numbers match. | Yes, E2 and E3 |
| 6 | What would you do differently? | Close OI-8 (rf2o reading 24 % of a push on 2026-11-01 against 96 % on 2026-10-31) before anything else, and tape the checkpoints on day one. We would also fix a bag-recording protocol earlier, because replay was not repeatable. | Partly, OI-8 status |
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
- Cite on the slide footer by key, as listed in [`../docs/slam.md`](../docs/slam.md) References: [R25] 2D lidar SLAM review, [K26] repeatability benchmark, [M26] IMU ablation, [Y21] people in scans, [S23] de-skew. Slide 6 cites K26 and M26, slide 7 K26, slide 8 M26, slide 10 Y21, slide 13 Y21 and S23, slide 3 any product source.
- Colour-blind-safe palette; no sound-only information in clips (captions on every clip).

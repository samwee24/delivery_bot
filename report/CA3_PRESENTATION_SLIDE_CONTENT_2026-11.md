# CA3 presentation: slide-by-slide content, 2026-11-11

The content specification for the slide-building session. It fixes the narrative, the order, the
on-slide text, the visuals, the speaker scripts, the timing and who presents each slide. The next
session should design and lay out these slides, not re-plan them.

**Source of truth:** [`slides_outline.md`](slides_outline.md) v5 (cited below as **OL**), with its
section 7 challenge table (**OL§7**) and section 8 figure sources (**OL§8**). Numbers come from
`docs/test_log.md` (**TL**, by date and row name), `notes/notes.md` (**NB**, by date),
[`slam_challenges.md`](slam_challenges.md) (**SC**, by section) and
[`literature_notes.md`](literature_notes.md) (**LN**). Nothing here goes beyond those sources. Where
a fact is missing, a placeholder says so.

**Placeholder notation.** Placeholders never appear on a slide. They sit in each slide's
"Placeholders" line, outside the on-slide content.

| Tag | Meaning |
|---|---|
| `[TEAM INPUT REQUIRED: ...]` | A fact only the team can supply |
| `[VERIFY: ...]` | A claim to confirm before the talk |
| `[ARTEFACT NEEDED: ... (owner)]` | A picture, video or record that must be made or found. The named owner supplies it |
| `[SOURCE GAP: ...]` | No evidence exists for this yet |

All figure paths are relative to `report/`.

---

## A. Presentation overview

| Item | Content |
|---|---|
| Title | A Low-Cost Autonomous SLAM Robot: What It Took to Map a Room and Navigate It |
| Aim | How can we apply what we learned in the course to build a low-cost autonomous driving robot? |
| One-sentence summary | We built a robot from a 2D lidar, a cheap IMU, a Raspberry Pi 4 and four DC motors with no wheel encoders, mapped a room with SLAM, localised on that map, and reached a navigation goal on its own while driving around a box. |
| Central message | The SLAM and navigation software came as ready-made packages and worked. Most of the work was making cheap hardware and a slow computer meet the assumptions those packages make. |
| Audience | Lecturers and classmates of an autonomous-vehicles course. They know SLAM, the EKF, lidar, path planning and pure pursuit, so none of these is defined. They do not know our robot, ROS 2 or the specific packages |
| Core time | 10 to 15 minutes, then 5 minutes of questions (not counted here) |
| Slides | 21 core slides (title, 7 background, 1 pipeline, 10 implementation and results, close), plus 6 backup slides |
| Brief | Overview, state of the art, product or paper comparison, brief technical information, future trends, and most importantly our own insights. Videos and animations at most 2 minutes in total. Each student presents their own contribution |

**Three key takeaways**

1. The algorithms were not the hard part. Of 14 challenges we logged, 13 came from hardware,
   computer load, interfaces between programs, or process. One came from an algorithm's assumption:
   lidar odometry assumes the world is still, and a person walking behind the robot broke that.
2. A cheap robot has to be measured live. Published results use better sensors and replay
   recordings on desktop computers. Three replays of one recording on our Pi gave 0.68, 0.59 and
   0.53 m for a push that measured 0.962 m live.
3. When there is no ground truth, build one. A lap that starts and ends on one taped mark turns the
   gap between start and end into an error measure: 0.20 m with SLAM against 0.36 m on odometry
   alone, live.

**Narrative and section timings**

| Section | Slides | Presenter | Time |
|---|---|---|---|
| Title | T | Yujie | 0:30 |
| 1. Background: our design against a road AV, the choices and their assumptions, papers and products | 1.1 to 1.7 | Yujie | 4:35 |
| 2. The planned pipeline | 2.1 | Sherman | 0:35 |
| 3a. Sensing, mapping, localisation, the surprise, navigation (pipeline blocks 1 to 5) | 3.1 to 3.5 | Sherman | 4:20 |
| 3b. Hardware, power and motors (block 6), the result, analysis, lessons | 3.6 to 3.10 | Chloe | 3:40 |
| Close | Close | Chloe | 0:15 |
| Handover pauses (2 changes of presenter, about 5 s each) | | | 0:10 |
| **Total** | | | **14:05** |

**Why this order works for the assessment.** The audience knows the theory, so the background does
not teach it. It places our robot against a road AV, states each design choice with its parameters
and the assumption it makes, and compares with papers and products. Every challenge in Section 3
then points back to the assumption that broke ("← 1.2"). Section
3 then follows the pipeline left to right, which is also the order the work happened: the room was
mapped by pushing the robot by hand on 31 Oct, and the motors went live on 9 Nov. So the story
reads "first it learned to see, then it learned to move". Ordering by pipeline also gives two
presenter handovers instead of seven, and each person presents a contiguous block of their own
work: Sherman the sensing and SLAM side, Chloe the motors and the drive.

**Rules for the slide-building session**

1. **Pitch at an AV-course audience.** Do not define SLAM, EKF, costmaps or pure pursuit. Each
   background slide states our choice, its parameters and its assumption. One design choice per
   background slide, one pipeline block per implementation slide.
2. **A recurring pipeline strip.** On slides 3.1 to 3.7 the pipeline sits small in a corner with
   the current block highlighted: `figures/2026-11-11_pipeline_block1.png` to `block6.png`. Mapping
   of slides to blocks: 3.1 blocks 1 and 2, 3.2 block 3, 3.3 blocks 3 and 4, 3.4 block 2, 3.5 block
   5, 3.6 and 3.7 block 6.
3. **Back-links.** Every challenge that a background slide explains carries a small grey tag such as
   "← 1.2" next to it.
4. **"Our take" box.** A fixed box at the bottom of slides 1.6, 1.7, 3.4, 3.5, 3.8 and 3.9, one line of
   at most 20 words, always in the same place and colour.
5. **Every number keeps its condition and provenance.** "0.20 m" always carries "live, start-end gap
   on the taped mark". Replay numbers always say "replay". Tags: *measured*, *fitted*, *by eye*.
6. **No internal codes on slides.** No challenge IDs (C1, S7), no open-issue numbers (OI-8), no
   decision numbers (D5), no PR numbers. The audience has never seen our tracker.
7. **Figures carry no titles.** The slide headline is the title. Each figure's source goes in one
   small footer line (from OL§8).
8. **Colour.** The figures use one palette: blue = what worked or what we measured, orange = a
   problem or our own code, grey = background. Keep slide accents to the same three.
9. **Writing style.** Plain language, no em dashes, no semicolons, no emojis, no hype.
10. **Videos.** Local files, muted, captioned in the slide software (the clips have no burned-in
    text). Total 108 s, under the 120 s limit.
11. **Spoken style in the scripts.** Short sentences, one idea each. Signpost lists ("Three
    assumptions. One... Two..."). Round numbers aloud when the slide shows the exact value
    ("about a quarter" for 26 to 29 %). Each transition line leads straight into the next slide's
    first sentence. Scripts point at the figure when it helps ("On the left...", "the orange
    rays"). "rf2o" is written R-F-2-O in the scripts to show how to say it. Scripts are
    a guide for rehearsal, not text to read off the slide.

---

## B. Slide-by-slide content

---

## Slide T: A Low-Cost Autonomous SLAM Robot: What It Took to Map a Room and Navigate It

**Purpose.** Open the talk, name the team, show the robot moving in the first 30 seconds.

**Key takeaway.** An AV stack on a hobby budget: it plans its own path around a box.

**On-slide content**

- Title: *A Low-Cost Autonomous SLAM Robot: What It Took to Map a Room and Navigate It*
- Aim: *How can we apply what we learned in the course to build a low-cost autonomous driving robot?*
- Team: Yujie, Chloe, Sherman
- Parts line: *Raspberry Pi 4 · RPLidar A1M8 (2D) · MPU6050 IMU · 4 DC motors · no wheel encoders*
- Course and date: MA4890 CA3, Thursday 12 November 2026

**Recommended visualisation.** Clip V1 (`figures/2026-11-10_V1_box_2x.mp4`, the first 40 s of the
box run at 2x, 20 s) plays on the left two thirds. The labelled top-view photo
(`figures/2026-11-11_robot_labelled.png`) sits small on the right, so the audience sees the parts
before slide 3.6. Caption on the clip: "2x speed".

**Proposed speaker script.**
"Good morning, everyone. We're Yujie, Chloe and Sherman, and our project is building an autonomous driving robot from scratch, on a student budget."

**Estimated duration.** 0:30

**Evidence and source notes.** OL title and aim. Parts from `AGENTS.md` and the photos of 2026-11-11.
Four motors in two pairs per the team (2026-11-11). Clip from `IMG_8217.MOV`.

**Placeholders.** `[VERIFY: the box video is the run that logged "Goal succeeded". The video is 45 s, the successful goal took 92.8 s, and two cancelled goals took 42.3 s and 54.9 s (Chloe)]`
`[TEAM INPUT REQUIRED: full names and the lecturer's name, if the title slide should carry them]`

**Presenter.** Yujie

**Transition.** "We started with one question."

---

## Slide 1.1: Same loop as a road AV, scaled down to one room and one sensor plane

**Purpose.** Place the robot against the AV stack the class knows, and show what we cut. No
definitions of SLAM.

**Key takeaway.** Perception, localisation, planning and control are all there. The sensing and the
compute are cut down by orders of magnitude, and that is where the trouble came from.

**On-slide content**

- Title: *Same loop as a road AV, scaled down to one room*
- Two columns:

| | Road AV (Waymo, 6th generation) | Our robot |
|---|---|---|
| Sensing | 13 cameras, 4 lidar, 6 radar | one 2D lidar, one IMU |
| Odometry | wheel odometry and IMU, among others | lidar odometry and gyro, no encoders |
| Map | built in advance, then localised on | one SLAM lap, then localised on |
| Planning and control | in-house stack | Nav2: Dijkstra planner, pure pursuit |
| Compute | in-car computer | Raspberry Pi 4 |

- Caption on the GIF: *odometry only drifts up to 0.46 m over one lap, SLAM pulls it back*

**Recommended visualisation.** Table on the left. Right: `figures/2026-11-11_drift_vs_slam.gif`
(14 s), or the still `2026-11-11_drift_vs_slam.png`. Optional small inset:
`figures/2026-11-11_pose_graph.png` (our lap as a pose graph, 63 nodes, places seen twice in orange).

**Proposed speaker script.**
"This Waymo robotaxi carries twenty-nine cameras, plus lidar and radar all around. Ours has one 2D lidar, one IMU and a Raspberry Pi. Yet both run the same loop from the course: build a map, locate yourself on it, plan a path, and follow it.

The animation shows why that matters even at our scale. In orange is the robot's own motion estimate over one lap, drifting up to forty-six centimetres. In blue is SLAM, which keeps correcting it. So the method works. The question is what it takes on hardware this cheap."

**Estimated duration.** 0:40

**Evidence and source notes.** Waymo sensor counts from Waymo's blog, 2024-08 (LN Part 3). GIF from
bag `2026-10-31_map_200956`, odometry moved into the map frame at the first pose (OL§8). Pose graph:
a node every 0.5 m, 63 nodes, geometric revisits within 0.4 m, an illustration, not slam_toolbox's
loop-closure list (OL§8).

**Placeholders.** `[VERIFY: the "Odometry" and "Map" cells of the Waymo column are general course knowledge, not from LN. Keep them generic or drop the two rows]`

**Presenter.** Yujie

**Transition.** "Most of that effort went into sensing."

---

## Slide 1.2: A 7 Hz single-plane lidar replaces the encoders, and its odometry assumes a static world

**Purpose.** The perception and odometry choices, with the three assumptions Section 3 comes back to.

**Key takeaway.** Lidar odometry stands in for wheel encoders. It assumes the scene is static, the
scan is instantaneous and every surface echoes.

**On-slide content**

- Title: *A 7 Hz single-plane lidar replaces the encoders*
- **RPLidar A1M8:** one plane at 12 cm, 7 Hz, about 0.5° between beams
- **rf2o [J16]:** range-flow odometry. Fits one rigid motion to the whole scan pair
- **SLAM Toolbox [MJ21]:** graph-based: scan matching, pose graph, loop closure, then localisation on the saved graph. Graph-based is the usual choice for 2D lidar [R25]
- Three assumptions to watch:
  - *static scene:* anything moving with the robot reads as "not moving"
  - *instant scan:* at 7 Hz, the robot turns about 8° within one sweep at 1 rad/s [S23]
  - *every surface echoes:* glass and dark surfaces return nothing, table tops sit above the plane

**Recommended visualisation.** `figures/2026-11-11_lidar_plane.png` (side view of the one plane:
legs and walls seen, table top missed, glass no echo). Footer: "sketch, not data".

**Proposed speaker script.**
"Our lidar scans one flat plane, twelve centimetres off the floor, about seven times a second. With no encoders, it also has to be our odometry. For that we use rf2o, which compares two consecutive scans to work out how the robot moved. SLAM Toolbox then builds the map, and later localises the robot on it.

Three assumptions hide in here, and each comes back later. rf2o assumes nothing in the scene moves. It treats each scan as a snapshot, though at seven hertz the robot can turn eight degrees mid-sweep. And it assumes every surface reflects. As the sketch shows, glass often doesn't, and a table top sits above the plane."

**Estimated duration.** 0:50

**Evidence and source notes.** Scan rate 7.05 Hz (TL 2026-10-21). 720 beams after `angle_compensate`
(0.5°, TL 2026-11-01 scan format row). Plane height 0.12 m from the URDF (NB 2026-10-31). Methods LN
brief entries [J16], [MJ21], [R25]. 8° per scan is our arithmetic (LN, S23 entry).

**Placeholders.** None.

**Presenter.** Yujie

**Transition.** "Lidar odometry is weakest on fast turns, which is where the IMU helps."

---

## Slide 1.3: The EKF fuses lidar odometry with the gyro, and it alone publishes the odometry frame

**Purpose.** Our fusion configuration, not the EKF itself. The measured noise values are on 3.1.

**Key takeaway.** Velocities in, one smooth odometry frame out, weighted by fitted noise.

**On-slide content**

- Title: *The EKF fuses lidar odometry with the gyro*
- robot_localization EKF, 2D mode, 20 Hz
- Inputs: *rf2o forward speed and yaw rate, gyro yaw rate (100 Hz)*
- Weights: *noise values fitted from hand tests (on 3.1)*
- One rule: *the EKF is the only publisher of odom → base. Two publishers of one transform make the map spin*

**Recommended visualisation.** `figures/2026-11-11_fusion_flow.png` (lidar → rf2o → EKF ← gyro, our
IMU node in orange).

**Proposed speaker script.**
"We combine the two with an Extended Kalman Filter. As the diagram shows, it takes speed and turning rate from rf2o, turning rate from the gyro, and blends them into one smooth estimate.

The cards show three choices. We fuse speeds, not positions, so one bad reading can't throw it off. Each input is weighted by its noise, which we measured ourselves. And only the filter may publish the robot's position. When two programs did, the map visibly spun."

**Estimated duration.** 0:35

**Evidence and source notes.** `delivery_bot_bringup/config/ekf.yaml` (odom0 vx and vyaw, imu0 vyaw,
two_d_mode true, 20 Hz). TF rule in `AGENTS.md`. IMU 100 Hz (TL 2026-10-30).

**Placeholders.** None.

**Presenter.** Yujie

**Transition.** "That's how the robot knows where it is. Moving it was just as tricky."

---

## Slide 1.4: Skid steer driven as a differential drive, open loop, with a stall floor

**Purpose.** The actuation model and its two limits, so 3.5 and 3.7 need no explanation.

**Key takeaway.** No encoders means no speed feedback, and below a certain duty nothing moves.

**On-slide content**

- Title: *Skid steer, driven open loop, with a stall floor*
- *4 DC motors, each side's pair on one L298N channel, so it is driven as a differential drive: left = v − ω·b/2, right = v + ω·b/2, b = 0.156 m taped*
- *Skid steer scrapes sideways on turns, so the effective b is larger than the taped one (not fitted)*
- *No encoders: duty-to-speed must be calibrated, and nothing corrects it at run time*
- *PWM generated in software on the Pi*
- **Stall floor:** *below a certain duty, static friction wins*

**Recommended visualisation.** `figures/2026-11-11_motor_drive.png` (H-bridge with one diagonal lit,
four-wheel base with the left pair in blue and the right pair in orange).

**Proposed speaker script.**
"On the left is the motor driver. The speed comes from the duty cycle, the share of time the power is on. On the right, each side's motors share one channel, so the robot steers like a tank.

The cards are the three catches. With no encoders, it's open loop: we send a duty cycle and trust the wheels follow. The wheels skid on turns, so real turning differs from the model. And there's a stall floor: below a certain duty, the wheels don't turn at all."

**Estimated duration.** 0:35

**Evidence and source notes.** Four motors in two pairs (team, 2026-11-11). Track 0.156 m taped,
effective not fitted (NB 2026-10-31). L298N and software PWM (`AGENTS.md` Motors row).

**Placeholders.** None.

**Presenter.** Yujie

**Transition.** "On top of all this sits the navigation software."

---

## Slide 1.5: Nav2 with a Dijkstra planner and Regulated Pure Pursuit, configured for a 0.15 m/s robot

**Purpose.** Our navigation configuration, with the numbers that matter later.

**Key takeaway.** Standard planner and controller. The parameters that matter are the margins, the
speeds and the safety layers.

**On-slide content**

- Title: *Nav2: Dijkstra planner, Regulated Pure Pursuit*
- **Costmap:** saved map plus live lidar, inflation 0.25 m, robot radius 0.12 m
- **Planner:** NavFn (Dijkstra)
- **Controller:** Regulated Pure Pursuit, lookahead 0.2 to 0.4 m, speed capped at 0.15 m/s
- **Safety, three layers:** Nav2 collision monitor (stop zone 0.20 m), motor node lidar stop (0.20 m, ±35°), 0.5 s command watchdog. Motor switch as the kill switch
- **Checks:** goal within 0.10 m, progress 0.5 m in 10 s

**Recommended visualisation.** `figures/2026-11-11_nav2_concept.png` (our map, 0.25 m inflation, a
planned path, the lookahead point). Small inset: `figures/2026-11-11_safety_zones.png`. Footer:
"path computed offline for illustration".

**Proposed speaker script.**
"For navigation we use Nav2, the standard ROS 2 package. It plans with Dijkstra's algorithm on a map where every obstacle is grown by twenty-five centimetres, then follows the path with pure pursuit, steering at a point just ahead. In our example, the orange band is that margin and the orange dot is the point being chased.

We capped speed at fifteen centimetres a second, with three safety layers: Nav2's collision monitor, a lidar stop in our motor program, and a physical switch. Remember that Nav2 slows down near obstacles. That matters later."

**Estimated duration.** 0:40

**Evidence and source notes.** `delivery_bot_bringup/config/nav2_params.yaml` (NavfnPlanner,
RegulatedPurePursuitController, lookahead 0.2 to 0.4, desired_linear_vel 0.15, inflation_radius
0.25, xy_goal_tolerance 0.10, SimpleProgressChecker 0.5 m in 10 s). Motor node limits (`AGENTS.md`).
The path in the figure is an offline Dijkstra in `tools/analysis/slide_figs.py`.

**Placeholders.** None.

**Presenter.** Yujie

**Transition.** "How does our setup compare with published work?"

---

## Slide 1.6: Published work used far better sensors and desktop replays, so ours had to be measured live

**Purpose.** State of the art: four papers against our robot.

**Key takeaway.** Our robot is far cheaper than any published setup, and the closest paper's
method, replaying recordings, did not work on our computer.

**On-slide content**

- Title: *Published work used far better sensors. Ours had to be measured live*
- Table, five rows:

| | Lidar | Encoders | Results computed on | They found | We saw |
|---|---|---|---|---|---|
| K26 | Ouster 3D, cut to 2D | no | desktop replay | runs repeat within 0.20 to 0.23 m | 3 replays: 0.68 / 0.59 / 0.53 m |
| M26 | Hokuyo UTM-30LX | yes | PR2 dataset | IMU cuts odometry error 60 to 75 % before SLAM, about 0 after | gyro 360.2° vs lidar 352.9° on one turn |
| Y21 | Hokuyo, 40 Hz | | | people raise map error 5.9 → 80 cm | person behind: odometry 24 % |
| S23 | low-rate 2D lidars | | | motion skews each scan | 7 Hz: about 8° per scan at 1 rad/s |
| Ours | A1M8, 7 Hz | no | Raspberry Pi 4, live | | |

- Our take: *Published numbers come from good sensors and desktop replays. A cheap robot has to be measured live.*

**Recommended visualisation.** Build the table natively in the slide software (no image), from the rows above. Shade the "Ours" row, keep each cell to a few words.

**Proposed speaker script.**
"The closest paper, by Kudriashov and colleagues, uses exactly our software. But they recorded their sensor data and replayed it later on a powerful desktop. When we replayed one of our recordings on the Pi three times, we got three different distances, all short of what the robot really moved, because the Pi can't keep up. So everything we show you today was measured live on the robot.

Merrick and Nandikolla found an IMU cuts odometry error by up to three quarters, which matches our gyro beating the lidar on turns. Ye and colleagues showed people walking through scans corrupt maps, and we hit that too. And Salem and colleagues describe the mid-sweep smearing from earlier."

**Estimated duration.** 0:40

**Evidence and source notes.** LN Part 1 for K26, M26, Y21, LN brief entry for S23. Replays TL
2026-11-03 "replay repeatability". Turn TL 2026-10-31 "3.2 spin only". Blank cells are not stated in
what we read.

**Placeholders.** `[VERIFY: M26's computer and lidar rate, and Y21's encoder use, if anyone asks. LN gives M26 "Hokuyo UTM-30LX, MicroStrain IMU, wheel encoders, PR2 dataset" only]`

**Presenter.** Yujie

**Transition.** "And against robots you can buy?"

---

## Slide 1.7: Indoor delivery robots on sale fuse lidar with cameras and run up to 8 times faster

**Purpose.** The product comparison the brief asks for, and a pointer to where the field is going.

**Key takeaway.** Every product adds cameras to its lidar. Our one-plane lidar is the main gap, and
it is the one Section 3 keeps running into.

**On-slide content**

- Title: *Robots on sale fuse lidar with cameras and run up to 8 times faster*

| | Sensors | Localisation | Speed | Price |
|---|---|---|---|---|
| Pudu BellaBot | lidar + 3 RGBD cameras | lidar or visual SLAM, optional markers | 0.5 to 1.2 m/s | not published |
| Keenon T10 | 2 lidars (2D) + 4 stereo cameras | own system, not described | not published | about $9k to $20k, reseller-dependent |
| Bear Servi | lidar + cameras | mapping and a home dock | 0.1 to 1.2 m/s | $9,990 |
| Ours | one 2D lidar + IMU | saved 2D map, taped home mark | capped 0.15 m/s | |

- Our take: *Commercial robots see above and below the lidar plane. Ours cannot, and that limits where it can go.*

**Recommended visualisation.** Native slide table from the rows above, same style as 1.6. Shade the "Ours" row. Optional: one small product photo per row, only from the maker's page.

**Proposed speaker script.**
"Pudu's BellaBot, a restaurant robot, adds three depth cameras to its lidar and drives up to one point two metres a second. Starship's sidewalk robot uses cameras and radar. Both see far more than our single lidar plane, and BellaBot drives eight times faster. Our main gap is clear: we only see one slice of the room."

**Estimated duration.** 0:35

**Evidence and source notes.** LN Part 2 (maker pages and named resellers, access dates in LN).
"Up to 8 times faster": 1.2 m/s against our 0.15 m/s cap. Keenon price range as LN advises.

**Placeholders.** `[TEAM INPUT REQUIRED: our parts cost, to fill the price cell for "Ours"]`

**Presenter.** Yujie

**Transition.** "I'll hand over to Sherman, who'll show how we built it."

---

## Slide 2.1: Six blocks, left to right: sense, odometry, map, localise, navigate, act

**Purpose.** Show the whole system once, simply, and say what we wrote ourselves.

**Key takeaway.** Four ready-made packages carry the maths. We wrote the parts that touch the
hardware.

**On-slide content**

- Title: *Six blocks, left to right*
- Pipeline: *1 Sense → 2 Odometry + fusion → 3 Map → 4 Localise → 5 Navigate → 6 Act*
- Legend: *orange = our code (IMU node, motor node), blue = ready-made packages (rf2o, EKF, SLAM Toolbox, Nav2), grey = hardware and data*
- Footer line: *ROS 2 Jazzy: each program is a node, they share data on named topics. Foxglove to watch live, rosbag to record*

**Recommended visualisation.** `figures/2026-11-11_pipeline.png` across the full width. The
highlighted copies (`pipeline_block1` to `block6`) reappear small on slides 3.1 to 3.7.

**Proposed speaker script.**
"Thanks, Yujie. Here's our software as six blocks: sensing, then odometry and the filter, then the map, localisation, Nav2, and finally the motors. It all runs on ROS 2.

The orange panel is what we wrote: the IMU and motor programs, the robot description and the launch files. The blue panel is the existing packages we built on. I'll cover blocks one to five, and Chloe the motors."

**Estimated duration.** 0:35

**Evidence and source notes.** `figures/pipeline.mmd`. Decision to use packages, not our own maths:
`docs/CA3.md` decisions (not named on the slide).

**Placeholders.** None.

**Presenter.** Sherman

**Transition.** "Let's start with the sensors."

---

## Slide 3.1: We made two cheap sensors trustworthy: measured them, mounted them, and fused them

**Purpose.** Show Sherman's sensing and fusion work: what was built, what was measured, what broke.

**Key takeaway.** Every sensor number in this talk was measured on this robot, and the fusion needed
two fixes before it could be trusted.

**On-slide content**

- Title: *We made two cheap sensors trustworthy*
- Three columns:
  - **Built:** IMU program (100 Hz, 3 s still calibration, a recalibrate button), sensor positions taped into the robot model (lidar 2 cm ahead, 12 cm up), lidar driver fixed at 720 beams, the filter as the only source of position
  - **Measured (← 1.2, 1.3):** lidar 7.05 Hz, 26 to 29 % of pings return nothing, gaps follow the room not the lidar. Gyro noise 0.00175 rad/s at rest. Hand turn: gyro 360.2°, lidar odometry 352.9°. A 1.000 m push read 0.962 m
  - **Fixed:** lidar odometry claimed zero uncertainty, so the filter could not weigh it → noise values fitted from hand tests. Filter missed 30 Hz under load → 20 Hz
- Footnote: *fast turns under-read 9 to 15 %, scan skew a likely part (hypothesis)*

**Recommended visualisation.** Left: `figures/2026-11-11_scan_gaps.png` (one real scan on the map,
9 % of directions empty). Right: `figures/2026-11-10_turn_gyro_vs_rf2o.png`. Pipeline strip with
blocks 1 and 2.

**Proposed speaker script.**
"Before any mapping, we measured both sensors. On the left is one real scan on our map. The orange rays found nothing. About a quarter of readings are empty, but the gaps line up with glass and dark surfaces, not a lidar fault. On the right, a full turn by hand: the gyro read 360.2 degrees, the lidar odometry 352.9. That's why the filter trusts the gyro for turning.

The filter needed two fixes. The lidar odometry claimed zero uncertainty, so we gave it measured noise values. And on a busy Pi the filter couldn't keep thirty updates a second, so it runs at twenty."

**Estimated duration.** 0:50

**Evidence and source notes.** Echo rate 26 to 29 % and the white-box test (TL 2026-10-21, OL§7
row C1). Gyro std (TL 2026-10-30). Turn (TL 2026-10-31 "3.2 spin only"). Push 0.962 m and rf2o hand
tests −2 % turn, −3.8 % push (TL 2026-10-31). Covariance relay and fitted variances (SC S9, TL
2026-10-30 "4.3 relay", TL 2026-10-31 "4.4 variances"). 20 Hz (`ekf.yaml` comment). 9 % of
directions in one published scan (OL§8 scan_gaps). Under-read 9 to 15 % on fast turns (SC S9).

**Placeholders.** None.

**Presenter.** Sherman

**Transition.** "With sensors we trusted, we built the map."

---

## Slide 3.2: One hand-pushed lap made the map, once the scans had a fixed size

**Purpose.** Show the mapping run and the first SLAM failure.

**Key takeaway.** The first map failed because the lidar driver sent a different number of beams
every sweep. One setting fixed it.

**On-slide content**

- Title: *One hand-pushed lap made the map, once the scans had a fixed size*
- Method: *robot pushed by hand round a taped loop, about 7 minutes. Settings frozen after a parameter sweep*
- Challenge: *SLAM Toolbox rejected every scan: "LaserRangeScan contains 1041 range readings, expected 931"*
  - *The driver sent 931 to 1048 beams per sweep. SLAM Toolbox expects the first count forever*
  - *Fix: fixed 720 beams per sweep*

**Recommended visualisation.** Main: `figures/2026-11-10_map_build.gif` (14 s), the map growing as
the lap goes round. Side: `figures/2026-11-11_beam_count.png` (orange wobbling line vs flat blue line
at 720). Optional small: `figures/2026-11-11_slam_sweep.png` labelled "replay". Pipeline strip block 3.

**Proposed speaker script.**
"We mapped by pushing the robot by hand around a taped loop, about seven minutes, so any error came from the mapping, not the motors.

The first attempt failed oddly. SLAM Toolbox rejected almost every scan: it expected 931 readings and got 1041. The driver sent a slightly different count every sweep, the orange line, while SLAM Toolbox expects it fixed. One driver setting held it at 720, the flat blue line, and the next lap gave a proper map."

**Estimated duration.** 0:45

**Evidence and source notes.** Error text and 223 rejected scans (SC S2, OL§7 row C4). Beam counts
from bags `2026-10-31_map_200132` and `_200956` (OL§8). Sweep TL 2026-10-31 "5.5 sweep" (replay).

**Placeholders.** `[ARTEFACT NEEDED: the first "fan" map image from the Pi (~/maps/2026-10-31_room*), for a before and after pair (Sherman)]`

**Presenter.** Sherman

**Transition.** "But how good is that map, with nothing to compare it to?"

---

## Slide 3.3: Loop closure made the map usable, and localisation finds the robot within 3 cm if it starts within 20°

**Purpose.** Map quality with a home-made ground truth, then localisation accuracy and its limit.

**Key takeaway.** We had no ground truth, so we designed one: a lap that starts and ends on the same
taped mark.

**On-slide content**

- Title: *Loop closure made the map usable. Localisation finds the robot within 3 cm*
- The map: *317 × 233 cells of 5 cm, 65.5 m² of free floor*
- Our ground truth: *the lap starts and ends on one taped mark, so any gap is error*
  - **Live:** *0.20 m with SLAM, 0.36 m with odometry only*
  - *Replay of the settings sweep: 0.109 m with loop closure, 0.658 m without (← 1.2)*
- Localisation: *on the home mark, scan matches map to a median 2.6 cm*
- Limit: *30 cm and 20° off still recovers, 31° never does: the matcher searches only ±20° → a taped home mark*
- Small: *old home 0.21 m from furniture, inside Nav2's 0.25 m margin → moved to 0.67 m clear*

**Recommended visualisation.** Left: `figures/2026-11-11_map_overlay.png` (the same scans placed by
SLAM in dark, thin walls, and by odometry only in orange, smeared and doubled walls; odometry aligned
at the first pose). Right: `figures/2026-11-11_wrong_start.png`. Small corner:
`figures/2026-11-11_home_move.png`. Pipeline strip blocks 3 and 4.

**Proposed speaker script.**
"We made our own ground truth. The lap starts and ends on one taped mark, so any gap between start and end is error. Live, SLAM closed to twenty centimetres, odometry alone was thirty-six off. The overlay shows the effect: with SLAM, in dark, walls stay thin. With odometry alone, in orange, they smear and double.

On that map, the robot localises to about three centimetres. But the chart on the right shows a limit. Start thirty centimetres and twenty degrees off, and it recovers. At thirty-one degrees it never does, because matching only searches twenty degrees each way. So the robot always starts on a taped home mark."

**Estimated duration.** 0:50

**Evidence and source notes.** Map size and free area (OL, NB 2026-10-31). Live gaps 0.20 and 0.36 m
(OL§8 drift_vs_slam). Replay gaps 0.109 and 0.658 m over 42 m (TL 2026-10-31 "5.5 sweep"). Median
2.6 cm and the wrong-start rows (TL 2026-11-01 "6.4 wrong start", OL). Home clearances 0.21 and 0.67
m by distance transform (NB 2026-11-10, reproduced by `fig_home_move`).

**Placeholders.** None.

**Presenter.** Sherman

**Transition.** "Then, partway through, the odometry started giving very wrong answers."

---

## Slide 3.4: A person walking behind the robot fooled the odometry

**Purpose.** The one algorithm-assumption failure, told as an investigation. Sherman's longest
debugging effort.

**Key takeaway.** Without wheel encoders the lidar is the odometry, and anything moving with the
robot fools it.

**On-slide content**

- Title: *A person walking behind the robot fooled the odometry*
- The symptom: *a 1 m push read 24 % of the true distance, twice, in two places*
- Seven steps over three days (figure): two wrong leads ruled out, then the cause
- The cause (← 1.2): *lidar odometry assumes everything it sees is still. A person walking behind at a constant distance says "we are not moving"*
- The proof: *127 to 152 scan points behind the robot during the bad pushes, 16 to 18 on good ones*
- Fix, **offline only**: *ignore returns closer than 0.6 m → 99.5 % of the push*
- Our take: *Without encoders the lidar is the odometry, and anything moving with the robot fools it.*

**Recommended visualisation.** First build: `figures/2026-11-11_oi8_ladder.png` (four boxes left to
right: beam count and CPU ruled out in grey, person behind in orange, the range cut in blue, one
evidence line under each). Second build: `figures/2026-11-10_oi8_person_behind.gif` (15 s), the
points behind the robot and odometry falling behind the real distance. Pipeline strip block 2.

**Proposed speaker script.**
"We pushed the robot one metre, and the odometry said twenty-four percent. Same again elsewhere. It looked like a scaling bug.

These cards follow the investigation. We'd just changed the scan format, but live pushes with nobody near read a hundred and one and ninety-six percent, so the format was fine. A slow replay of the bad recording gave the same answer, so it wasn't the Pi being slow either.

What cracked it was counting scan points behind the robot. In the bad pushes, over a hundred sat half a metre behind, moved with it, and vanished when the push ended. It was the person pushing, in orange in the animation. rf2o assumes nothing moves, so someone walking behind tells it the robot is standing still. Ignoring everything within sixty centimetres restored 99.5 percent, so far on recordings."

**Estimated duration.** 1:00

**Evidence and source notes.** SC S7 table, TL 2026-11-01 to 2026-11-03 (push rows, replay rig, "OI-8
live push A/B", "bad bags re-read", "offline fix test"). Evidence files
`evidence/lidar/2026-11-03_oi8_*.txt`. Y21 link on slide 1.6.

**Placeholders.** None.

**Presenter.** Sherman

**Transition.** "With a map and a position we could trust, we handed the robot to Nav2."

---

## Slide 3.5: Nav2 failed seven ways before reaching a goal

**Purpose.** The integration problems of navigation, each linked to a background slide.

**Key takeaway.** Nav2's defaults assume motors that can crawl and a fast computer. Ours had neither.

**On-slide content**

- Title: *Nav2 failed seven ways before reaching a goal*
- Silent mismatch: *Nav2 sent one message type, the motor program listened for another. Wheels never moved, no error*
- Slow computer: *two timeouts 20 → 1000 ms. "Transform data too old": SLAM stamps its correction with the last scan, and scans arrived 0.5 s apart under load → tolerances 0.5 s*
- Stall floor (← 1.4): *Nav2 slowed to 0.045 m/s near obstacles, below the 0.10 m/s the wheels need → slowdown removed, minimum speed 0.10 m/s*
- *Drove backwards → reversing off. Final turn stalled → any final heading accepted*
- Our take: *Navigation defaults assume motors that can crawl and a fast computer. Ours had neither.*

**Recommended visualisation.** `figures/2026-11-11_nav_goal_attempts.png`: left, the ladder of
symptoms and fixes ending in "Goal succeeded", right, the eight evening goals in order. Pipeline
strip block 5.

**Proposed speaker script.**
"Nav2 failed seven ways before reaching one goal. The cards show four.

The first was silent: Nav2 sent commands in one message format, our motor program expected another, so the wheels never moved and nothing complained. Two came from the slow Pi: timeouts too short, and position data arriving half a second late, so we relaxed both. The fourth is the stall floor. Near obstacles, Nav2 slowed to four and a half centimetres a second, below what our wheels can do, so the robot just stopped.

The other three: the home mark sat too close to furniture, and the robot tried to reverse and spin at the goal, so we moved the mark and switched those off. Every fix was a setting, not new code."

**Estimated duration.** 0:55

**Evidence and source notes.** Ladder from `tools/analysis/slide_figs.py` LADDER (TL 2026-11-10,
handover of 2026-11-10, commits). Message type mismatch (OL§7 row C8, `enable_stamped_cmd_vel`).
Timeouts and tolerances (commits a0a54b1, 7fd9037). Load 13 to 22 (OL). Evening goals from
`bt_navigator` logs (GOALS_EVENING).

**Placeholders.** `[ARTEFACT NEEDED: a docs/test_log.md row for the 2026-11-10 evening Nav2 runs and "Goal succeeded", so every number here has its command (Sherman)]`

**Presenter.** Sherman

**Transition.** "For the last block, over to Chloe, who'll show what it took to make the wheels obey."

---

## Slide 3.6: To drive itself, the robot first needed stable power

**Purpose.** Introduce the physical robot and the power problem that crashed Nav2.

**Key takeaway.** Half our early Nav2 crashes were the Pi browning out, not software.

**On-slide content**

- Title: *To drive itself, the robot first needed stable power*
- Parts: *Raspberry Pi 4, 2D lidar on top, IMU, L298N driver, 4 DC gear motors in two pairs, motor battery, power bank for the Pi, motor switch as the kill switch*
- No screen: *SSH over the network, Foxglove in the browser*
- Challenge: *the Pi rebooted and Nav2 shut down mid-run*
  - *Wall supply: under-voltage in 67.5 % of samples*
  - *Power bank: 0 of 60 samples*
  - *A loose motor wire rebooted the Pi twice*
- Safety: *lidar stop at 0.20 m, tested stopping at 0.155 m*

**Recommended visualisation.** Left: `figures/2026-11-11_robot_labelled.png`. Right:
`figures/2026-11-10_power.png` (67.5 % vs 0 %). Optional small: `figures/2026-11-11_safety_zones.png`.
Pipeline strip block 6.

**Proposed speaker script.**
"Thanks, Sherman. Early on, the Pi kept rebooting and Nav2 kept shutting down mid-run. So we logged the Pi's power every two seconds, and these tiles show the result. On the wall supply it was short of voltage two thirds of the time. On a power bank, zero of sixty samples. A loose motor wire also rebooted it twice. Until power was stable, no driving result meant anything."

**Estimated duration.** 0:40

**Evidence and source notes.** Under-voltage 67.5 % and 0 of 60 (`vcgencmd get_throttled` every 2 s,
OL§7 row C11, `docs/CA3.md` open issue on power). Loose wire (OL§7 row C10). Lidar stop test (TL
2026-11-09). Photos 2026-11-11.

**Placeholders.** `[VERIFY: the black cable trailing behind the robot in the box video. If it is the Pi's power from the wall, the slide's "power bank" claim needs a sentence (Chloe)]`
`[TEAM INPUT REQUIRED: bill of materials and total cost, if "low-cost" should carry a number]`

**Presenter.** Chloe

**Transition.** "With stable power, we could calibrate the motors."

---

## Slide 3.7: The wheels stall below 0.10 m/s and the battery lasts one run

**Purpose.** Motor calibration, the stall floor, and two motor problems that looked like software.

**Key takeaway.** Open-loop motors need a measured duty-to-speed curve, a kick to start, and a fresh
battery.

**On-slide content**

- Title: *The wheels stall below 0.10 m/s and the battery lasts one run*
- First drive: *curved 35 to 40°, would not start slowly, then overshot 2 to 3 times when the Pi was busy*
  - *The Pi makes PWM in software, and at 1 kHz its timing slipped under load → 100 Hz*
- Calibration (← 1.4): *speed = 2.46 × (duty − 0.078), fitted*
  - *Stall below about 0.10 m/s → a kick of duty 0.30 for 0.35 s from rest*
- Result: *1 m straights of 0.96, 1.06 and 1.16 m, 2 of 3 within ±10 cm*
- Battery: *the same command drove 0.84, 0.74, then 0.38 m → switch off and on between runs*
- Silent failure: *a "live" setting was never passed on, so live runs drove nothing and nothing complained*

**Recommended visualisation.** Left: `figures/2026-11-10_motor_curve.png` (stall band shaded, the
0.045 m/s slowdown from 3.5 marked inside it). Right: `figures/2026-11-10_straights.png` (lidar
odometry distance of the 10 Nov runs, tape values in the legend). Pipeline strip block 6.

**Proposed speaker script.**
"The first drive was rough: the robot curved up to forty degrees, wouldn't start slowly, and sometimes overshot two to three times. The Pi generates the motor signal in software, and when it got busy the timing slipped. Slowing the signal from a thousand to a hundred pulses a second fixed it.

On the left is our calibration. Speed rises in a line with duty cycle, but below ten centimetres a second the wheels stall, the same floor that stopped Nav2, so every start gets a short kick. On the right, two of three one-metre runs landed within ten centimetres, and the flatter lines show the battery fading.

One more silent failure: the setting that turns the motors live was never passed through, so our first live runs didn't move."

**Estimated duration.** 0:55

**Evidence and source notes.** PWM, fit and kick (NB 2026-11-09, PR 38, `AGENTS.md` Motors row).
Straights 0.96 m (TL 2026-11-09), 1.06 and 1.16 m and battery fade 0.84, 0.74, 0.38 m (TL
2026-11-10 CP5 rows). The straights figure shows the 10 Nov runs only, the 0.96 m run is from
9 Nov. Dry-run bug (OL§7 row C12, PR 42).

**Placeholders.** `[VERIFY: the 0.84 m run. The straights figure has 0.74 and 0.38 m runs labelled "low battery" and "flat battery", but no 0.84 m run (Chloe)]`

**Presenter.** Chloe

**Transition.** "With all of that in place, here's what the robot did on its own."

---

## Slide 3.8: It works: a goal 1.5 m away reached on its own, and a box driven around

**Purpose.** The headline result, shown honestly.

**Key takeaway.** The whole loop closed once: map, localise, plan, drive, arrive.

**On-slide content**

- Title: *It works: a goal reached on its own, around a box*
- *"Goal succeeded": 1.5 m in 93 s, from the home mark*
- *Box about 1 m ahead, path about 3 m* (by eye)
- *1 success out of 8 goals that evening. The others were cancelled by hand*
- Our take: *One success proves the loop closes, not that it is reliable.*

**Recommended visualisation.** Clip V2 (`figures/2026-11-10_V2_box_full.mp4`, 45 s at 1x) as the
main visual, playing while Chloe speaks. Beside it: `figures/2026-11-11_goal_on_map.png` (home mark,
goal, 0.25 m margin). Pipeline strip with all six blocks lit, or no strip.

**Proposed speaker script.**
"We give Nav2 a goal on the far side of a box. The robot plans around it and drives there with nobody touching it, and after ninety-three seconds Nav2 reports success.

To be upfront: that evening we sent eight goals, and one succeeded. We cancelled the rest as we found faults. So this proves the whole system works together, but not yet that it's reliable."

**Estimated duration.** 0:50 (the clip plays during the script)

**Evidence and source notes.** `bt_navigator` log 2026-11-10, launch 7359: start (−1.35, −0.29),
goal (−2.67, 0.42), 92.8 s, eight goals that evening (GOALS_EVENING in
`tools/analysis/slide_figs.py`). The driven path was not recorded, so the line on the map figure is
straight.

**Placeholders.** `[VERIFY: the video is the "Goal succeeded" run (45 s video vs 92.8 s goal). If it is a cancelled goal, change the caption to "a later goal around the box" (Chloe)]`
`[ARTEFACT NEEDED: tape numbers for the box run: box position and size, path length, sideways drift (Chloe)]`

**Presenter.** Chloe

**Transition.** "Looking back, there's a clear pattern in what went wrong."

---

## Slide 3.9: Almost every challenge was integration, and most were surprises

**Purpose.** The insight slide the brief values most.

**Key takeaway.** The algorithms worked. Integration with cheap hardware and a slow computer did not,
at first.

**On-slide content**

- Title: *Almost every challenge was integration, and most were surprises*
- *14 challenges in three weeks*
  - *13 from hardware, computer load, interfaces between programs, or process*
  - *1 from an algorithm's assumption: the person behind the robot*
- *8 of 14 were unexpected*
- *Two silent failures: the message type and the "live" setting. Nothing reported an error*
- *Replays disagreed, so every result in this talk is live*
- Our take: *Package defaults assume better hardware, so every default had to be re-tested on ours.*

**Recommended visualisation.** Top: `figures/2026-11-10_challenge_timeline.png` (when each problem
hit, coloured by kind, milestones above). Bottom: `figures/2026-11-11_root_cause.png` (five causes,
unexpected in orange).

**Proposed speaker script.**
"We logged fourteen challenges in three weeks. Thirteen came from hardware, the slow computer, mismatched programs or process, and the bars show cheap hardware alone caused six. Only one, in coral, came from an algorithm's assumption: the person behind the robot. Eight were surprises.

Two were silent, the message format and the live setting, and the robot just sat there. So our main takeaway: these packages assume better hardware than ours, and every default had to be retested."

**Estimated duration.** 0:35

**Evidence and source notes.** OL§7 challenge table (14 rows, Group and Expected columns). Root-cause
figure counts 8 unexpected, 6 expected or partly. Timeline from OL§7 dates.

**Placeholders.** `[TEAM INPUT REQUIRED: one agreed count. OL§7 says 1 of 14 challenges is an algorithm assumption. If the ±20° matcher window (slide 3.3) also counts, it is 2. Use the same number here and in the report]`

**Presenter.** Chloe

**Transition.** "So what would we do differently?"

---

## Slide 3.10: What we learned, what limits us, and what we would do next

**Purpose.** Conclusions and future work (25 % of the rubric).

**Key takeaway.** Measure physical limits on day one, test live, and make silent failures loud.

**On-slide content**

- Title: *What we learned, what limits us, what comes next*
- **Lessons:**
  - *Integration was the hard part, not the algorithms*
  - *Measure physical limits on day one: stall speed, power, CPU load*
  - *Test on the real robot, not on replays*
  - *When there is no ground truth, design one*
  - *Make silent failures loud*
- **Limits:** *no encoders, one navigation success, a slow Pi, a one-plane lidar, no tests with people moving during navigation*
- **Next:** *wheel encoders, hardware PWM, a faster computer, filter people out of the scan live, correct scan skew*

**Recommended visualisation.** Three columns of plain text (lessons, limits, next), no figure and no icons.

**Proposed speaker script.**
"On the left, five lessons. Integration was the hard part, not the algorithms. Measure physical limits like stall speed, power and processing load on day one, because each cost us days. Test on the real robot, not recordings. Without ground truth, design one. And make silent failures loud.

On the right, our limits and next steps: wheel encoders, a hardware motor signal, a faster computer, and running the people filter live."

**Estimated duration.** 0:40

**Evidence and source notes.** OL v5 slide 3.10. Offline people filter (SC S7). Scan de-skew [S23].

**Placeholders.** `[VERIFY: an optional future-trends sentence on the AV industry. LN Part 3: Waymo's 6th generation uses 13 cameras, 4 lidar and 6 radar for redundancy, while Tesla removed radar (2021) and ultrasonic sensors (2022) for cameras only. The Tesla facts are second-hand in LN. Add only if checked, cost about 0:10]`

**Presenter.** Chloe

**Transition.** "So, to close."

---

## Slide Close: A low-cost robot can map a room and navigate it on its own, once every physical limit is measured and designed around

**Purpose.** One sentence to remember, then questions.

**Key takeaway.** The verdict.

**On-slide content**

- *A low-cost robot can map a room and navigate it on its own, once every physical limit is measured and designed around.*
- *Thank you. Questions?*

**Recommended visualisation.** The sentence in large type. A still frame of the robot beside the box
from V2 behind it, faded.

**Proposed speaker script.**
"Back to our question: yes, a low-cost robot can map a room and navigate it on its own, as long as every physical limit is measured and designed around. Thank you, and we're happy to take questions."

**Estimated duration.** 0:15

**Evidence and source notes.** OL v5 Close.

**Placeholders.** `[ARTEFACT NEEDED: one still frame from V2 with the robot beside the box (Chloe or Sherman, ffmpeg)]`

**Presenter.** Chloe

**Transition.** None.

---

## C. Brief and rubric coverage check

Rubric: presentation skills 20 %, content 40 %, conclusions 25 % (including future work), peer
assessment 15 %.

| Assessment item | Slide(s) | Evidence strength and gaps |
|---|---|---|
| Topic overview | T, 1.1 | Strong. Aim, our robot against a road AV, the drift GIF |
| State of the art | 1.2, 1.6 | Good. Four verified papers with what each found. Review [R25] cited, not read in full |
| Product or paper comparison | 1.1 (Waymo), 1.6 (papers), 1.7 (products) | Strong. Four papers, three indoor products, one road AV |
| Brief technical information | 1.2 to 1.5, 2.1, 3.1 to 3.7 | Strong. Choices, parameters and assumptions, no textbook definitions |
| Future trends | 1.7, 3.10 | Partial. Products show the move to lidar plus cameras. Our next steps on 3.10. The Waymo and Tesla sensor trend is an optional, unverified sentence |
| Own insights | 3.4, 3.5, 3.9, five "Our take" lines | Strong. The integration finding, the person-behind investigation, live vs replay |
| Results with conditions | 3.1, 3.3, 3.7, 3.8 | Strong on sensing and mapping. Navigation is one success out of eight, said plainly |
| Limitations | 3.3, 3.4, 3.8, 3.10 | Stated on the slides and gathered on 3.10 |
| Conclusions and future work | 3.10, Close | Present. Concrete next steps tied to measured causes |
| Each student presents own contribution | Section D | Yujie background, Sherman sensing to navigation, Chloe hardware to conclusion |
| Videos at most 2 minutes | V1, three GIFs, V2 | 108 s |

---

## D. Timing and team handover plan

| Slide | Section | Presenter | Duration | Elapsed |
|---|---|---|---|---|
| T | Title | Yujie | 0:30 | 0:30 |
| 1.1 | Our robot against a road AV | Yujie | 0:40 | 1:10 |
| 1.2 | Lidar, rf2o, SLAM Toolbox and their assumptions | Yujie | 0:50 | 2:00 |
| 1.3 | EKF configuration | Yujie | 0:35 | 2:35 |
| 1.4 | Actuation model, open loop, stall floor | Yujie | 0:35 | 3:10 |
| 1.5 | Nav2 configuration | Yujie | 0:40 | 3:50 |
| 1.6 | Papers vs ours | Yujie | 0:40 | 4:30 |
| 1.7 | Products vs ours | Yujie | 0:35 | 5:05 |
| | *Handover to Sherman* | | 0:05 | 5:10 |
| 2.1 | Pipeline | Sherman | 0:35 | 5:45 |
| 3.1 | Sensing and fusion | Sherman | 0:50 | 6:35 |
| 3.2 | Mapping | Sherman | 0:45 | 7:20 |
| 3.3 | Map and localisation results | Sherman | 0:50 | 8:10 |
| 3.4 | The person behind | Sherman | 1:00 | 9:10 |
| 3.5 | Navigation | Sherman | 0:55 | 10:05 |
| | *Handover to Chloe* | | 0:05 | 10:10 |
| 3.6 | Hardware and power | Chloe | 0:40 | 10:50 |
| 3.7 | Motors | Chloe | 0:55 | 11:45 |
| 3.8 | Result | Chloe | 0:50 | 12:35 |
| 3.9 | Analysis | Chloe | 0:35 | 13:10 |
| 3.10 | Lessons, limits, next | Chloe | 0:40 | 13:50 |
| Close | Verdict | Chloe | 0:15 | 14:05 |

**Total: 14:05**, including two handovers of about 5 s, inside the 15-minute limit with 0:55 spare.
Videos play while the presenter talks: V1 on T, the drift GIF on 1.1, the map GIF on 3.2, the
person GIF on 3.4, V2 on 3.8. If rehearsal runs long, cut in this order: the slam_sweep inset on
3.2, the pose-graph inset on 1.1, then merge 1.3 into 1.2 (saves about 0:25).

**Speaking time per person (slides only):** Yujie 5:05, Sherman 4:55, Chloe 3:55. Yujie's block is
background only and carries no measured numbers, so each person's measured work stays with them.

**Handover lines** (the outgoing presenter says the first half, the incoming one picks up):

| From, to | Line |
|---|---|
| Yujie to Sherman (after 1.7) | "Sherman will now show how we put these parts together on the robot." / "Here is the whole system, six blocks." |
| Sherman to Chloe (after 3.5) | "Chloe will now show block six: what it took to make the wheels do what Nav2 asked." / "This is the robot." |

---

## E. Appendix slides (backup for questions, not in the 15 minutes)

| # | Slide | Likely question it answers | Content from |
|---|---|---|---|
| A1 | Software stack and frame chain | "How do the frames fit together?" | `figures/tf_tree.mmd` (map → odom → base_footprint → laser, imu_link), key YAML values |
| A2 | Every number with its command | "Where does that number come from?" | Table from `docs/test_log.md` |
| A3 | The person behind and the replays, in numbers | "How sure are you about the person?" | `figures/2026-11-10_oi8_and_replay_bars.png` |
| A4 | Planner paths on the saved map | "Does the planner work for other goals?" | `results/maps/2026-11-08_planner_paths.png` |
| A5 | Every challenge, in detail | "What else went wrong?" | OL§7 table and `slam_challenges.md`: configure delay at start, `map_start_pose`, covariance relay, lidar start hang |
| A6 | Every node and topic | "What exactly is connected?" | `figures/2026-11-11_pipeline_detailed.png` |

Draft answers to ten likely questions are in OL section 5. Two to rehearse:

- **"Why only one successful goal?"** The evening went on finding and fixing faults, and the battery
  gave about one run per charge. We claim the loop works, not a success rate.
- **"Why packages, not your own code?"** The brief allows them, and the hard part turned out to be
  integration anyway. Our own EKF and planner stay a documented fallback.

---

## F. Final quality audit

| # | Question | Result |
|---|---|---|
| 1 | One coherent story? | Yes. Question, concepts, pipeline, each block in order, result, pattern, lessons, verdict |
| 2 | Pitched at an AV-course audience? | Yes. Course concepts are not defined. Background slides state our choices, parameters and assumptions, and back-links point to them |
| 3 | Measured vs fitted vs by-eye clear? | Yes, with tags. Replay numbers labelled as replay. The box path is by eye until taped |
| 4 | Strongest results given space? | Yes. The person-behind investigation and the ground-truth design each have a full slide |
| 5 | Every claim backed? | Yes except the evening Nav2 runs, which need a test_log row (placeholder on 3.5) |
| 6 | One purpose and one useful visual per slide? | Yes. Every slide but 3.10 and Close has a project figure |
| 7 | Scripts add value beyond bullets? | Yes. They explain why (why the filter leans on the gyro, why 31° fails, why the robot stopped at 0.045 m/s) |
| 8 | Limitations stated plainly? | Yes. 1 of 8 goals on 3.8, offline-only fix on 3.4, limits on 3.10 |
| 9 | Fits 15 minutes? | Slot times sum to 14:05, set from each script at 156 words a minute, a normal pace for a rehearsed talk. Scripts and transitions total about 2,122 words, about 13:36 at 156 words a minute, leaving room for the clips and pauses. Rehearse with a timer |
| 10 | Each person presents own work? | Yes. Yujie sets the design against the field, Sherman presents sensing to navigation, Chloe presents hardware to conclusion |
| 11 | No internal codes on slides? | Yes. Codes appear only in the evidence notes of this file |

**Discrepancies carried from the source** (do not resolve silently on the slides):

- Box video length 45 s vs "Goal succeeded" 92.8 s (slides T, 3.8).
- Algorithm-assumption count, 1 or 2 of 14 (slide 3.9).
- Battery fade 0.84 m has no run in the straights figure (slide 3.7).
- The robot in the box video trails a cable, while slide 3.6 says the Pi runs on a power bank.
- Push read "24 %" (TL) and "25 %" (Chloe's earlier plan). This file uses 24 %.

---

## Artefacts to collect, by owner

| Owner | Item | Slides |
|---|---|---|
| Chloe | Confirm which run the box video shows. Tape numbers for the box run. The trailing cable. The 0.84 m run. Bill of materials if a cost goes on a slide | T, 3.6, 3.7, 3.8 |
| Sherman | `docs/test_log.md` row for the 2026-11-10 evening Nav2 runs. First "fan" map image from the Pi. Agree the challenge count | 3.2, 3.5, 3.9 |
| Yujie | Rehearse 1.1 to 1.7 against the timer. Check the Waymo column on 1.1. Optional: the Tesla facts for 3.10 | 1.x, 3.10 |
| Any member | Still frame from V2 for the Close slide | Close |

---

## Changelog

| Date | Who | Change |
|---|---|---|
| 2026-11-11 | Claude (Opus 5.5) + Sherman | Created from `slides_outline.md` v5, in the format of the Gappler interim slide content spec. 20 core slides, 7 backup. Pipeline-order split (two handovers), sensing and fusion slide 3.1 for Sherman, new figures of 2026-11-11, no internal codes on slides |
| 2026-11-11 | Claude (Opus 5.5) + Sherman | Pitched for an AV-course audience: background no longer defines SLAM, EKF, PWM or pure pursuit. 1.1 now compares our robot with a road AV (Waymo), 1.2 to 1.5 state our choices, parameters and assumptions, new 1.7 compares indoor delivery products. Backup A7 folded into 1.7. Total 14:35 |
| 2026-11-11 | Claude (Opus 5.5) + Sherman | Figures simplified (fewer words): fusion flow redrawn, motor drive, lidar plane, safety zones, Nav2 concept, home move, and the person-behind figure now four boxes. Tables on 1.6 and 1.7 are built natively in the slides, the table images were deleted |
| 2026-11-11 | Claude (Opus 5.5) + Sherman | All 21 scripts rewritten for spoken delivery: shorter sentences, signposted lists, numbers rounded aloud, each transition leading into the next slide's opening, technical detail kept. New rule 11 |
| 2026-11-11 | Claude (Opus 5.5) + Sherman | Scripts trimmed to fit, each slot set from its script length. Slide 3.3 now uses `figures/2026-11-11_map_overlay.png` (same scans placed by SLAM and by odometry only, overlaid) instead of the side-by-side maps |
| 2026-11-11 | Claude (Opus 5.5) + Sherman | Scripts rewritten again for natural delivery (connected sentences instead of fragments) and now point at the figures ("on the left", "the orange rays"). Slots set at 156 words a minute |
| 2026-11-11 | Claude (Opus 5.5) + Sherman | Deck built: `report/slides/CA3_presentation.pptx` (26 slides) from the group template by `report/slides/build_deck.py`, scripts in `report/slides/speaker_scripts.py`. Changes from this spec: new slide "This is the robot we built" (labelled top and side photos, Sherman, opens the Pipeline section, script key `R`); 1.1 now shows a Waymo Jaguar I-Pace photo and quotes that car's sensors (29 cameras, lidar, radar; LN Part 3) instead of the 6th generation; 1.7 compares BellaBot and Starship (photos from Wikimedia Commons, credits in `report/figures/web/CREDITS.md`) with ours, Keenon and Servi dropped for lack of free photos; 3.6 shows the power chart (the robot photo moved to the new slide); 3.9 and 3.10 redrawn as native shapes; no window dots on any slide; template's play triangle removed. Timing table not yet updated for the new slide (about +0:25) |
| 2026-11-11 | Claude (Opus 5.5) + Sherman | Scripts rewritten for the built deck and audited in deck order: every visual reference matches the slide as built (cards, tiles, overlay, video), no term is used before it is introduced (rf2o, SLAM Toolbox, duty cycle, stall floor, Nav2 slowdown), dropped references to removed items (clip on the title, pipeline strip, progress checker, timeline). New scripts for the Aim slide (`A`) and the robot slide (`R`), see `report/slides/speaker_scripts.py`. Speaker notes in the deck are plain paragraphs with the hand-over as the last line. About 2,040 words, 13:05 at 156 words a minute: Yujie 5:30, Sherman 4:25, Chloe 3:05 |

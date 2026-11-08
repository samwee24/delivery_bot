# Literature notes: verified source base for the CA3 report and slides

Accessed 2026-11-03. Every fact is followed by the page it came from. Anything not seen in a source is marked "not found" or "to check". Citation keys for papers follow the References table in [`docs/slam.md`](../docs/slam.md); new keys are defined in Part 2 and Part 3.

## Verification result (read this first)

All six DOIs in `docs/slam.md` resolve to the paper named there. None failed. Method: Crossref record for each DOI, plus the full text for K26 and M26 (open access, via Europe PMC) and Y21 (arXiv).

| Key | DOI | Matches docs/slam.md? | Evidence |
| --- | --- | --- | --- |
| [K26] | 10.3390/s26134264 | Yes. Kudriashov, Koszyk, Hyla, Ambroziński; *Sensors* 26(13), 4264; published 2026-07-04 | [Crossref](https://api.crossref.org/works/10.3390/s26134264), [full text PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/) |
| [M26] | 10.3390/s26175468 | Yes. Merrick, Nandikolla; *Sensors* 26(17), 5468; published 2026-08-29 | [Crossref](https://api.crossref.org/works/10.3390/s26175468), [full text PMC13568328](https://pmc.ncbi.nlm.nih.gov/articles/PMC13568328/) |
| [Y21] | 10.1109/ROBIO54168.2021.9739394 | Yes. Ye, Chen, Chen, He, Guan, Zhang; 2021 IEEE ROBIO. Author list in docs/slam.md says "Ye et al.", fine | [Crossref](https://api.crossref.org/works/10.1109/ROBIO54168.2021.9739394); preprint [arXiv 2204.08163](https://arxiv.org/abs/2204.08163) |
| [R25] | 10.3390/rs17071214 | Yes. Ran, Xu, Tan, Luo; *Remote Sensing* 17(7); 2025-03-28 | [Crossref](https://api.crossref.org/works/10.3390/rs17071214) |
| [J16] | 10.1109/ICRA.2016.7487647 | Yes. Jaimez, Monroy, Gonzalez-Jimenez; ICRA 2016 | [Crossref](https://api.crossref.org/works/10.1109/ICRA.2016.7487647) |
| [MJ21] | 10.21105/joss.02783 | Yes. Macenski, Jambrecic; JOSS 6(61); 2021 | [Crossref](https://api.crossref.org/works/10.21105/joss.02783) |

Three things in `docs/slam.md` and the plan need correcting or softening, because the papers say something different from how we use them:

1. **K26 does not test the IMU.** Its comparison is AMCL feedback on versus off. The IMU is fused in both conditions ([K26 full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/)). K26 is the anchor for E3 (repeatability), not for E2 (IMU ablation).
2. **K26 is mostly offline replay.** 12 recorded datasets were reprocessed 720 times on a workstation, so the run-to-run spread is SLAM stochasticity on identical input, not repeated driving ([K26 full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/)). Our E3 (five driven runs) measures something broader. State this in the report.
3. **M26's "IMU ablation" is wheel odometry versus wheel odometry plus IMU yaw rate, on a public ROS 1 dataset.** It has wheel encoders and ground truth; we have neither encoders nor motion-capture ground truth ([M26 full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13568328/)). Our E2 is rf2o alone versus rf2o plus IMU, so it is an analogue, not a replication.

The "SLAM Toolbox without AMCL" condition in K26 (rf2o + IMU through `robot_localization`, into SLAM Toolbox, ROS 2 Jazzy) is the closest published match to our stack ([K26 full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/)).

---

## Part 1: replication targets

### [K26] Kudriashov et al., Sensors 26(13), 4264 (2026)

Title: "A Real-World Benchmark of Monte Carlo-Assisted EKF Odometry for Online Pose Estimation in 2D LiDAR SLAM". Open access, CC BY ([PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/)).

| Item | What the paper says | Source |
| --- | --- | --- |
| Question | Does AMCL feedback (AMCL pose, computed against the map the SLAM backend is building, fed into the EKF) make 2D LiDAR SLAM more repeatable? Repeatability is between-run dispersion, not accuracy against ground truth | [PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/) |
| Platforms | Husarion Panther (wheeled) and Boston Dynamics Spot (quadruped) | same |
| Lidar | Ouster OS-1, 64-channel 3D lidar with built-in 6-DOF IMU, same payload on both robots. Converted to a 2D scan with PointCloud-to-LaserScan (height 0.1 to 2.0 m, min range 0.45 m, max range 100 m) | same |
| Compute on robot | NVIDIA Jetson, time-synchronised via hardware clock. Ubuntu 24.04, ROS 2 Jazzy | same |
| Compute for results | All 720 SLAM runs replayed offline on a workstation: AMD Ryzen 7 5800X, 32 GB RAM, Arch Linux in Docker. Embedded performance was not evaluated | same |
| Software stack | RF2O laser odometry (20 Hz); `robot_localization` EKF (20 Hz, `two_d_mode: true`) fusing RF2O {x, y, z, vx, vy, vyaw}, IMU {orientation and rates}, and in AMCL runs an AMCL {x, y}; SLAM backends Cartographer, GMapping, SLAM Toolbox. No wheel encoders are listed among the EKF inputs | same |
| Fixed-parameter rule | Same parameters for all repeated runs of a backend; no environment-specific tuning after seeing results. All backends: 0.05 m map resolution, 0.5 m and 0.2 rad update thresholds | same |
| Environment | AGH University of Krakow, main building: A long repetitive corridor (longest paths), B feature-rich offices and open areas, C mixed corridor and rooms. Path lengths about 163 to 287 m | same |
| Data collected | 2 measurements per environment per platform = 12 datasets. Spot replayed an autonomous mission with AprilTag markers; Panther was human-assisted along the same route | same |
| Runs | 10 SLAM iterations x 3 backends x 2 conditions (AMCL on, off) per dataset = 720 SLAM executions | same |
| Speeds | Panther about 0.37 to 1.09 m/s mean; Spot about 0.45 to 0.92 m/s mean (Table 4) | same |
| Metrics | Pairwise ATE (RMSE after SE(2) alignment, no scale) between every pair of runs; centroid ATE; translational RPE proxy; run completeness; occupied-cell IoU between maps after ICP alignment; Welch, Mann-Whitney, Cliff's delta, 95 % bootstrap CIs | same |
| Ground truth | None. ATE here means dispersion between runs, "they do not represent error with respect to a true physical trajectory" | same |
| Dataset | RODBUK Dataverse, [10.58032/AGH/FKFLPY](https://doi.org/10.58032/AGH/FKFLPY) (raw ROS 2 bags on request) | same |

**Headline numbers, SLAM Toolbox (our backend), AMCL off versus on, pairwise ATE**

| Case | AMCL off | AMCL on | Source |
| --- | --- | --- | --- |
| Panther, Env A, meas. 1 | 0.198 m | 0.330 m | [PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/) |
| Panther, Env A, meas. 2 | 0.230 m | 0.282 m | same |
| Panther, Env C, meas. 2 | 0.217 m | 0.333 m | same |
| Spot, Env A, meas. 1 | 2.250 m | 2.260 m | same |
| Spot, Env C, meas. 2 | 0.281 m | 0.220 m | same |

**Headline numbers, map IoU.** GMapping and SLAM Toolbox "often ranged between 0.02 and 0.35" while Cartographer was typically 0.4 to 0.75. SLAM Toolbox on Spot, Env B meas. 1: 0.132 with and without AMCL. Spot, Env A meas. 2: 0.185 off, 0.105 on. ([PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/))

**Authors' conclusions.** AMCL-EKF feedback "is not universally beneficial"; it helps in some environment/platform/backend combinations and hurts in others, notably repetitive corridors. They recommend gating the correction on confidence. ([PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/))

**Assumptions and limits the authors state** ([PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/), Limitations section): no external ground truth, so a run set can be repeatable and still biased; the two platforms did not run identical trajectories; velocities come from TF, not an independent measure; EKF and AMCL parameters fixed, so no sensitivity analysis; no onboard computational profiling; pairwise metrics are not independent because many runs reuse the same raw dataset; limited to 2D lidar occupancy-grid SLAM, indoor, GPS-denied.

### [M26] Merrick and Nandikolla, Sensors 26(17), 5468 (2026)

Title: "Evaluating the Impact of Extended Kalman Filter Odometry on the Performance of 2D LiDAR SLAM Algorithms". Open access ([PMC13568328](https://pmc.ncbi.nlm.nih.gov/articles/PMC13568328/)).

| Item | What the paper says | Source |
| --- | --- | --- |
| Question | How much of an odometry improvement (wheel odometry versus EKF of wheel odometry plus IMU) survives into the final SLAM trajectory? | [PMC13568328](https://pmc.ncbi.nlm.nih.gov/articles/PMC13568328/) |
| Data | Not a new robot. MIT Stata Center public dataset (`2012-04-06-11-15-29.bag`), PR2 robot, Hokuyo UTM-30LX 2D lidar, wheel encoder odometry, MicroStrain 3DM-GX2 IMU, ground-truth trajectory included | same |
| Software | ROS Melodic (ROS 1); GMapping 1.4.2, Karto SLAM (slam_karto) 0.8.1, SLAM Toolbox 1.1.6; `robot_localization` 2.6.12; `evo` 1.37.0 | same |
| EKF | 100 Hz, `two_d_mode`. Fuses only longitudinal wheel velocity vx and IMU yaw rate wz. Wheel velocity covariance reassigned to 0.01 (m/s)^2 after residual analysis against ground truth; IMU yaw-rate covariance 1.44e-4 (rad/s)^2 from the datasheet | same |
| SLAM config | Package defaults, map resolution 0.05 m, update thresholds 0.5 m / 0.5 rad (Karto 0.2 m / 0.1 rad) | same |
| Trajectories | A, B, C are segments of D, the full route; they are not independent | same |
| Runs | 5 repeats x 2 odometry sources x 4 trajectories x 3 algorithms = 120 SLAM executions, replayed from the bag | same |
| Metrics | Translational and rotational APE RMSE, mean, max (`evo`, SE(2)-type alignment), before and after SLAM; Welch's t-test across the 5 repeats | same |

**Headline numbers**

- Before SLAM, the EKF cut translational APE RMSE by about 60 to 75 % and rotational by 65 to 77 %. Full-route example: translational 9.5720 m raw versus 2.7716 m EKF (Table 2). ([PMC13568328](https://pmc.ncbi.nlm.nih.gov/articles/PMC13568328/))
- After SLAM the gain mostly vanishes. SLAM Toolbox translational APE RMSE, raw versus EKF: A 0.2748 versus 0.2755 m (-0.2 %); B 0.2710 versus 0.2780 (-2.6 %); C 0.3572 versus 0.3663 (-2.5 %); D 0.3636 versus 0.3578 (+1.6 %). Negative means the EKF was worse. (Table 3, same source)
- Rotational changes were larger and inconsistent in sign: SLAM Toolbox -22.6 % (A), +36.9 % (B), -29.7 % (C), +24.0 % (D) (Table 3, same source).
- Karto and SLAM Toolbox were worse with the EKF in most trajectory conditions; GMapping was mixed (same source).

**Assumptions and limits the authors state** ([PMC13568328](https://pmc.ncbi.nlm.nih.gov/articles/PMC13568328/)): single recorded traversal, so repeats measure SLAM run-to-run variability, not independent traversals; the EKF covariance was calibrated against the same ground truth later used for evaluation ("ground-truth-informed", listed as a limitation); trajectories A to C are subsets of D; scan matcher, thresholds and loop-closure settings were not varied, so causes cannot be isolated.

### [Y21] Ye et al., IEEE ROBIO 2021

Title: "Mapping While Following: 2D LiDAR SLAM in Indoor Dynamic Environments with a Person Tracker". Read from the arXiv version, [2204.08163](https://arxiv.org/abs/2204.08163), whose text I took to be the same paper (same title and authors); the IEEE version was not read.

| Item | What the paper says | Source |
| --- | --- | --- |
| Question | Does removing people from the scan, using a leg-detecting tracker, improve 2D lidar maps, while the robot also follows a person instead of being joysticked? | [arXiv PDF](https://arxiv.org/pdf/2204.08163) |
| Hardware | Clearpath Dingo-O (holonomic); Hokuyo UTM-30LX (0.1 to 30 m, 270 degrees, 0.25 degree resolution, 40 Hz); laptop with Intel Core i5-10200H | same |
| Software | ROS; GMapping and Cartographer, map resolution 0.02 m; people detection by clustering plus random forest, Kalman filter plus global-nearest-neighbour tracking | same |
| Environments | Two rooms in an office building: a long corridor, and a meeting room with chairs and a large table | same |
| Conditions | No people (slow, smooth run, used as the ground-truth map); 1 person leading; 2 people walking in front. The 1-person and 2-people experiments were each repeated 5 times | same |
| Metric | ADNN (average distance to nearest neighbour) between the estimated map and the no-people map, after PCA and ICP registration | same |

**Headline numbers (mean ADNN, filtered versus unfiltered scans)**

- Corridor, GMapping, 1 person: 4.98 cm filtered versus 39.36 cm unfiltered. 2 people: 5.90 cm versus 80.24 cm. ([arXiv PDF](https://arxiv.org/pdf/2204.08163))
- Corridor, Cartographer: 1.36 cm filtered versus 2.16 cm unfiltered (the text's wording is garbled; this is my reading, to check against the IEEE version). (same source)
- Meeting room, GMapping filtered: 10.46 cm (1 person), 10.30 cm (2 people); unfiltered values were only in the figure, not read. Cartographer gained little in the meeting room. (same source)
- Authors' conclusion: Cartographer is more robust to people than GMapping, which has no explicit outlier removal. (same source)

**Limits (from the paper's own method and future-work text):** only two environments and at most two people; the ground truth is itself a map made by the robot in an empty room, not an external measurement; they name testing "a large range of complexity in terms of the number of people" as future work. SLAM Toolbox was not tested ([arXiv PDF](https://arxiv.org/pdf/2204.08163)).

### Brief entries: [R25], [J16], [MJ21]

- [R25] is a review of 2D lidar SLAM in *Remote Sensing* 17(7), 2025 ([Crossref](https://api.crossref.org/works/10.3390/rs17071214)). Used as the background citation only; I did not read its full text.
- [J16] introduces the range-flow planar odometry method that rf2o implements, ICRA 2016 ([Crossref](https://api.crossref.org/works/10.1109/ICRA.2016.7487647)). Full text not read.
- [MJ21] is the SLAM Toolbox paper, JOSS 6(61), 2021 ([Crossref](https://api.crossref.org/works/10.21105/joss.02783)). Full text not read. K26 describes SLAM Toolbox as graph-based scan matching with loop closure ([PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/)).

### What we can compare against

Our numbers are targets until measured on the robot (AGENTS.md rule 4). Our-side facts about the lidar come from this repo's `AGENTS.md` (A1M8, 7.05 Hz, 26 to 29 % no-echo).

| Our experiment | Paper | Their metric and value | How ours will be measured | Differences that make the comparison imperfect |
| --- | --- | --- | --- | --- |
| E3 repeatability: 5 driven runs, same route, frozen config | [K26] | Pairwise ATE between runs, SLAM Toolbox without AMCL: 0.198 to 0.230 m (Panther, Env A), 0.217 m (Panther, Env C, meas. 2); map IoU for SLAM Toolbox about 0.02 to 0.35 ([PMC13364119](https://pmc.ncbi.nlm.nih.gov/articles/PMC13364119/)) | Same definitions: SE(2)-aligned pairwise ATE over all 10 pairs of 5 runs (`evo` or our own script), occupied-cell IoU after alignment | They: 3D Ouster lidar converted to 2D, about 0.4 to 1.1 m/s, 163 to 287 m routes, offline replay of 12 datasets, 10 stochastic reprocessings each. Us: A1M8 at 7.05 Hz with 26 to 29 % no-echo, 0.15 m/s cap, a room-scale loop, 5 driven runs on a Pi 4. Our route is much shorter, so ATE will scale differently. Our five runs are separately driven, so motion also differs between runs |
| E2 IMU ablation: E1 bags replayed with and without IMU in the EKF, plus one live run each | [M26] | Pre-SLAM translational APE RMSE cut 60 to 75 %; post-SLAM SLAM Toolbox change -2.6 % to +1.6 % translational (Table 3) ([PMC13568328](https://pmc.ncbi.nlm.nih.gov/articles/PMC13568328/)) | APE and heading error with `evo` against tape-measured checkpoints (5 points), before SLAM (EKF output) and after (SLAM pose), 5 replays per condition | They: wheel encoders in both conditions, IMU is the added sensor, ground truth is a full trajectory, ROS 1, 2D lidar at 40 Hz class, large building. Us: no encoders, so the baseline is rf2o alone; ground truth is a handful of taped checkpoints, not a trajectory; MPU6050 is a cheap gyro. Our "before SLAM" gain could be larger or smaller; do not claim replication, claim analogue |
| E4 people in room: 5 runs with 1 to 2 people walking, plus a step-in | [Y21] | Mean ADNN map error versus empty-room map: GMapping 5.9 cm filtered versus 80.24 cm unfiltered with 2 people (corridor); Cartographer 1.36 versus 2.16 cm ([arXiv PDF](https://arxiv.org/pdf/2204.08163)) | Map ADNN (or IoU) against our empty-room map from the same config, plus arrival error versus E1; no people filtering in v1, so we measure the unfiltered case only | They: GMapping and Cartographer, we use SLAM Toolbox; they filter people, we do not (our case matches their "unfiltered" bars); Hokuyo 40 Hz versus A1M8 7 Hz; their reference map is also robot-made; we add delivery and safety metrics they do not have |

---

## Part 2: indoor and last-metre delivery robot products

Short keys: [PUDU], [KEENON], [AETHON], [STARSHIP], [SCOUT], [BEAR]. Speeds and prices are as published by the maker or a named reseller; "not found" means I did not see it in a source I opened.

| Product | Setting | Main sensors | Localisation approach | Speed | Price class | Status | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pudu BellaBot | Restaurants and similar indoor venues (the page offers 10 kg per tray, 40 kg max) | 3 RGBD cameras and a lidar for obstacle avoidance ([PUDU](https://www.pudurobotics.com/products/bellabot)) | "supports both LiDAR and visual SLAM positioning and navigation". Positioning row lists marker positioning (markers up to 8 m high, optional) and code-free laser positioning ([PUDU](https://www.pudurobotics.com/products/bellabot)) | 0.5 to 1.2 m/s adjustable | Not found: page says "Request a Demo" | On sale (page live at access date) | [PUDU](https://www.pudurobotics.com/products/bellabot) |
| Keenon DINERBOT T10 | Hotels and restaurants; Keenon cites Wyndham, Dongcheng, Jinjiang hotel partnerships ([KEENON-PR](https://www.automatedwarehouseonline.com/keenon-robotics-introduces-dinerbot-t10/)) | Four stereo cameras (270 degree 3D detection) and two lidars (360 degree 2D) per the 2023 launch release ([KEENON-PR](https://www.automatedwarehouseonline.com/keenon-robotics-introduces-dinerbot-t10/)); Keenon's page says "four stereo vision sensors and LiDAR" ([KEENON](https://www.keenon.com/en/news/k2)) | "self-developed and fully autonomous position and navigation system" ([KEENON-PR](https://www.automatedwarehouseonline.com/keenon-robotics-introduces-dinerbot-t10/)). No further detail found | Not found for T10 (a reseller shows "Contact for details"; ~1.0 m/s appears only on the T8 page, a different model) | Reseller prices conflict: $13,000 ([RobotLAB](https://www.robotlab.com/store/keenon-t10/)), $19,600 ([Knox Labs](https://www.knoxlabs.com/products/keenon-dinerbot-t10-delivery-promotions-robot)), $9,000 (The Robot Warehouse, listed in search results only). Use "about $9k to $20k, reseller-dependent" | Launched 2023; page live at access date | [KEENON-PR](https://www.automatedwarehouseonline.com/keenon-robotics-introduces-dinerbot-t10/), [KEENON](https://www.keenon.com/en/news/k2) |
| Aethon TUG (now sold as T3 cart robot) | Hospitals and other facilities, hauling carts | Not found (Aethon's pages say it "dynamically navigates and safely works around people" without naming sensors) ([AETHON-ST](https://aethon.com/st-engineering-acquires-aethon-market-leading-autonomous-mobile-robot-technology/)) | Not found; patents say it uses an onboard hospital map and navigation software ([USPTO US 7,894,939](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7894939), read only as a search snippet) | Not found from a current maker page | Not found | Acquired by ST Engineering, announced 2017-07-17 ([AETHON-ST](https://aethon.com/st-engineering-acquires-aethon-market-leading-autonomous-mobile-robot-technology/)); Aethon's current site lists T3 and no longer names TUG in the pages I read ([Aethon](https://aethon.com/mobile-robots-for-healthcare/)). Payload: TUG "up to 1,400 lbs" | [AETHON-ST](https://aethon.com/st-engineering-acquires-aethon-market-leading-autonomous-mobile-robot-technology/) |
| Starship | Outdoor sidewalk and campus delivery; included as the contrast case | "a combination of radars, cameras, sensors and machine learning" ([STARSHIP](https://www.starship.xyz/)). Wikipedia lists ten stereo and time-of-flight cameras, GPS, ultrasonic, radar, IMU ([Wikipedia](https://en.wikipedia.org/wiki/Starship_Technologies)); counts vary by source, so treat as to check | Not described on Starship's page; Wikipedia says "feature detection of edges and mapping techniques" for terrain and lists GPS | Max 6 km/h (3.7 mph) per Wikipedia ([Wikipedia](https://en.wikipedia.org/wiki/Starship_Technologies)) | Not found per delivery; 2018 robot cost US$5,500 claimed, target $2,250 (Wikipedia, same page) | Operating: "10 million+" deliveries, "99% autonomous and operate at Level 4" ([STARSHIP](https://www.starship.xyz/)) | [STARSHIP](https://www.starship.xyz/) |
| Amazon Scout | Sidewalk home delivery (not indoor) | Not found | Not found | Not found | Not applicable | Ended. Amazon spokesperson: "we are ending our field tests and reorienting the program"; reason given: aspects "weren't meeting customers' needs"; reported the week of 2022-10-07; tested in Washington state, Georgia, Tennessee, Southern California ([FreightWaves](https://www.freightwaves.com/news/amazon-scraps-scout-home-delivery-robot)) | [SCOUT](https://www.freightwaves.com/news/amazon-scraps-scout-home-delivery-robot) |
| Bear Robotics Servi (optional) | Restaurants, hotels, senior living, hospital dining | "LiDAR + camera sensors" ([RobotLAB](https://www.robotlab.com/store/servi-delivery-robot/)) | Mapping and a home dock; installation under an hour in about 1,000 sq ft (same page) | 0.1 to 1.2 m/s | $9,990 on the product page, $11,990 in its FAQ ([RobotLAB](https://www.robotlab.com/store/servi-delivery-robot/)) | On sale via reseller | [BEAR](https://www.robotlab.com/store/servi-delivery-robot/) |

Notes for the report:

- The Scout shutdown is confirmed (Oct 2022), but the "paused" wording in the brief is too weak: the spokesperson said the field tests were ending ([FreightWaves](https://www.freightwaves.com/news/amazon-scraps-scout-home-delivery-robot)).
- The Pudu page I opened has no ceiling-marker claim; the marker option is "Marker Positioning", up to 8 m high ([PUDU](https://www.pudurobotics.com/products/bellabot)). Do not write "ceiling markers" unless a source says so.
- Two Pudu sources disagree on BellaBot navigation: an older Pudu academy page lists visual SLAM with markers and 0.1 to 1.2 m/s for the base model, as relayed by a search summary; I did not open it. Use the current product page.
- Our robot for the comparison row: lidar SLAM with an IMU, 0.15 m/s cap, no encoders, no cameras in the loop (repo: `AGENTS.md`).

---

## Part 3: AV context sources

### Waymo ([WAYMO])

- 6th-generation Waymo Driver: "13 cameras, 4 lidar, 6 radar" plus external audio receivers; coverage "up to 500 meters"; Waymo says "Redundancies are essential" and describes "three complementary sensing modalities" ([Waymo blog, 2024-08](https://waymo.com/blog/2024/08/meet-the-6th-generation-waymo-driver/)).
- Earlier Jaguar I-PACE fleet: 29 cameras, lidar all around the vehicle, radar "effective in rain, fog, and snow" ([Waymo Driver page](https://waymo.com/waymo-driver/)).
- Safety hub: claims versus an average human driver over the same distance in its cities, for example 95 % fewer serious-injury-or-worse crashes and 82 % fewer injury-causing crashes, over "100 million miles". The page does not state the period behind the percentages, so cite as Waymo's claim and check the linked dashboard before using the numbers ([Waymo safety](https://www.waymo.com/safety/)).
- Safety methodology: a Safety Framework (2020 post) and a Safety Case approach (2023 post "A blueprint for AV safety"), both named on the same page ([Waymo safety](https://www.waymo.com/safety/)).

### Tesla ([TESLA])

- May 2021: North American Model 3 and Model Y "will no longer be equipped with radar", described as the first to "rely on camera vision and neural net processing" for Autopilot; Model S/X and non-North American cars kept radar at that point ([The Drive, updated 2021-05-26](https://www.thedrive.com/news/40794/tesla-removes-radar-sensors-from-model-3-and-model-y-so-autopilot-will-use-cameras-only)).
- October 2022: Tesla began removing ultrasonic sensors, replacing their input with the camera-based occupancy network; Park Assist, Autopark, Summon and Smart Summon were limited or inactive until performance matched ([InsideEVs, 2022-10-06](https://insideevs.com/news/614707/tesla-removing-ultrasonic-sensors-vision-only/)).
- I could not open tesla.com directly (HTTP 403), so both facts are second-hand. Check the current state of Tesla's sensor suite before slides.

### Standards (one line each)

- **ISO 21448 (SOTIF), 2022:** guidance on avoiding unreasonable risk from functional insufficiencies (for example sensor or algorithm limits) in road-vehicle E/E functions that depend on situational awareness, including driving automation levels 1 to 5, across design, verification and operation; it excludes faults handled by ISO 26262 and cybersecurity ([EVS listing, valid from 2022-06-30](https://www.evs.ee/et/iso-21448-2022); scope detail from a search summary of the ISO abstract, [ISO page](https://www.iso.org/standard/77490.html), which I could not open directly).
- **ISO 13482:2014:** safety requirements for personal care robots: mobile servant robots, physical assistant robots and person carrier robots; excludes robots above 20 km/h, toys, water-borne and flying robots, industrial robots (ISO 10218), medical devices and military robots; published 2014-02-03 ([Genorma](https://genorma.com/en/standards/iso-13482-2014)). Status is disputed: Genorma shows "to be revised" since 2021 with ISO/FDIS 13482 in development, while one search result says ISO confirmed it in 2020; check [ISO](https://www.iso.org/standard/53820.html). Whether a commercial restaurant-delivery robot counts as a "mobile servant robot" is a judgement; I did not find a source that says so. Treat as to check.

---

## Open items (to check before the report is final)

1. Read the IEEE version of [Y21] to confirm the Cartographer corridor numbers and obtain the unfiltered meeting-room values.
2. Confirm whether the student NTULearn template needs a different citation style (IEEE or other); keys here are placeholders.
3. Aethon TUG sensors and speed from a current maker datasheet (not found).
4. Keenon T10 speed from Keenon's own spec sheet (not found).
5. Waymo safety numbers: period and mileage behind the percentages, from the dashboard.
6. Tesla: current sensor suite from tesla.com or a regulatory filing.

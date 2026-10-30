# Test log

One row per test run. Commit is the short hash of the code under test. Numbers, not
adjectives; a fail with a number is more useful than a pass with none.

| Date | Commit | Phase | Test | Result | Numbers | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-22 | | 0 | `colcon build` on the Pi | | | |
| 2026-10-22 | | 1 | `ros2 topic hz /scan` | | | |
| 2026-10-22 | | 1 | `scan_stats` (2 min, still) | | | |
| 2026-10-22 | | 2 | `ros2 topic hz /imu/data` | | | |
| 2026-10-22 | | 2 | `tf2_echo odom base_footprint` | | | |
| 2026-10-22 | | 2 | teleop dry run → `/motor/duty` | | | |
| | 3 | dead zone/gain per side | | | |
| | 3 | 1 m straight (10 cm, 10°) | | | |
| | 3 | gyro 5 spins (5°) | | | |
| | 4 | 1 m square (10 cm) | | | |
| | 4 | 3 spins heading (5°) | | | |
| | 5 | room map saved | | | |
| | 6 | 5 goals (15 cm, no contact) | | | |
| | 7 | home → seat → home ×5 | | | |
| 2026-10-30 | 44f11a3 | 3 | 3.4 startup race, `bash tools/startup_race.sh 10 2.0` | pass | 10/10 launches, no transform error; rf2o ran with URDF tf | rf2o delayed 2 s after robot_state_publisher; lidar first scan arrives ~13 s after launch |
| 2026-10-30 | 44f11a3 | 3 | 3.4 control, `bash tools/startup_race.sh 3 0.0` | no repro | 0/3 errors | delay 0 does not reproduce the race here: rsp is up long before the first scan, so the guard is cheap insurance, not shown necessary |
| 2026-10-30 | d8f46bf | 4 | 4.3 relay on bag replay (still2), `ros2 topic echo /odom_rf2o_cov --once --field twist.covariance` | pass | idx0 1e-3, idx35 4e-3, other diagonals 1e3, input stays all zero; 7.06 Hz out = rf2o rate | variances are CALIBRATE placeholders (4.4); EKF diagnostics not yet checked |
| 2026-10-30 | 25403ba | 5 | 5.3 `ros2 launch delivery_bot_bringup mapping.launch.py include_base:=false use_sim_time:=true` + `ros2 bag play bags/still2_2026-10-30 --clock --topics /scan` | pass | `ros2 lifecycle get /slam_toolbox` = active [3] with no manual steps; `/map` 102x65 cells at 0.05 m | replay only; tf was scaffolding (URDF rsp + fixed odom->base_footprint), robot at rest; base.launch.py still a stub so the live half is untested |

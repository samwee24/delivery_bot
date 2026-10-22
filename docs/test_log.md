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

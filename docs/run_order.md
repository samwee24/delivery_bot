# Driven session run order (2026-11-10)

## 1. Before power-up

- Pi on a proper 5.1 V 3 A supply (not a power bank, not the motor pack), OI-11.
- Motor battery charged, voltage measured and written down; a spare if there is one.
- Wiring and common ground reseated.
- Floor marks (home, 1 m line) taped.

## 2. On the Pi

1. `cd ~/ros2_ws/src/delivery_bot && git pull`.
2. `vcgencmd get_throttled` → `0x0`.
   Start `ros2 launch delivery_bot_bringup navigation.launch.py bridge:=false` and watch `vcgencmd get_throttled` for 60 s: any 0x1 or 0x4 bit means stop and swap the supply. Until then only CP5 straights on `base.launch.py`.
3. `python3 tools/motor_check.py run 0.30 2` → about 0.9 m. Silent means stop and fix the power first.

## 3. Every block

Repeat the motor check after any battery swap or if a run is silent. If a run goes silent, mark it `invalid` in `docs/test_log.md`, never `fail`.

## 4. Stack rules

- Start in tmux in the foreground; stop with Ctrl-C and wait 20 s before the next start.
- Drive live only with `-- dry_run:=false` on the command line.
- Keep Foxglove off unless needed (`run_cell.py` default); camera off.
- After start, `ros2 param get /lifecycle_manager_navigation bond_timeout` → 10.0.

## 5. Order (most valuable first; stop where time or battery runs out)

1. CP5: two more 1 m straights on `base.launch.py` with `python3 tools/timed_move.py straight --speed 0.15 --topic cmd_vel` (bar 0.90-1.10 m, ≤ 10 cm sideways by tape).
2. One straight under `navigation.launch.py` (`timed_move` default topic), to confirm Nav2 stays up.
3. Nav2 goal to (1, 0) and back from the home mark.
4. E2 `rf2o_imu_empty`: straight ×3, spin ×3.
5. E2 `rf2o_imu_people`: straight ×3, spin ×3.
6. E3 `slam_empty` ×3, `amcl_empty` ×3.
7. E3 `slam_people`, `amcl_people`.
8. E4 step-ins ×3.
9. E1 demo ×5.
10. Remaining E2 configs (`rf2o_only`, `imu_only`, `none`) and E3 wrong starts.

## 6. Per run

- Start with `python3 tools/run_cell.py <exp> <cell> <run> -- dry_run:=false`; drive with `tools/timed_move.py` in a second shell; tape forward and sideways.
- Paste the printed row into `docs/test_log.md` with the tape numbers.
- `python3 tools/analysis/bag_summary.py ~/bags/<bag>` for the odometry numbers.

## 7. Fallback if driving fails

Push with a stick for E2 (nobody behind the robot except in people runs).

## 8. Analysis on the Mac

Bags are copied from the Pi (`../delivery_bot_pi_backup/bags/`); no ROS needed on the Mac.

- Setup, once: `python3 -m venv .venv && .venv/bin/pip install evo pytest`.
- E2 distance and heading per bag: `.venv/bin/python tools/analysis/bag_summary.py <bag_dir> [<bag_dir> ...]`.
- Export odometry to TUM, in a per-bag output folder: `mkdir out && cd out && ../.venv/bin/evo_traj bag2 <bag_dir> /odom_rf2o /odometry/filtered --save_as_tum` (fails with `no messages for topic` if a topic is not in the bag; then list only the topics it has, e.g. `/odom_rf2o`). Writes one `.tum` per topic (e.g. `odom_rf2o.tum`).
- E3 pairwise APE between two loops: `.venv/bin/evo_ape tum <loop_a>.tum <loop_b>.tum -a`. Smoke-tested on the 2026-10-31 push bag with the same file twice: APE 0.000000.

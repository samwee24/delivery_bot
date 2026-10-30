# CA3 — lab notebook

Newest entry first. One block per session: date, goal, what ran, result, next.
Reference material belongs in `docs/`, raw artefacts in `evidence/`.

---

## 2026-10-30 (evening) · 3.4 startup race, near-return ring is the room

**Ran.** `tools/startup_race.sh 10 2.0` on the Pi: 10/10 clean (rf2o_alone.launch.py,
rf2o delayed 2 s). Delay 0, 3 launches: also clean; first scan arrives ~13 s after
launch, so the race needs a slow URDF. Keep the delay in `base.launch.py` anyway
(request to the bringup owner).
**Near-return ring (OI-4).** Fraction of returns <0.30 m per 30 deg bin
(`/tmp/near.py` over `still_`, `still2_`, `rot90_` bags): the bins move between bags
(0..60 deg, then 30..120, then 90..180), so it follows the scene, not the lidar. No
`mask_deg` needed on this evidence; recheck once mounted on the robot.
`/dev/rplidar` symlink now exists on the Pi.

---

## 2026-10-30 (later) · 1.4 box test: on +x, coarse only

**Ran.** `bash /tmp/box_check.sh` on the Pi, then ranges within +-40 deg of the same
`/scan`. Box arc spans -13..+30 deg at 0.23-0.25 m (centre ~+9 deg, ~43 deg wide).

**Result.** Box is on +x, not +-90 or 180: the convention check passes, `laser_yaw = 0`
holds coarsely (+-10 deg). Not the spec test: box was at 0.23 m not 0.50 m and off-centre,
so the 0 +- 2 deg tolerance in `docs/slam.md` is **not** shown. Still *brief default*,
not *measured*. Returns at 0.18-0.25 m around the other directions persist (the OI-4 ring).

**Next.** Re-verify the +-2 deg after the URDF is live: box centred at 0.50 m, view in
`base_link`.

---

## 2026-10-30 · SLAM build path: stage 1 done, 1.4 redo not yet clean

**Goal.** Redo the 50 cm box test (1.4) cleanly; push on to stage 3.

**Ran.** `bash /tmp/box_check.sh` on the Pi (one `/scan`, nearest returns and close
returns per 30 deg bin). Scene still cluttered: nearest returns at 85-90 deg, 0.18 m
(something on the lidar's left side, probably the desk or the robot itself); nothing
at 0.50 m near 0 deg (min 0.318 m in -30..30). Not a valid box test.

**Result.** `laser_yaw = 0` stays *provisional* (brief default, not measured).
Earlier findings (rf2o still baseline: x -2.4 mm, y -0.6 mm, yaw +0.26 deg over ~28 s,
`bags/still2_2026-10-30`) are in the session record.

**Next.** Clear 1 m around the lidar, one box at 0.50 m on +x, rerun `box_check.sh`.
Stage 3 hardware tests (3.2, 3.3) and 2.1 need the robot built.

---

## 2026-10-23 · documentation moved into the repository; repo made private

**Goal.** Stop the plan, notes and evidence from existing only on one MacBook.

**Decided.** One repository, three copies (Mac, GitHub, Pi), GitHub as source of truth.
`delivery_bot` becomes **private** — the notebook, report draft and assessment
reasoning are not for publication. CA1/CA2 stay out of this repo.

**What moved** (from the local-only `MA4890/CA3/`, 172 KB):

| Was | Now |
| --- | --- |
| `CA3/README.md` | `docs/CA3.md` |
| `CA3/CA3_plan.md` | `docs/design-plan.md` |
| `CA3/docs/01…07` | `docs/system/01…07` |
| `CA3/notes.md` | `notes/notes.md` |
| `CA3/AGENTS.md` | `AGENTS.md` (repo root), with sync rules added |
| `CA3/evidence/lidar/` | `evidence/lidar/` |
| `CA3/report/` | `report/` |
| `CA3/scripts/` | `tools/` |

`config/` and `results/` were empty placeholders — the real configs already live in
the package `config/` directories, so only `results/.gitkeep` was kept.

**Also committed.** The six untracked pipeline diagrams (`docs/img/`, `docs/*.mmd`,
`docs/pipeline*.html`) that had been sitting on the Mac since 2026-10-22.

**Verification.** Relative links checked across every `.md` (0 dangling);
`gh api` unauthenticated → 404, so the repo is genuinely private; backup tarball at
`~/Desktop/CA3-backup-20261023.tar.gz` before any move.

**Consequence.** `docs/pi_setup.md` (from-scratch install) and
`docs/system/02_pi_setup.md` (measured state) both survive, each now pointing at the
other. The Pi pulls; it does not author prose.

**Next.** Delete the local `MA4890/CA3` once the repo copy is confirmed, so there is
no second copy to diverge. Then the OI-4 echo-rate control run.

---

## 2026-10-22 · D5 — standard ROS 2 stack adopted; own-maths v1 retired

**Goal.** Decide the estimation / mapping / navigation stack before P1 bring-up work.

**Decided.** The brief permits packages, so v1 moves from D4's own numpy stack to the
standard lidar-only robot stack, recorded as D5 in the README:

| Job | Package (Jazzy) |
| --- | --- |
| Lidar driver | `rplidar_ros` |
| Lidar odometry (in place of encoders) | `rf2o_laser_odometry` (source, `ros2` branch) |
| Odometry + gyro fusion | `robot_localization` EKF, `two_d_mode: true` |
| Mapping + localization | `slam_toolbox` |
| Planning, control, obstacle stop | Nav2 (RPP controller, Collision Monitor) |
| Keyboard driving | `teleop_twist_keyboard` |
| Viewing / logging | `foxglove_bridge`, `rosbag2` MCAP (D2/D3 unchanged) |

**Dropped.** `kiss-icp`. It is 3D point-to-point ICP tuned for dense spinning-lidar
clouds; on a sparse planar A1 scan at 5–7 Hz it solves a problem shaped nothing like
ours, and cost a source compile plus a 2 GB swapfile for the privilege. `rf2o` is
planar by construction. The own EKF / A\* / pure pursuit stay documented as the
fallback of record if a package underperforms.

**What we still write.** Motor node (L298N PWM on `lgpio`, gyro turn-rate loop,
watchdog), IMU node (MPU6050 → `sensor_msgs/Imu`, bias calibration, gyro-z only),
URDF (`base_link → laser` / `imu_link`), delivery script (Nav2 Simple Commander).
Safety rules unchanged: motor-node watchdog, Collision Monitor between controller and
motors, `v_max` 0.15 m/s.

**Corrections to the plan as received.**

| Claim | Correction |
| --- | --- |
| Foxglove at `ws://100.73.7.24:8765` | that is the **offline** box (OI-1); use `ws://100.83.14.99:8765` |
| "the C++ driver may recover the missing points" | loss is photonic (67 % of pings return distance 0, clean serial); a driver change moves no photons — the 50 cm white-box test is still the gate |
| install clock workaround (`htpdate`) / Ghostty fix | unverified claims, not needed for bring-up; check only if a symptom appears |
| bag list `/scan /imu/data /cmd_vel /tf` | add `/odom` and `/odometry/filtered` for the replay tests |

**Next.** The echo-rate verdict on `sherm-raspi` (OI-4) still gates everything: apt
install the stack, URDF + both nodes, keyboard drive, bag, rf2o+EKF tuning, map, Nav2.

**Risk.** `rf2o` is a single-file Humble-era port; expect to patch the `ros2` branch
on Jazzy. Fallback if it stalls: EKF on gyro + `slam_toolbox` pose deltas.

---

## 2026-10-22 · P0 install: ROS stack on sherm-raspi, tmux base, Ghostty terminfo

**Goal.** Put the D5 stack on the box and make SSH sessions survive drops.

**What ran (user-driven, in a `tmux` session `ca3`).**

| Step | Outcome |
| --- | --- |
| `infocmp -x xterm-ghostty \| ssh ... 'tic -x -'` from the Mac | ✅ Pi now reads `~/.terminfo/x/xterm-ghostty`; `tic` alias warning is harmless |
| first `tmux` attempts | ❌ `missing or unsuitable terminal` → server never started → `no server running on /tmp/tmux-1000/default`; fixed by the terminfo import, recorded in [docs/06_troubleshooting.md](../docs/system/06_troubleshooting.md) |
| `tmux new -s ca3` with windows `driver` / `monitor` / `view` / `shell` | ✅ persistent workspace |
| `sudo apt update` | ✅ all three sources fetched (ROS, Ubuntu ports, Tailscale) |
| `sudo apt install ros-jazzy-{rplidar-ros,slam-toolbox,robot-localization,navigation2,nav2-bringup,teleop-twist-keyboard,robot-state-publisher}` | ✅ first attempt never ran (mangled multi-line paste); retried as one line |
| `ros2 pkg prefix` loop over the six packages | ✅ all `/opt/ros/jazzy` |

**Notes.** `id` still shows no `dialout` after the 01:24 reboot — the earlier `usermod`
had not taken; re-run `sudo usermod -aG dialout robot` and use a fresh login before
the IMU step (the lidar works via `MODE="0666"`). Pip and venv apt packages are now
installed (`python3-pip-wheels`, `python3.12-venv` in the transcript).

**Next.** `rf2o_laser_odometry` from source into `~/ros2_ws`, then the venv.

---

## 2026-10-22 · Repo reduced to a rebuild skeleton (friend builds it slowly)

**Decision.** The working implementation stays as the tag `reference-v1`; `main`
becomes a skeleton so someone can learn the ROS 2 stack by writing it.

**What was blanked — 10 files, 1,530 → 342 lines.** `motor_node.py`,
`imu_node.py`, `deliver.py`, `save_goal.py`, `scan_stats.py`, the four launch
files, and the URDF body. Each is now its docstring (the contract: watchdog
rules, `publish_tf: false`, `orientation_covariance[0] = -1`, the frame tree)
plus signatures that `raise NotImplementedError`. Launch files return an empty
`LaunchDescription`; the xacro keeps a valid `<robot>` root so `xacro` still
exits 0 and CI keeps a real check to grow into.

**What was deliberately kept.** `README.md` (plus a banner explaining the
skeleton), repo `docs/`, this folder, all YAML — `ekf.yaml`,
`slam_mapping/localization`, `nav2_params` (369 lines), `drivers.yaml`,
`goals.yaml` — and the packaging: `package.xml`, `CMakeLists.txt`, `setup.py`,
`setup.cfg`, `resource/`, `deps.repos`, `.github/workflows/ci.yml`. Deleting the
YAML would turn "rebuild this robot" into "invent a Nav2 configuration", which is
a different task.

**Verification on `sherm-raspi` after `git pull` (commit `a407464`):**

```text
colcon build --symlink-install --executor sequential
  Summary: 5 packages finished [20.4s]
xacro …/delivery_bot.urdf.xacro        -> exit 0, <robot name="delivery_bot">
ros2 launch delivery_bot_bringup base.launch.py  -> clean start, zero nodes
ros2 run delivery_bot_drivers motor_node         -> NotImplementedError, exit 1
```

So the scaffold builds and launches; nothing pretends to work. That last line is
the honest signature of this commit: **green build, no behaviour.**

**Consequence for these docs.** `docs/07_ros_stack.md` and the P-status in
`README.md` describe `reference-v1`, not the current tree. Read them as the
target specification. "Builds" no longer implies "runs".

---

## 2026-10-22 · rf2o built and verified; stack on the Pi documented as it really is

**Goal.** Finish P0 and build `rf2o_laser_odometry` from source.

**Blocker first.** The Pi had fallen off SSH (`Connection timed out during banner
exchange`) — logged as the incident entry below. After the power-cycle: `up 0 min`,
`dialout` now active for `robot`, 3.2 GiB free.

**Swap, before anything else.**

```
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo "/swapfile none swap sw 0 0" >> /etc/fstab      # persisted
```

`free -h` → `Swap: 2.0Gi`. `/etc/fstab` line verified.

**Apt stack confirmed present:** `build-essential 12.10ubuntu1`, `cmake 3.28.3`,
`git 2.43.0`, `python3-pip 24.0`, `python3-venv 3.12.3`. `i2c-tools` still absent.
The D5 ROS packages were already installed: `rplidar_ros 2.1.0`, `slam_toolbox 2.8.5`,
`nav2_bringup 1.3.13`, `robot_localization 3.8.3`, `xacro 2.1.1`, `tf2_ros`.

**A stale SSH host key cost a detour.** `192.168.31.109` had two entries in
`known_hosts`; the older one (from a different device that held that IP) was being
matched, giving `Host key verification failed`. The live key matched the
`sherm-raspi.local` entry, so the stale line was removed with
`ssh-keygen -R 192.168.31.109`.

**Build.**

```
cd ~/ros2_ws && source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --executor sequential --parallel-workers 1
```

Output: `delivery_bot_description` 1.3 s, `drivers` 8.6 s, `mission` 7.7 s,
**`rf2o_laser_odometry` 3 min 17 s**, `bringup` 7.4 s — *5 packages finished in 3 min 43 s*.
Verified: `ros2 pkg prefix rf2o_laser_odometry` →
`/home/robot/ros2_ws/install/rf2o_laser_odometry`, executable `rf2o_laser_odometry_node` present.

**What was already there.** `~/ros2_ws/src/delivery_bot` is a git repo
(`9e2fd2e Initial delivery_bot stack: drivers, bringup, mission, docs`) with
`bringup` (launch: base/lidar/mapping/navigation, config: ekf, slam_mapping,
slam_localization, nav2_params), `description` (URDF/xacro), `drivers`
(`imu_node`, `motor_node`), `mission`. `rf2o` is cloned alongside, outside the repo,
branch `ros2`, HEAD `b38c68e`.

**Already handled correctly in the launch file** — worth noting because it was the
risk flagged before the build: `base.launch.py` runs rf2o with `publish_tf: False`,
`odom_topic: /odom_rf2o`, and lets `ekf_filter_node` own `odom → base_footprint`.
`motor_node` is overridden to `dry_run: true` by the launch file.

**GPIO question settled.** `motor_node` uses `gpiozero` with `LGPIOFactory`;
`lgpio` is at `/usr/lib/python3/dist-packages/lgpio.py` (`python3-lgpio`), and
`RPi.GPIO` is absent — so the plan's `python3-lgpio` route works, just through
gpiozero rather than a bare import.

**Docs updated to match reality.** `README.md` gained D5 (rf2o + robot_localization
replace KISS-ICP + our own EKF) and D6 (code lives in `~/ros2_ws/src/delivery_bot`;
this folder is documentation and evidence). `docs/07_ros_stack.md` was rewritten from
intention to inventory: real nodes, topics, `tf` ownership, gotchas. `docs/04`'s
pipeline table now names the nodes that exist, and records that **the safety node
does not exist yet** — `motor_node` takes `/cmd_vel` directly, protected only by the
watchdog.

**Next.** `/dev/rplidar` symlink, `i2c-tools`, then the echo-rate probe on this box.

---

## 2026-10-22 · INCIDENT: sherm-raspi stops answering SSH at the banner (unresolved)

**Symptom.** `ssh robot@sherm-raspi.local` hangs and dies with
`Connection timed out during banner exchange` / `Connection to <ip> port 22 timed out`.

**What still works.** `ping` replies (lossless, but RTT jumped from ~7 ms to ~74–140 ms),
and `nc -z 192.168.31.109 22` reports **`tcp/ssh succeeded`** — so the network path,
the listener and the kernel are all alive. Also checked: LAN IPv4, `.local` (IPv6
link-local), and Tailscale `100.83.14.99` (which now times out at connect). Port 8765
(Foxglove bridge) is closed.

**Interpretation.** A TCP handshake completes but sshd never sends its version string.
That is not DNS or firewall — it is the sshd child being unable to run: the classic
cause on this box is **memory exhaustion**. The image has **no swap** (`Swap: 0B`),
4 GB RAM, and a `colcon build` (rf2o, and previously a `kiss-icp` pip compile) runs
4 parallel jobs on 4 cores. Under that load the OOM killer takes sshd children before
they can write the banner.

**Not yet tried:** physical power-cycle, and a longer wait.

**Fix before retrying any build:**

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
colcon build --symlink-install --executor sequential --parallel-workers 1
```

**Lesson.** "No swap" was recorded in [docs/02_pi_setup.md](../docs/system/02_pi_setup.md) as a
footnote for `kiss-icp`; it is a hard prerequisite for *any* build on this Pi, and it
can take the whole machine off the network rather than failing with an OOM message
you can read.

---

## 2026-10-22 · P0 on sherm-raspi — serial access half done

**Goal.** First real P0 steps: `dialout` membership and the `/dev/rplidar` udev alias.

**What ran.**

```
sudo usermod -aG dialout robot
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"' \
  | sudo tee /etc/udev/rules.d/99-rplidar.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/rplidar /dev/ttyUSB0; i2cdetect -y 1
```

**Result.**

| Step | Outcome |
| --- | --- |
| `usermod -aG dialout robot` | ✅ command succeeded — **not yet in effect** (`id` in the same session still showed the old groups; needs a fresh login) |
| udev rule written to `/etc/udev/rules.d/99-rplidar.rules` | ✅ |
| `udevadm control --reload-rules && udevadm trigger` | ✅ ran clean |
| `/dev/rplidar` exists | ❌ **still absent** — the rule did not materialise the symlink on a plain trigger |
| `i2cdetect -y 1` | ❌ `Command 'i2cdetect' not found` — `i2c-tools` is not installed |

**Reading.** `/dev/ttyUSB0` is still `root:dialout 0660`, so nothing is readable by
`robot` yet. Two likely causes for the missing symlink: the trigger did not emit an
`add` event for an already-attached device, or the rule needs the device to
re-enumerate. Next attempt: `sudo udevadm trigger -c add -s tty`, else unplug and
replug the CP210x adapter. The `MODE="0666"` in the rule means group membership stops
being the blocker once the symlink lands.

**Also missing:** `python3-pip`, `python3-venv`, `i2c-tools` — apt install next, plus
a 2 GB swapfile before any `kiss-icp` compile.

**Added this session.** `AGENTS.md` at the top of `CA3/` — the short "how to work
here" file: target machine, stack decisions, rules, current state, next actions in
order. Anything that changes goes in this notebook, not into `AGENTS.md`.

---

## 2026-10-22 · CA3 folder scaffolded, stack direction fixed

**Goal.** Give the project a home in `CA3/` and settle which machine and stack we build on.

**Decided.** Target is `robot@sherm-raspi` (Ubuntu 24.04.5, Pi 4B). ROS 2 Jazzy is
in scope; Foxglove replaces the plan's ZeroMQ telemetry and `tools/viewer.py`; the
pure-Python EKF / A\* / pure-pursuit / occupancy-grid maths stays ours, wrapped in
ROS nodes. `CA3_plan.md` §0 "no ROS" is superseded — recorded as D2 in the README.

**Done.** Created `README.md`, this notebook, `docs/01–07`, `scripts/`, `config/`,
`evidence/{lidar,imu,motors}`, `results/`, `report/`. Renamed
`Room Delivery Robot — Implementation Plan.md` → `CA3_plan.md` (spaces and an em
dash in a filename bite you in git and on the Pi).

**Next.** P0 on `sherm-raspi`: `python3-pip` + `python3-venv`, `dialout`, udev rule,
venv, then re-run the lidar probe on *this* box to answer OI-4.

---

## 2026-10-22 · Machine discovery: the brief's Pi is gone, sherm-raspi is the box

**Goal.** Get back to the lidar work; `ssh robot@100.73.7.24` had started timing out.

**What ran.** `tailscale status`, `ssh -v` banners, `ping` probes against every
candidate host.

**Result.** `robot` @ `100.73.7.24` — **offline, last seen 1 d**. That box held all
P0/P1 work from CA3's brief: `~/botenv` venv, `~/delivery-bot`, the udev rule,
`/dev/rplidar`. Two candidates instead:

| Host | Address | Banner | Outcome |
| --- | --- | --- | --- |
| `raspberrypi` | 100.98.163.85 | OpenSSH 10.0p2 Debian-13 | up, but `robot` key rejected |
| `sherm-raspi` | 100.83.14.99 / 192.168.31.109 | OpenSSH 9.6p1 Ubuntu | up; credentials `robot` / `robot` work |

`sherm-raspi` inventoried in [docs/02_pi_setup.md](../docs/system/02_pi_setup.md): Pi 4B
Rev 1.4, 4 GB, 32 GB card 13 % used, 40.4 °C, **no swap**, ROS 2 Jazzy (205
packages: `ros-base`, `ros-dev-tools`, `foxglove-bridge`, `rosbag2` with MCAP),
empty `~/ros2_ws/src`, CP210x lidar on `1-1.1` → `/dev/ttyUSB0`, `i2c-1` present.

**Blockers found.** `robot` is not in `dialout`, no udev rule, no venv, `pip` is
not installed (`/usr/bin/python3: No module named pip`), no `rplidar` module,
`vcgencmd` cannot open `/dev/vcio` (cosmetic — the tool is not on Ubuntu's default path).

**Access fixed.** Password login works; the Mac's ed25519 key is now in
`~robot/.ssh/authorized_keys`, so key auth works without a password.

**Lesson.** The bare hostname `sherm-raspi` does not resolve on the Mac — mDNS
needs `sherm-raspi.local`, otherwise `ssh: Could not resolve hostname`. Worth an
SSH alias later.

---

## 2026-10-20/21 · P1 lidar bring-up on the old Pi — works, but only 33 % of pings return

**Goal.** Follow CA3 brief P1: identify the lidar, confirm the Pi sees it, run
`test_lidar.py`, read the scan.

**Machine.** `robot` @ `100.73.7.24` (Debian 13, Raspberry Pi OS Lite 64-bit) — **now offline (OI-1)**.
This is the only session run on it; all of it is evidence for how the unit behaves.

**What ran.**

```
lsusb; ls -l /dev/ttyUSB*; groups; vcgencmd get_throttled      # brief step 2
udevadm rules check; ls -l /dev/rplidar                        # brief step 3
python -c "from rplidar import RPLidar; ..."                    # get_info / get_health
python ~/delivery-bot/scripts/test_lidar.py                    # brief step 4
scripts/probe_echo_rate.py                                      # our own diagnostic
```

**Result — hardware answers.**

| Item | Value | Verdict |
| --- | --- | --- |
| USB | `10c4:ea60` Silicon Labs CP210x, bus 001 device 003 | ✅ expected |
| Device | `/dev/ttyUSB0`, `/dev/rplidar -> ttyUSB0` (udev rule present) | ✅ |
| Groups | `robot … dialout …` | ✅ |
| Power | `throttled=0x0` when the lidar started | ✅ no undervoltage |
| `get_info()` | `model: 24` (= A1M8), fw `(1, 29)`, hw `7`, serial `EEA5ECF0…4110` | ✅ |
| `get_health()` | `('Good', 0)` | ✅ |
| Baud | 115200 (256000 not needed) | ✅ |
| Motor | stops on exit (`stop()` / `stop_motor()` / `disconnect()` in `finally`) | ✅ |

**Result — scan behaviour (the problem).**

| Quantity | Measured | Expected |
| --- | --- | --- |
| Rotation rate | 4.9–6.9 Hz | 5–10 Hz ✅ |
| Raw measurement packets / rev | 284 | ~360–400 ⚠️ |
| Returns with a distance | **95–105** | ~350 ❌ |
| **Echo rate** | **33–35 %, stable over 3 runs** | >90 % ❌ |
| Quality of the returns that arrive | median 15, max 15 | strong ✅ |
| Max range seen | 8.5–8.7 m | ~8 m ✅ |

Per 15° sector the echo rate is highly angle-dependent, which is the useful part:

| raw angle | echo % | median dist | Read |
| --- | --- | --- | --- |
| 15–30° | 11 % | **1.31 m** (max 1.32) | flat surface 1.3 m away, returning one ping in nine → **not range, not geometry** |
| 45–75° | 0 % | — | neighbours see 8.46 m → beam escapes through an opening ✅ |
| 120–150° | 66–68 % | 1.8–2.6 m | wall |
| 195–225° | 80–82 % | 0.85 m | best sector in the room |
| 240–255° | 34 % | **0.23 m** | the robot's own mast/cable → candidate `mask_deg` |
| 315–330° | 10 % | 0.56 m | |

**Reading.** Link is clean — angles step smoothly at ~1.27°, no sync errors, no
`Wrong body size` / descriptor exceptions, quality saturates. So the 67 % loss is
photons not coming back, not bytes. No sector exceeds 82 %, so there is a ~20 %
loss floor even on the best wall.

**Script quirk worth remembering.** The brief's `iter_scans(..., min_len=100)`
silently drops every revolution with under 100 valid points — about half of them —
so the printed "scan rate ~0.9 Hz" is an artefact. True rate measured off the
`new_scan` flag is 5–7 Hz. Keep `min_len=5` for diagnostics.

**Next.** Re-run this probe on `sherm-raspi` — different mounting, so it doubles
as a control experiment. If that box's lidar also sits near 35 %, the unit or the
series is the problem; if it jumps to ~90 %, the old mounting was.

**Artefacts.** [evidence/lidar/](../evidence/lidar/) — `2026-10-21_scan_run1.png`,
`2026-10-21_composite_20revs.png`.

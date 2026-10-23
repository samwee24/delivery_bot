# 06 · Troubleshooting

Symptom → cause → fix. Anything we actually hit is marked **hit**, with the exact
text of the error, so it is searchable later.

## Access and networking

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `ssh: Could not resolve hostname sherm-raspi: nodename nor servname provided, or not known` | bare mDNS name | use `sherm-raspi.local`, `192.168.31.109`, or Tailscale `100.83.14.99` |
| **hit** `Permission denied (publickey,password)` | key not in `authorized_keys` | `ssh-copy-id -i ~/.ssh/id_ed25519.pub robot@sherm-raspi.local`, or install the key over one password login |
| **hit** `ssh: connect to host 100.73.7.24 port 22: Operation timed out` | the old bot Pi is offline (`tailscale status`: `offline, last seen 1d`) | power it on; do not debug it as a network problem |
| host key mismatch after a reflash | old key in `known_hosts` | `ssh-keygen -R <host>` |
| password prompt never appears | BatchMode or piped stdin | run from an interactive terminal; `sshpass`/`expect` only for automation |

## Lidar

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `Permission denied` opening `/dev/ttyUSB0` | user not in `dialout`, or udev rule absent | `sudo usermod -aG dialout robot` + re-login; install `99-rplidar.rules` |
| **hit** echo rate only 33–35 %, `distance = 0` for 2/3 of pings | film, dust or damage on the scan window; robot self-occlusion; dark/glass surfaces | white box at 50 cm test: ~95 % → scene, ~35 % → optics. See [03_bringup.md](03_bringup.md) |
| **hit** script prints `Scan rate ~0.9 Hz` while the sensor spins at 5–7 Hz | `iter_scans(min_len=100)` skips revolutions with <100 valid points; the script divides by wall time | use `min_len=5` for diagnostics, or time between `new_scan` flags |
| `Wrong body size`, `Descriptor length mismatch`, `Incorrect descriptor starting bytes` | stale bytes in the buffer | re-run; if it repeats, unplug and replug the lidar |
| hangs or times out on `get_info()` | baud does not match the model | A1/A2M8 = 115200; A2M12/A3/S1/S2 = 256000 |
| spins but very few points | dirty lens, or something right next to it | clean the window; check `min_range_m` |
| Pi reboots, or `vcgencmd get_throttled` ≠ `0x0` when the motor starts | power bank or USB-C cable too weak | report it; do not work around it |
| `vcgencmd: Can't open device file: /dev/vcio` | **hit** on Ubuntu — `vcgencmd` is not the default path/tool | install `raspi-utils`, or read `/sys/class/thermal/thermal_zone0/temp` (idle was 40.4 °C) |

## Python / environment

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `/usr/bin/python3: No module named pip` | `python3-pip` not installed on this image | `sudo apt install python3-pip python3-venv` |
| `ModuleNotFoundError: No module named 'rplidar'` | wrong interpreter — plain `python3` instead of the venv, or ROS sourced over it | activate `~/botenv` **after** `/opt/ros/jazzy/setup.bash` |
| **hit** `ModuleNotFoundError: No module named 'rplidar'` over SSH | non-interactive shells do not run `.bashrc` | `source ~/botenv/bin/activate` explicitly in the command |
| `kiss-icp` build runs out of memory or dies | no swap on this image (historical — `kiss-icp` dropped in D5) | only if a heavy source build returns: add a 2 GB swapfile first |
| `Error opening terminal: xterm-ghostty` (from the Mac) | Ghostty terminfo missing on the Pi | **Durable fix** — on the Mac: `infocmp -x xterm-ghostty \| ssh robot@sherm-raspi.local 'tic -x -'` (tic prints a harmless alias warning); verify on the Pi with `infocmp xterm-ghostty \| head -3`. Quick fallback: `export TERM=xterm-256color`. **hit 2026-10-22** as `tmux attach` → `missing or unsuitable terminal`, cascading to `no server running on /tmp/tmux-1000/default` |
| `gpiozero`/`lgpio` import fails | those are Raspberry Pi OS apt packages; this box is Ubuntu | use `lgpio` from pip, or Adafruit Blinka — decide once, record in [01_hardware.md](01_hardware.md) |

## ROS 2 / Foxglove

| Symptom | Cause | Fix |
| --- | --- | --- |
| **hit** `ros2 launch foxglove_bridge ...` hangs or refuses to bind | a stale bridge already holds 8765 | `sudo fuser -k 8765/tcp` |
| no topics in Foxglove | bridge and client on different networks | the bridge binds 0.0.0.0:8765; connect by Tailscale IP `100.83.14.99` |
| `ros2 bag record` produces huge files | recording `/scan` at high rate uncompressed | MCAP + zstd is installed; keep `/scan`, `/imu/data`, `/odom`, `/cmd_vel`, `/plan` only |
| `.bashrc` sources ROS but the venv is lost | sourcing order | ROS first, `source ~/botenv/bin/activate` second |

## Reporting a problem

Put it in [`../notes.md`](../../notes/notes.md) with: date, exact error text, the command
that produced it, and what was tried. Then add a row here once it is understood.

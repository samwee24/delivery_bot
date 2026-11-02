# 02 · Pi setup — `sherm-raspi`

> This page is the **measured state** of this machine. The generic from-scratch
> install procedure is [`../pi_setup.md`](../pi_setup.md).

Target: `robot@sherm-raspi`, Raspberry Pi 4B Rev 1.4 (4 GB), Ubuntu 24.04.5 LTS,
kernel `6.8.0-1065-raspi`, Python 3.12.3, 32 GB card (3.6 GB used).

## State as of 2026-10-22

| Item | State |
| --- | --- |
| Access | `robot` over key auth; Mac key in `authorized_keys` ✅ |
| Tailscale | installed 2026-10-21, IP `100.83.14.99`, tailnet `chloe.tan.yi.ling@` ✅ |
| ROS 2 Jazzy | `/opt/ros/jazzy`, 184 MB, 205 `ros-jazzy-*` packages ✅ |
| `foxglove_bridge` | 3.6.0 installed ✅ |
| `rosbag2` | + `storage-mcap`, `storage-sqlite3`, `compression-zstd` ✅ |
| Colcon workspace | `~/ros2_ws` — `src/` holds `delivery_bot` (git `9e2fd2e`) + `rf2o_laser_odometry`; **build verified 2026-10-22, 5 packages, 3 min 43 s** ✅ |
| `pip` | installed (`python3-pip 24.0`) ✅ |
| venv | none — **not required** by the D5 stack (ROS runs from `/opt/ros/jazzy`); only needed for ad-hoc diagnostics |
| ROS stack | installed: `rplidar_ros 2.1.0`, `slam_toolbox 2.8.5`, `nav2_bringup 1.3.13`, `robot_localization 3.8.3`, `xacro 2.1.1`, `tf2_ros` ✅ |
| Serial access | `robot` **in `dialout`** (active after the 2026-10-22 reboot) ✅ |
| udev rule | rule written and reloaded; **`/dev/rplidar` still does not appear** ❌ — driver falls back to `/dev/ttyUSB0` |
| I2C | `/dev/i2c-1`, `-20`, `-21` present; MPU6050 **not yet probed**, `i2c-tools` not installed ⏸ |
| GPIO/PWM | **resolved**: `motor_node` uses gpiozero + `LGPIOFactory`; `lgpio` present in `/usr/lib/python3/dist-packages`, `RPi.GPIO` absent (by design on aarch64) ✅ |
| Swap | **2.0 GiB** `/swapfile`, persisted in `/etc/fstab` ✅ (added after an SSH outage, see notes) |
| Cooling / throttle | 40.4 °C idle; `vcgencmd` unavailable (needs `libraspberrypi-bin`), use `vcgencmd` from `raspi-utils` or read `/sys/class/thermal` ⚠️ |

## To-do (P0)

Run as `robot` unless noted; `sudo` needs the owner's password (not stored here).

- [x] **Serial access — udev route** (2026-10-22, partially)
  ```bash
  sudo usermod -aG dialout robot      # ran OK; takes effect at next login
  echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"' \
    | sudo tee /etc/udev/rules.d/99-rplidar.rules          # written
  sudo udevadm control --reload-rules && sudo udevadm trigger
  ls -l /dev/rplidar    # ❌ still absent — try: sudo udevadm trigger -c add -s tty, else replug the adapter
  ```
- [x] **Python tooling** (2026-10-22)
  ```bash
  sudo apt install python3-pip python3-venv python3-dev build-essential cmake i2c-tools
  ```
  All present except **`i2c-tools`** — install it before the IMU probe.
- [x] **Swap** (2026-10-22) — required before any large build; its absence took the
  machine off the network during a parallel `colcon build`.
  ```bash
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile && sudo swapon /swapfile
  echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
  ```
- [x] **ROS 2 stack (D5)** (2026-10-22) — packages were already installed; `rf2o` built here
  ```bash
  sudo apt install ros-jazzy-rplidar-ros ros-jazzy-slam-toolbox \
    ros-jazzy-robot-localization ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
    ros-jazzy-teleop-twist-keyboard ros-jazzy-robot-state-publisher
  mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
  git clone -b ros2 https://github.com/MAPIRlab/rf2o_laser_odometry.git
  cd ~/ros2_ws && source /opt/ros/jazzy/setup.bash
  colcon build --symlink-install --executor sequential --parallel-workers 1
  ros2 pkg prefix rf2o_laser_odometry
  ```
  Result: 5 packages, 3 min 43 s; `rf2o` alone 3 min 17 s. Build **one job at a time**
  on this Pi even with swap.
- [ ] **venv** — only for the two custom nodes (GPIO + I2C); no `--system-site-packages`
  ```bash
  python3 -m venv ~/botenv && ~/botenv/bin/pip install -U pip
  ~/botenv/bin/pip install numpy smbus2 lgpio
  ```
- [ ] **GPIO** — plan's `python3-lgpio` is Raspberry-Pi-OS-only. On Ubuntu use `lgpio` via pip,
  or `Adafruit-Blinka` + `adafruit-circuitpython-motorkit`. Decide before P1 motors; record in [01_hardware.md](01_hardware.md).
- [ ] **I2C probe** — `i2cdetect -y 1` must show `68` (MPU6050). Plan's `dtparam=i2c_arm_baudrate=400000`
  lives in `/boot/firmware/config.txt` on Pi OS; on Ubuntu 24.04 the Pi 4 path is the same file, but check
  `grep -i i2c /boot/firmware/config.txt` before editing.
- [ ] **ROS side** — custom package in `~/ros2_ws/src/` for the motor node, IMU node and URDF (see [07_ros_stack.md](07_ros_stack.md)); the rest comes from apt.
- [ ] **Shell** — `.bashrc` already sources `/opt/ros/jazzy/setup.bash` and `~/ros2_ws/install/setup.bash`.
  Add `source ~/botenv/bin/activate` after them (venv last, so ROS packages stay visible).

## Networking notes

- `sherm-raspi` (bare) does **not** resolve from the Mac — use `sherm-raspi.local`, `192.168.31.109`,
  or Tailscale `100.83.14.99`. Add an alias to `~/.ssh/config` once the setup is stable.
- `ssh-copy-id` failed earlier for lack of `sshpass`; key was installed through an `expect` password session instead.

## Machine inventory from the CA3 brief (different box, now offline)

`robot` @ `100.73.7.24` — Debian 13 Trixie, Raspberry Pi OS Lite 64-bit, aarch64,
hostname `robot`, `~/botenv` (with `--system-site-packages`), `~/delivery-bot/`,
`99-rplidar.rules`, `rplidar-roboticia` + `kiss-icp` + `smbus2` installed. Offline
since 2026-10-21 (OI-1). Its setup predates D5 — treat it as history, not as the P0
target for `sherm-raspi`.

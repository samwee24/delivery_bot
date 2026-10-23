# Raspberry Pi setup (Ubuntu 24.04 + ROS 2 Jazzy)

Assumes the ROS 2 Jazzy apt repository is configured. Run as `robot`.

> This page is the **from-scratch install**. The measured state of the actual robot
> (`sherm-raspi`, with every step verified or still failing) is
> [`system/02_pi_setup.md`](system/02_pi_setup.md).

## 1. Clock first

A wrong clock makes apt fail with signature/"not live until" errors, and every bag
timestamp wrong.

```bash
sudo date -s "$(curl -sI https://www.google.com | grep -i '^date:' | cut -d' ' -f2-)"
date   # sanity check

# make it survive reboots (this network blocks NTP, htpdate polls HTTP)
sudo apt install -y htpdate
sudo systemctl enable --now htpdate
```

## 2. Packages

```bash
sudo apt update
sudo apt install -y python3-vcstool python3-rosdep git \
  ros-jazzy-rplidar-ros ros-jazzy-slam-toolbox ros-jazzy-robot-localization \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-foxglove-bridge \
  ros-jazzy-teleop-twist-keyboard ros-jazzy-robot-state-publisher ros-jazzy-xacro \
  ros-jazzy-nav2-simple-commander python3-smbus2 python3-gpiozero python3-lgpio
```

Check a name before trusting it: `apt-cache policy <name>`.

## 3. Serial access for the lidar

CP210x adapter is `10c4:ea60`. The udev rule both creates `/dev/rplidar` and makes it
world-writable, which also covers the group being late to apply:

```bash
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0666"' \
  | sudo tee /etc/udev/rules.d/99-rplidar.rules
sudo udevadm control --reload-rules
sudo udevadm trigger -c add -s tty     # needed for an already-attached device
ls -l /dev/rplidar                     # -> ttyUSB0
```

If the symlink still does not appear, unplug and replug the adapter.

## 4. Groups: serial, I2C, GPIO

```bash
sudo usermod -aG dialout robot
```

On this image `/dev/ttyUSB0`, `/dev/i2c-1` and `/dev/gpiochip0` are all
`root:dialout 0660`, so `dialout` covers the lidar, the IMU and the GPIO lines. A new
login is required (`newgrp dialout` for the current shell). Verify:

```bash
id | grep dialout
ls -l /dev/i2c-1 /dev/gpiochip0
```

If a future image makes `/dev/gpiochip0` root-only, add:

```bash
echo 'SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="dialout", MODE="0660"' \
  | sudo tee /etc/udev/rules.d/98-gpio.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## 5. Ghostty terminal

The Mac's Ghostty advertises `TERM=xterm-ghostty`, which the Pi's terminfo lacks.
`tmux` fails with `missing or unsuitable terminal`, and `nano` misbehaves. Install the
entry once, from the Mac:

```bash
infocmp -x xterm-ghostty | ssh robot@<pi> 'tic -x -'
```

`tic` may print an alias warning; it is harmless. Verify on the Pi with
`infocmp xterm-ghostty | head -3`. Quick fallback: `export TERM=xterm-256color`.

## 6. Tailscale (optional, for working off the LAN)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4
```

## 7. Workspace

```bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone git@github.com:samwee24/delivery_bot.git
vcs import . < delivery_bot/deps.repos
cd ~/ros2_ws
sudo rosdep init 2>/dev/null; rosdep update
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install
```

Add to `~/.bashrc` (if not already there), in this order:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

## 8. Non-interactive SSH

`.bashrc` is not sourced for non-interactive commands. In scripts and over
`ssh host 'cmd'`, source explicitly:

```bash
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
```

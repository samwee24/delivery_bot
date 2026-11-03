#!/bin/bash
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
AC=${1:-true}
echo "angle_compensate $AC"; echo "throttled start: $(vcgencmd get_throttled)"
echo "stale: $(ps -eo cmd | grep -cE '[s]lam_toolbox|[r]os2 launch|[r]plidar_c|[f]oxglove_b|[i]mu_node|[e]kf_node|[r]f2o')"
setsid nohup ros2 launch delivery_bot_slam rf2o_alone.launch.py angle_compensate:=$AC > /tmp/push_rf2o.log 2>&1 < /dev/null &
setsid nohup ros2 run delivery_bot_drivers imu_node --ros-args --params-file ~/ros2_ws/src/delivery_bot/delivery_bot_drivers/config/drivers.yaml > /tmp/push_imu.log 2>&1 < /dev/null &
sleep 30
echo "S/N lines: $(grep -c 'RPLIDAR S/N' /tmp/push_rf2o.log) rf2o odom lines: $(grep -c 'Laser odom' /tmp/push_rf2o.log) imu calib: $(grep -c 'gyro bias' /tmp/push_imu.log) imu fail: $(grep -c 'calib_max_std' /tmp/push_imu.log)"
B=~/bags/$(date +%F)_push_ac${AC}_$(date +%H%M%S)
echo "bag $B"
setsid nohup ros2 bag record -s mcap -o $B /scan /odom_rf2o /imu/data /tf /tf_static /marker > /tmp/push_bag.log 2>&1 < /dev/null &
sleep 4
grep -E "Recording|Opened|rror" /tmp/push_bag.log | head -3

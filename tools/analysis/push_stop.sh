#!/bin/bash
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
pkill -TERM -f "[r]os2 bag record"; sleep 4
B=$(ls -dt ~/bags/2026-11-01_push_* | head -1)
ls $B
pkill -TERM -f "[r]os2 launch delivery_bot_slam rf2o_alone"; sleep 6
for p in rplidar_composit[i]on imu_nod[e] rf2o_laser_odometry_nod[e] robot_state_publishe[r]; do pkill -f "$p"; done
sleep 2
echo "left: $(ps -eo cmd | grep -cE '[s]lam_toolbox|[r]os2 launch|[r]plidar_c|[i]mu_node|[r]f2o|[r]os2 bag')"
python3 ~/ros2_ws/src/delivery_bot/tools/analysis/push_an.py $B

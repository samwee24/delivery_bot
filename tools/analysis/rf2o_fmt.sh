#!/bin/bash
# usage: rf2o_fmt.sh <bag> <orig|resampled> ; own domain, so nothing live is touched
# An empty override (`-p name:=`) is rejected by rcl, so the empty string is passed as ''.
export ROS_DOMAIN_ID=42
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
BAG=$1; MODE=$2; OUT=/tmp/fmt_$MODE; rm -rf $OUT
setsid nohup ros2 run rf2o_laser_odometry rf2o_laser_odometry_node --ros-args -r __node:=rf2o_laser_odometry -p laser_scan_topic:=/scan -p odom_topic:=/odom_rf2o -p publish_tf:=false -p base_frame_id:=base_footprint -p odom_frame_id:=odom -p "init_pose_from_topic:=''" -p freq:=20.0 -p use_sim_time:=true > /tmp/fmt_rf2o.log 2>&1 < /dev/null &
if [ "$MODE" = resampled ]; then setsid nohup python3 ~/ros2_ws/src/delivery_bot/tools/analysis/resample_scan.py --ros-args -p use_sim_time:=true > /tmp/fmt_res.log 2>&1 < /dev/null & REMAP="--remap /scan:=/scan_raw"; else REMAP=""; fi
setsid nohup ros2 bag record -s mcap -o $OUT /odom_rf2o > /tmp/fmt_rec.log 2>&1 < /dev/null &
sleep 6
ros2 bag play $BAG --clock --topics /scan /tf_static $REMAP > /tmp/fmt_play.log 2>&1
sleep 3
pkill -TERM -f "[r]os2 bag record"; sleep 3
pkill -f "[r]f2o_laser_odometry_node"; pkill -f "[r]esample_scan.py"
echo "== $MODE: $(grep -c 'Laser odom' /tmp/fmt_rf2o.log) rf2o updates"
python3 ~/ros2_ws/src/delivery_bot/tools/analysis/push_an.py $OUT | tail -2

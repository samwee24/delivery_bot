#!/bin/bash
# Camera quality under SLAM load: replay 45 s of the 5.4 bag through slam_replay once per camera setting
# and record camera rate, node CPU, slam CPU, load, dropped scans and poses written.
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
BAG=~/bags/2026-10-31_map_200956
CFG=~/ros2_ws/src/delivery_bot/delivery_bot_bringup/config/camera.yaml
OUT=/tmp/loadtest; rm -rf $OUT; mkdir -p $OUT

killslam(){
  pkill -INT -f "ros2 launch delivery_bot_sla[m]"; sleep 8
  for p in async_slam_toolbo[x] ekf_nod[e] rf2o_lase[r] odom_covarianc[e] trajectory_recorde[r] robot_state_publishe[r] imu_nod[e] static_transform_publishe[r] "ros2 ba[g]"; do pkill -9 -f "$p"; done
  sleep 2
}
killcam(){ pkill -f "usb_cam_node_ex[e]"; pkill -f "ros2 launch delivery_bot_bringup camera"; sleep 3; }
startcam(){ # $1 w $2 h $3 fps
  sed -e "s/image_width: .*/image_width: $1/" -e "s/image_height: .*/image_height: $2/" \
      -e "s/framerate: .*/framerate: $3.0/" $CFG > /tmp/cam_try.yaml
  nohup /opt/ros/jazzy/lib/usb_cam/usb_cam_node_exe --ros-args -r __node:=camera \
      --params-file /tmp/cam_try.yaml > /tmp/cam_try.log 2>&1 &
}

pkill -f "rplidar_compositio[n]"; killslam; killcam   # live lidar off: the bag supplies /scan

for S in "none 0 0" "640 480 30" "1024 768 15" "1280 720 10" "1280 720 5" "1920 1080 5"; do
  set -- $S; V="$1x$2@$3"; mkdir -p $OUT/$V/tum
  echo "== $V $(date +%T)"
  killcam
  [ "$1" != none ] && startcam $1 $2 $3
  nohup ros2 launch delivery_bot_slam slam_replay.launch.py use_sim_time:=true foxglove:=false \
      tum_output_dir:=$OUT/$V/tum > $OUT/$V/launch.log 2>&1 &
  sleep 15
  timeout 65 ros2 bag play $BAG --clock --topics /scan /imu/data /tf_static > $OUT/$V/play.log 2>&1 &
  sleep 8
  if [ "$1" != none ]; then
    timeout 25 ros2 topic hz /image_raw/compressed --window 20 2>&1 | grep "average rate" | tail -1 > $OUT/$V/camhz.txt &
    CPID=$(pgrep -x usb_cam_node_ex | head -1)
    top -b -n 2 -d 5 -p $CPID | tail -1 | awk '{print $9}' > $OUT/$V/camcpu.txt
  fi
  SPID=$(pgrep -f "async_slam_toolbo[x]" | head -1)
  top -b -n 2 -d 5 -p $SPID | tail -1 | awk '{print $9}' > $OUT/$V/slamcpu.txt
  cat /proc/loadavg | cut -d' ' -f1 > $OUT/$V/load.txt
  sleep 36
  drops=$(grep -c "Message Filter dropping" $OUT/$V/launch.log); ekf=$(grep -c "Failed to meet update rate" $OUT/$V/launch.log)
  echo "cam_hz: $(cat $OUT/$V/camhz.txt 2>/dev/null) cam_cpu: $(cat $OUT/$V/camcpu.txt 2>/dev/null) slam_cpu: $(cat $OUT/$V/slamcpu.txt) load1: $(cat $OUT/$V/load.txt) slam_drops: $drops ekf_late: $ekf"
  killslam
done
killcam
echo LOADTEST_DONE

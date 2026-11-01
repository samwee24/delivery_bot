#!/bin/bash
# step camera resolution/fps, print compressed-topic rate, bandwidth and node CPU for each
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
CFG=~/ros2_ws/src/delivery_bot/delivery_bot_bringup/config/camera.yaml
for s in "640 480 30" "1280 720 15" "1280 720 30" "1920 1080 15" "1920 1080 30"; do
  set -- $s
  pkill -f usb_cam_node_exe; sleep 2
  sed -e "s/image_width: .*/image_width: $1/" -e "s/image_height: .*/image_height: $2/" \
      -e "s/framerate: .*/framerate: $3.0/" $CFG > /tmp/cam_try.yaml
  nohup /opt/ros/jazzy/lib/usb_cam/usb_cam_node_exe --ros-args -r __node:=camera \
      --params-file /tmp/cam_try.yaml > /tmp/cam_try.log 2>&1 &
  sleep 6
  PID=$(pgrep -x usb_cam_node_ex | head -1)
  echo "== $1x$2 @ $3"
  timeout 12 ros2 topic hz /image_raw/compressed --window 30 2>&1 | grep "average rate" | tail -1 &
  H=$!
  timeout 12 ros2 topic bw /image_raw/compressed 2>&1 | tail -1 &
  B=$!
  sleep 5
  top -b -n 2 -d 3 -p $PID | tail -1 | awk '{print "cpu%", $9}'
  wait $H $B
  uptime | sed 's/.*load/load/'
done

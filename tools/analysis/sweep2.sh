#!/bin/bash
# 720p/1080p with lower jpeg_quality on the compressed transport; rate + cpu per setting
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
CFG=~/ros2_ws/src/delivery_bot/delivery_bot_bringup/config/camera.yaml
for s in "1024 768 15 95" "1280 720 10 95" "1600 896 7 95"; do
  set -- $s
  pkill -f "usb_cam_node_ex[e]"; sleep 3
  sed -e "s/image_width: .*/image_width: $1/" -e "s/image_height: .*/image_height: $2/" \
      -e "s/framerate: .*/framerate: $3.0/" $CFG > /tmp/cam_try.yaml
  echo "    image_raw.compressed.jpeg_quality: $4" >> /tmp/cam_try.yaml
  nohup /opt/ros/jazzy/lib/usb_cam/usb_cam_node_exe --ros-args -r __node:=camera \
      --params-file /tmp/cam_try.yaml > /tmp/cam_try.log 2>&1 &
  sleep 6
  PID=$(pgrep -x usb_cam_node_ex | head -1)
  echo "== $1x$2 @ $3 q$4"
  timeout 14 ros2 topic hz /image_raw/compressed --window 40 2>&1 | grep "average rate" | tail -1 &
  H=$!
  timeout 14 ros2 topic bw /image_raw/compressed 2>&1 | grep -E "Message size|MB/s|KB/s" | tail -2 &
  B=$!
  sleep 6
  top -b -n 2 -d 3 -p $PID | tail -1 | awk '{print "cpu%", $9}'
  wait $H $B
done

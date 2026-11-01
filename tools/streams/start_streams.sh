#!/bin/bash
# Start streams on the Pi. Safe to rerun: anything already running is left alone.
#   Both modes also start the Foxglove bridge and tools/robot_control.py, which gives Foxglove
#   Call Service buttons for stacks, bag, camera, stream and power (see README).
#   bash tools/streams/start_streams.sh        ROS camera + Foxglove bridge + audio only
#       video  Foxglove ws://100.83.14.99:8765, Image panel on /image_raw/compressed
#       audio  http://100.83.14.99:8090/audio.mp3 (browser or VLC)
#   bash tools/streams/start_streams.sh av     one combined picture+sound stream, no ROS camera
#       vlc http://100.83.14.99:8090/stream.mkv
# The two modes share the camera and the mic, so switching stops the other one's processes.
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
R=~/ros2_ws/src/delivery_bot
if ! pgrep -f "[f]oxglove_bridge" > /dev/null; then setsid nohup ros2 run foxglove_bridge foxglove_bridge --ros-args -p 'topic_whitelist:=["^(?!/image_raw$)(?!/image_raw/(zstd|theora|compressedDepth)).*"]' > /tmp/fox.log 2>&1 < /dev/null & fi
if ! pgrep -f "[r]obot_control.py" > /dev/null; then setsid nohup python3 $R/tools/robot_control.py > /tmp/ctl.log 2>&1 < /dev/null & fi
if [ "$1" = av ]; then
  pkill -f "[u]sb_cam_node_exe"; pkill -f "[a]udio_stream.py$"; sleep 2
  if ! pgrep -f "[a]udio_stream.py --video" > /dev/null; then setsid nohup python3 $R/tools/streams/audio_stream.py --video > /tmp/audio.log 2>&1 < /dev/null & fi
  sleep 8; echo "av stream $(pgrep -fc '[a]udio_stream.py --video')"; exit
fi
pkill -f "[a]udio_stream.py --video"
if ! pgrep -f "[u]sb_cam_node_exe" > /dev/null; then setsid nohup ros2 launch delivery_bot_bringup camera.launch.py > /tmp/cam.log 2>&1 < /dev/null & fi
if ! pgrep -f "[f]oxglove_bridge" > /dev/null; then setsid nohup ros2 run foxglove_bridge foxglove_bridge --ros-args -p 'topic_whitelist:=["^(?!/image_raw$)(?!/image_raw/(zstd|theora|compressedDepth)).*"]' > /tmp/fox.log 2>&1 < /dev/null & fi
if ! pgrep -f "[a]udio_stream.py" > /dev/null; then setsid nohup python3 $R/tools/streams/audio_stream.py > /tmp/audio.log 2>&1 < /dev/null & fi
sleep 10
echo "camera $(pgrep -fc '[u]sb_cam_node_exe') bridge $(pgrep -fc '[f]oxglove_bridge') audio $(pgrep -fc '[a]udio_stream.py')"

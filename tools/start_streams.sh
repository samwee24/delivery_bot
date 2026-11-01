#!/bin/bash
# Start the camera, the Foxglove bridge and the microphone stream on the Pi. Safe to rerun:
# anything already running is left alone. Stop one with: pkill -f <name>.
#   video  Foxglove ws://100.83.14.99:8765, Image panel on /image_raw/compressed
#   audio  http://100.83.14.99:8090/audio.mp3 (browser or VLC)
source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
R=~/ros2_ws/src/delivery_bot
pgrep -f "[u]sb_cam_node_exe" > /dev/null || setsid nohup ros2 launch delivery_bot_bringup camera.launch.py > /tmp/cam.log 2>&1 < /dev/null &
pgrep -f "[f]oxglove_bridge" > /dev/null || setsid nohup ros2 run foxglove_bridge foxglove_bridge --ros-args -p 'topic_whitelist:=["^(?!/image_raw$)(?!/image_raw/(zstd|theora|compressedDepth)).*"]' > /tmp/fox.log 2>&1 < /dev/null &
pgrep -f "[a]udio_stream.py" > /dev/null || setsid nohup python3 $R/tools/audio_stream.py > /tmp/audio.log 2>&1 < /dev/null &
sleep 10
echo "camera $(pgrep -fc '[u]sb_cam_node_exe') bridge $(pgrep -fc '[f]oxglove_bridge') audio $(pgrep -fc '[a]udio_stream.py')"

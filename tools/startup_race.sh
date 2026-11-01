#!/bin/bash
# Build path 3.4: launch rf2o_alone N times, count launches whose rf2o log has a
# lookupTransform / transform error.   bash tools/startup_race.sh [N] [rf2o_delay]
# Run on the Pi with the lidar free (stop any other rplidar_node first).
N=${1:-10}; DELAY=${2:-2.0}
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
bad=0
for i in $(seq 1 "$N"); do
  log=/tmp/startup_race_$i.log
  timeout 20 ros2 launch delivery_bot_slam rf2o_alone.launch.py rf2o_delay:="$DELAY" > "$log" 2>&1
  if grep -qiE 'lookupTransform|could not (get|find) .*transform|extrapolation' "$log"; then
    bad=$((bad+1)); echo "run $i: TRANSFORM ERROR"
  else echo "run $i: ok"; fi
done
echo "delay=$DELAY  runs=$N  with_error=$bad"

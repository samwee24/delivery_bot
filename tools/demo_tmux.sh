#!/usr/bin/env bash
# Nav2 obstacle demo in one tmux window. Types the commands, runs none of them:
# press Enter in a pane to run its command.
#   left        : the stack (launch args are passed through, e.g. dry_run:=...)
#   top right   : the robot-frame goal, GOAL_X metres ahead (default 1.5)
#   bottom right: map pose of the robot (check it sits on the home mark first)
# Usage: tools/demo_tmux.sh [launch args...]; GOAL_X=2.0 tools/demo_tmux.sh ...
# Ctrl+C in the goal pane cancels the goal; Ctrl+C in the left pane stops the stack.
set -eu
S=nav2demo
X=${GOAL_X:-1.5}
tmux has-session -t "$S" 2>/dev/null && exec tmux attach -t "$S"

LAUNCH="ros2 launch delivery_bot_bringup navigation.launch.py bridge:=false $*"
GOAL="ros2 action send_goal --feedback /navigate_to_pose nav2_msgs/action/NavigateToPose \"{pose: {header: {frame_id: base_footprint}, pose: {position: {x: $X, y: 0.0}, orientation: {w: 1.0}}}}\" | grep --line-buffered -E '^  sec|distance_remaining|number_of_recoveries|error_code|status' | uniq"
POSE="ros2 run tf2_ros tf2_echo map base_footprint 2>&1 | grep --line-buffered -A3 Translation"

tmux new-session -d -s "$S" -x 220 -y 50
tmux split-window -h -t "$S"
tmux split-window -v -t "$S:0.1"
tmux send-keys -t "$S:0.0" "$LAUNCH"
tmux send-keys -t "$S:0.1" "$GOAL"
tmux send-keys -t "$S:0.2" "$POSE"
tmux select-pane -t "$S:0.0"
exec tmux attach -t "$S"

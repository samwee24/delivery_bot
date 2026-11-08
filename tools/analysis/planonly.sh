source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=42        # isolated from the live stack on domain 0
cd /tmp
setsid nohup ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=$HOME/maps/2026-10-31_room2.yaml > /tmp/po_map.log 2>&1 &
setsid nohup ros2 run tf2_ros static_transform_publisher --frame-id map --child-frame-id base_footprint > /tmp/po_tf.log 2>&1 &
setsid nohup ros2 run nav2_planner planner_server --ros-args --params-file /tmp/nav2_params.yaml > /tmp/po_plan.log 2>&1 &
setsid nohup ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args -r __node:=lm_planonly -p autostart:=true -p "node_names:=[map_server,planner_server]" > /tmp/po_lm.log 2>&1 &
sleep 20
echo ---lm; grep -E "Managed nodes are active|Failed|error" /tmp/po_lm.log | head -5
echo ---plan; grep -iE "error|fail" /tmp/po_plan.log | head -5
python3 /tmp/plan_check.py
echo ---topics; ros2 topic list | grep -E "cmd_vel|plan$"
uptime; vcgencmd get_throttled
pkill -f 'ROS_DOMAIN_ID=42' 2>/dev/null
pkill -f "yaml_filename:=$HOME/maps/2026-10-31_room2.yaml"; pkill -f 'lm_planonly'; pkill -f 'nav2_planner/planner_server'; pkill -f 'static_transform_publisher --frame-id map --child-frame-id base_footprint'
sleep 2; ps -eo cmd | grep -E "planner_server|lm_planonly|map_server" | grep -v grep | wc -l

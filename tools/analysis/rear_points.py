import sys, math, rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import LaserScan
r=rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=sys.argv[1],storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
rows=[];t0=None
while r.has_next():
    t,d,ts=r.read_next()
    if t!='/scan': continue
    m=deserialize_message(d,LaserScan)
    if t0 is None: t0=ts*1e-9
    near=[];allnear=0
    for i,v in enumerate(m.ranges):
        a=math.degrees(m.angle_min+i*m.angle_increment)
        if math.isfinite(v) and v>0.1:
            if abs(a)>135 and v<1.2: near.append((v,a))
            if v<1.2: allnear+=1
    rows.append((ts*1e-9-t0,len(near),min([v for v,_ in near],default=0),sum(a for _,a in near)/len(near) if near else 0))
step=max(1,len(rows)//20)
for k in range(0,len(rows),step): print('%5.1fs rear<1.2m pts %3d  nearest %.2f m  mean angle %6.1f'%rows[k])

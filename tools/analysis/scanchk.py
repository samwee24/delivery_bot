import sys, math, statistics as st, rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import LaserScan
r=rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=sys.argv[1],storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
S=[]
while r.has_next():
    t,d,ts=r.read_next()
    if t=='/scan': S.append((ts*1e-9,deserialize_message(d,LaserScan)))
t0=S[0][0]
def med(scans,deg):
    out=[]
    for _,m in scans:
        for i,v in enumerate(m.ranges):
            a=math.degrees(m.angle_min+i*m.angle_increment)
            da=(a-deg+180)%360-180
            if abs(da)<=3 and math.isfinite(v) and v>0.1: out.append(v)
    return round(st.median(out),3) if out else None
start=[s for s in S if s[0]-t0<70]
end=[s for s in S if s[0]-S[-1][0]>-12]
print('scans',len(S),'start',len(start),'end',len(end))
for deg in (0,90,180,-90): print('angle',deg,'start',med(start,deg),'end',med(end,deg))

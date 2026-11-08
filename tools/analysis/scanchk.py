"""usage: scanchk.py <bag> [W]
Median /scan range at 0, 90, 180 and -90 deg over the first W s (default 70) and the last 12 s."""
import sys, math, statistics as st


def med(scans,deg):
    """Median finite range > 0.1 m within 3 deg of deg (wrapped) over [(t, LaserScan)]; None if no beams."""
    out=[]
    for _,m in scans:
        for i,v in enumerate(m.ranges):
            a=math.degrees(m.angle_min+i*m.angle_increment)
            da=(a-deg+180)%360-180
            if abs(da)<=3 and math.isfinite(v) and v>0.1: out.append(v)
    return round(st.median(out),3) if out else None


if __name__ == '__main__':
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from sensor_msgs.msg import LaserScan
    r=rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=sys.argv[1],storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
    S=[]
    while r.has_next():
        t,d,ts=r.read_next()
        if t=='/scan': S.append((ts*1e-9,deserialize_message(d,LaserScan)))
    t0=S[0][0]
    W=float(sys.argv[2]) if len(sys.argv)>2 else 70
    start=[s for s in S if s[0]-t0<W]
    end=[s for s in S if s[0]-S[-1][0]>-12]
    print('scans',len(S),'start',len(start),'end',len(end))
    for deg in (0,90,180,-90): print('angle',deg,'start',med(start,deg),'end',med(end,deg))

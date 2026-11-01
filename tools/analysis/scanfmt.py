import sys, math, rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import LaserScan
for b in sys.argv[1:]:
    r=rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=b,storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
    n=0;f=None;ts=[]
    while r.has_next():
        t,d,s=r.read_next()
        if t=='/scan':
            m=deserialize_message(d,LaserScan); ts.append(s*1e-9)
            if f is None: f=m
    print(b.split('/')[-1],'scans',len(ts),'rate %.2f Hz'%((len(ts)-1)/(ts[-1]-ts[0])),'beams',len(f.ranges),'inc %.5f rad (%.3f deg)'%(f.angle_increment,math.degrees(f.angle_increment)),'min %.3f max %.3f'%(f.angle_min,f.angle_max),'scan_time %.4f time_inc %.6f'%(f.scan_time,f.time_increment),'range_max',f.range_max)

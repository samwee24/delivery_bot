import sys, math, rosbag2_py
from rclpy.serialization import deserialize_message
from nav_msgs.msg import Odometry
r=rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=sys.argv[1],storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
P=[]
while r.has_next():
    t,d,ts=r.read_next()
    if t=='/odom_rf2o':
        m=deserialize_message(d,Odometry);q=m.pose.pose.orientation
        P.append((ts*1e-9,m.pose.pose.position.x,m.pose.pose.position.y,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))))
t0,x0,y0,h0=P[0];c,s=math.cos(-h0),math.sin(-h0)
Q=[(t-t0,(x-x0)*c-(y-y0)*s,(x-x0)*s+(y-y0)*c,math.degrees(h-h0)) for t,x,y,h in P]
print('n',len(Q))
for k in range(0,len(Q),max(1,len(Q)//25)): print('%5.0fs x %6.3f y %6.3f yaw %6.1f'%Q[k])
xs=[q[1] for q in Q];i=xs.index(min(xs));print('min x',round(min(xs),3),'at',round(Q[i][0]),'s; max x',round(max(xs),3),'; final',[round(v,3) for v in Q[-1][1:]])
print('forward leg: from min x',round(xs[-1]-min(xs),3),'m; lateral at end vs at min',round(Q[-1][2]-Q[i][2],3),'yaw change',round(Q[-1][3]-Q[i][3],1))

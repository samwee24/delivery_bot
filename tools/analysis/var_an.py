import sys, math, statistics as st, rosbag2_py
from rclpy.serialization import deserialize_message
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
def load(uri):
    r=rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=uri,storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
    O=[];G=[]
    while r.has_next():
        t,d,ts=r.read_next()
        if t=='/odom_rf2o':
            m=deserialize_message(d,Odometry);O.append((ts*1e-9,m.twist.twist.linear.x,m.twist.twist.angular.z))
        elif t=='/imu/data':
            m=deserialize_message(d,Imu);G.append((ts*1e-9,m.angular_velocity.z))
    return O,G
def var(x): return st.pvariance(x)
for name,uri in [('turn',sys.argv[1]),('push',sys.argv[2])]:
    O,G=load(uri);t0=O[0][0]
    gm=[abs(g) for _,g in G]
    # motion window: gyro |wz| > 0.1 rad/s (turn) or rf2o |vx|>0.05 (push)
    on,off,r0,r1=(84,100,25,80) if name=='turn' else (18,52,2,16)
    print(name,'rf2o msgs',len(O),'motion window %.1f..%.1f s'%(on,off))
    rest=[(t,vx,wz) for t,vx,wz in O if r0<t-t0<r1]
    grest=[g for t,g in G if r0<t-t0<r1]
    print('  rest n_rf2o',len(rest),'vx var %.2e'%var([x[1] for x in rest]),'wz var %.2e'%var([x[2] for x in rest]),'| gyro n',len(grest),'var %.2e mean %.4f'%(var(grest),st.mean(grest)))
    # moving: gyro mean over each rf2o interval vs rf2o wz
    res=[];rf=[];gg=[];j=0
    for i in range(1,len(O)):
        if not(on<=O[i][0]-t0<=off): continue
        a,b=O[i-1][0],O[i][0]
        seg=[g for t,g in G if a<=t<b]
        if seg: res.append(O[i][2]-st.mean(seg));rf.append(O[i][2]);gg.append(st.mean(seg))
    if res:
        print('  moving n',len(res),'rf2o-gyro wz resid var %.2e (sd %.3f) mean %.4f; gyro rms %.3f'%(var(res),math.sqrt(var(res)),st.mean(res),math.sqrt(st.mean([g*g for g in gg]))))
        k=sum(a*b for a,b in zip(rf,gg))/sum(b*b for b in gg);print('  rf2o/gyro slope %.3f'%k)
    vx=[x[1] for x in O if on<=x[0]-t0<=off]
    print('  moving vx mean %.3f max %.3f'%(st.mean(vx),max(abs(v) for v in vx)))

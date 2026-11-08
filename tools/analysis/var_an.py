"""usage: var_an.py <turn bag> <push bag>
rf2o twist and gyro z variance at rest, and the rf2o-gyro wz residual while moving (hard-coded windows)."""
import sys, math, statistics as st


def var(x): return st.pvariance(x)


def rest(O,G,t0,r0,r1):
    """rf2o rows [(t, vx, wz)] and gyro wz values strictly inside (r0, r1) s after t0."""
    return [(t,vx,wz) for t,vx,wz in O if r0<t-t0<r1],[g for t,g in G if r0<t-t0<r1]


def moving(O,G,t0,on,off):
    """For each rf2o message i whose time is in [on, off] s after t0, the mean gyro wz over
    [t_(i-1), t_i): returns (rf2o wz - gyro mean, rf2o wz, gyro mean) lists. Intervals with no gyro are skipped."""
    res=[];rf=[];gg=[]
    for i in range(1,len(O)):
        if not(on<=O[i][0]-t0<=off): continue
        a,b=O[i-1][0],O[i][0]
        seg=[g for t,g in G if a<=t<b]
        if seg: res.append(O[i][2]-st.mean(seg));rf.append(O[i][2]);gg.append(st.mean(seg))
    return res,rf,gg


def slope(rf,gg): return sum(a*b for a,b in zip(rf,gg))/sum(b*b for b in gg)


def load(uri):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import Imu
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


if __name__ == '__main__':
    for name,uri in [('turn',sys.argv[1]),('push',sys.argv[2])]:
        O,G=load(uri);t0=O[0][0]
        # motion window: gyro |wz| > 0.1 rad/s (turn) or rf2o |vx|>0.05 (push)
        on,off,r0,r1=(84,100,25,80) if name=='turn' else (18,52,2,16)
        print(name,'rf2o msgs',len(O),'motion window %.1f..%.1f s'%(on,off))
        R,grest=rest(O,G,t0,r0,r1)
        print('  rest n_rf2o',len(R),'vx var %.2e'%var([x[1] for x in R]),'wz var %.2e'%var([x[2] for x in R]),'| gyro n',len(grest),'var %.2e mean %.4f'%(var(grest),st.mean(grest)))
        # moving: gyro mean over each rf2o interval vs rf2o wz
        res,rf,gg=moving(O,G,t0,on,off)
        if res:
            print('  moving n',len(res),'rf2o-gyro wz resid var %.2e (sd %.3f) mean %.4f; gyro rms %.3f'%(var(res),math.sqrt(var(res)),st.mean(res),math.sqrt(st.mean([g*g for g in gg]))))
            print('  rf2o/gyro slope %.3f'%slope(rf,gg))
        vx=[x[1] for x in O if on<=x[0]-t0<=off]
        print('  moving vx mean %.3f max %.3f'%(st.mean(vx),max(abs(v) for v in vx)))

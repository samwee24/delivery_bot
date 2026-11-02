"""usage: turn_an.py <bag>
rf2o yaw (unwrapped) against integrated gyro z over a hand turn."""
import sys, math


def unwrap(Y):
    """Y: [(t, yaw_rad)] -> [(t, cumulative yaw change, rad)], each step wrapped to [-pi, pi)."""
    u=[];p=None;acc=0
    for ts,y in Y:
        if p is not None:
            d=y-p; d=(d+math.pi)%(2*math.pi)-math.pi; acc+=d
        p=y;u.append((ts,acc))
    return u


def integrate(gz):
    """gz: [(t, wz)] -> sum of wz * dt, each sample weighted by the gap since the one before."""
    g=0
    for i in range(1,len(gz)): g+=gz[i][1]*(gz[i][0]-gz[i-1][0])
    return g


if __name__ == '__main__':
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import Imu
    r=rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=sys.argv[1],storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
    yaw=[];gz=[]
    while r.has_next():
        t,d,ts=r.read_next()
        if t=='/odom_rf2o':
            m=deserialize_message(d,Odometry); q=m.pose.pose.orientation
            y=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
            yaw.append((ts*1e-9,y,m.pose.pose.position.x,m.pose.pose.position.y))
        elif t=='/imu/data':
            m=deserialize_message(d,Imu); gz.append((ts*1e-9,m.angular_velocity.z))
    u=unwrap([(ts,y) for ts,y,_,_ in yaw]);acc=u[-1][1] if u else 0
    g=integrate(gz)
    print('rf2o msgs',len(yaw),'imu msgs',len(gz))
    print('rf2o total yaw deg',round(math.degrees(acc),1))
    print('gyro integrated deg',round(math.degrees(g),1))
    print('rf2o final xy m',round(yaw[-1][2],3),round(yaw[-1][3],3))
    mx=max(abs(a) for _,a in u); print('rf2o max |yaw| deg',round(math.degrees(mx),1))
    # 20 s checkpoints
    for k in range(0,len(u),max(1,len(u)//12)): print(round(u[k][0]-u[0][0]),'s rf2o',round(math.degrees(u[k][1]),1))

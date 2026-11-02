"""usage: gap.py <bag> <map.yaml> <map.pgm>
Last robot pose in the map frame (map->odom from /tf composed with /odometry/filtered), then the
distance along four rays to the first occupied cell of the saved map."""
import sys, math, re


def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))


def compose(mo,od):
    """map->odom (x, y, yaw) composed with odom->base (x, y, yaw) -> base pose in map."""
    c,s=math.cos(mo[2]),math.sin(mo[2])
    return mo[0]+c*od[0]-s*od[1],mo[1]+s*od[0]+c*od[1],mo[2]+od[2]


def origin(yml): return [float(v) for v in re.search(r'origin:\s*\[([^\]]+)\]',yml).group(1).split(',')[:2]]


def pgm(pg):
    """Binary PGM (P5, no comment lines) -> (width, height, pixel bytes)."""
    parts=pg.split(b'\n',3);w,h=map(int,parts[1].split())
    return w,h,parts[3]


def ray(px,w,h,ox,oy,x,y,a):
    """Distance from (x, y) along heading a to the first occupied (0) cell, in 0.025 m steps up to
    10 m; None if the ray leaves the map or hits nothing. Map resolution is 0.05 m, row 0 at the top."""
    def occ(wx,wy):
        i=int((wx-ox)/0.05);j=int((wy-oy)/0.05)
        if not(0<=i<w and 0<=j<h): return None
        return px[(h-1-j)*w+i]
    for k in range(1,400):
        d=k*0.025;v=occ(x+d*math.cos(a),y+d*math.sin(a))
        if v==0: return d
    return None


if __name__ == '__main__':
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from nav_msgs.msg import Odometry
    from tf2_msgs.msg import TFMessage
    r=rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=sys.argv[1],storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
    mo=None;od=None
    while r.has_next():
        t,d,ts=r.read_next()
        if t=='/tf':
            for tr in deserialize_message(d,TFMessage).transforms:
                if tr.header.frame_id=='map' and tr.child_frame_id=='odom':
                    mo=(tr.transform.translation.x,tr.transform.translation.y,yaw(tr.transform.rotation))
        elif t=='/odometry/filtered':
            m=deserialize_message(d,Odometry);od=(m.pose.pose.position.x,m.pose.pose.position.y,yaw(m.pose.pose.orientation))
    x,y,th=compose(mo,od)
    print('robot in map: x %.3f y %.3f yaw %.1f deg'%(x,y,math.degrees(th)))
    ox,oy=origin(open(sys.argv[2]).read())
    w,h,px=pgm(open(sys.argv[3],'rb').read())
    for name,off in [('left',90),('right',-90),('front',0),('back',180)]:
        print(name,ray(px,w,h,ox,oy,x,y,th+math.radians(off)))
    F=ray(px,w,h,ox,oy,x,y,th);B=ray(px,w,h,ox,oy,x,y,th+math.pi);print('map front+back',None if None in(F,B) else round(F+B,3))

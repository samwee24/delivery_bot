import sys, math, rosbag2_py
from rclpy.serialization import deserialize_message
from nav_msgs.msg import Odometry
from tf2_msgs.msg import TFMessage
r=rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=sys.argv[1],storage_id='mcap'),rosbag2_py.ConverterOptions('cdr','cdr'))
mo=None;od=None
def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
while r.has_next():
    t,d,ts=r.read_next()
    if t=='/tf':
        for tr in deserialize_message(d,TFMessage).transforms:
            if tr.header.frame_id=='map' and tr.child_frame_id=='odom':
                mo=(tr.transform.translation.x,tr.transform.translation.y,yaw(tr.transform.rotation))
    elif t=='/odometry/filtered':
        m=deserialize_message(d,Odometry);od=(m.pose.pose.position.x,m.pose.pose.position.y,yaw(m.pose.pose.orientation))
c,s=math.cos(mo[2]),math.sin(mo[2])
x=mo[0]+c*od[0]-s*od[1];y=mo[1]+s*od[0]+c*od[1];th=mo[2]+od[2]
print('robot in map: x %.3f y %.3f yaw %.1f deg'%(x,y,math.degrees(th)))
yml=open(sys.argv[2]).read();import re
ox,oy=[float(v) for v in re.search(r'origin:\s*\[([^\]]+)\]',yml).group(1).split(',')[:2]]
pg=open(sys.argv[3],'rb').read();parts=pg.split(b'\n',3);w,h=map(int,parts[1].split());px=parts[3]
def occ(wx,wy):
    i=int((wx-ox)/0.05);j=int((wy-oy)/0.05)
    if not(0<=i<w and 0<=j<h): return None
    return px[(h-1-j)*w+i]
def ray(a):
    for k in range(1,400):
        d=k*0.025;v=occ(x+d*math.cos(a),y+d*math.sin(a))
        if v==0: return d
    return None
for name,off in [('left',90),('right',-90),('front',0),('back',180)]:
    print(name,ray(th+math.radians(off)))
F=ray(th);B=ray(th+math.pi);print('map front+back',None if None in(F,B) else round(F+B,3))

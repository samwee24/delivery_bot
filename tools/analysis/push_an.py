"""usage: push_an.py <bag> [t0 t1] [--sim]
Track of /odom_rf2o in a bag. With t0 t1 (s from the first message) also prints the straight-line
distance and yaw change over that window. --sim takes times from header.stamp instead of bag receive time."""
import sys, math


def window(P, t0, t1):
    """P: [(t_rel, x, y, yaw_rad)]. Straight-line odom-frame distance and wrapped yaw change (deg)
    between the samples nearest t0 and t1, and the number of samples inside [t0, t1]."""
    a = min(P, key=lambda p: abs(p[0] - t0))
    b = min(P, key=lambda p: abs(p[0] - t1))
    dyaw = math.degrees(math.atan2(math.sin(b[3] - a[3]), math.cos(b[3] - a[3])))
    n = sum(1 for p in P if t0 <= p[0] <= t1)
    return math.hypot(b[1] - a[1], b[2] - a[2]), dyaw, n


if __name__ == '__main__':
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from nav_msgs.msg import Odometry
    args = [a for a in sys.argv[1:] if a != '--sim']
    sim = '--sim' in sys.argv
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=args[0], storage_id='mcap'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
    P = []
    while r.has_next():
        t, d, ts = r.read_next()
        if t == '/odom_rf2o':
            m = deserialize_message(d, Odometry); q = m.pose.pose.orientation
            if sim:
                ts = m.header.stamp.sec * 1_000_000_000 + m.header.stamp.nanosec
            P.append((ts * 1e-9, m.pose.pose.position.x, m.pose.pose.position.y, math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))))
    t0, x0, y0, h0 = P[0]; c, s = math.cos(-h0), math.sin(-h0)
    Q = [(t - t0, (x - x0) * c - (y - y0) * s, (x - x0) * s + (y - y0) * c, math.degrees(h - h0)) for t, x, y, h in P]
    print('n', len(Q))
    for k in range(0, len(Q), max(1, len(Q) // 25)): print('%5.0fs x %6.3f y %6.3f yaw %6.1f' % Q[k])
    xs = [q[1] for q in Q]; i = xs.index(min(xs)); print('min x', round(min(xs), 3), 'at', round(Q[i][0]), 's; max x', round(max(xs), 3), '; final', [round(v, 3) for v in Q[-1][1:]])
    print('forward leg: from min x', round(xs[-1] - min(xs), 3), 'm; lateral at end vs at min', round(Q[-1][2] - Q[i][2], 3), 'yaw change', round(Q[-1][3] - Q[i][3], 1))
    if len(args) >= 3:
        w0, w1 = float(args[1]), float(args[2])
        dist, dyaw, n = window([(p[0] - t0, p[1], p[2], p[3]) for p in P], w0, w1)
        print('window %g-%g s: dist %.3f m, yaw change %.1f deg, n %d' % (w0, w1, dist, dyaw, n))

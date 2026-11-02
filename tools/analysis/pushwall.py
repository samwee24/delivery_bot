"""usage: pushwall.py <bag> [t_start t_end]
Per-bag push check, times in s from the first /scan. Prints every ~1 s: median /scan range at 0 and 180 deg
(scanchk.med over the scans in that second), /odom_rf2o x (rotated into its start frame) and rear points
(<1.2 m, |angle|>135 deg). With t_start t_end also prints rf2o straight-line distance over that window
(push_an.window) and the wall-range change at 0 and 180 deg between the second before t_start and the second after t_end."""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scanchk import med
from push_an import window

if __name__ == '__main__':
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from sensor_msgs.msg import LaserScan
    from nav_msgs.msg import Odometry
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=sys.argv[1], storage_id='mcap'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
    S, P = [], []
    while r.has_next():
        t, d, ts = r.read_next()
        if t == '/scan': S.append((ts * 1e-9, deserialize_message(d, LaserScan)))
        elif t == '/odom_rf2o':
            m = deserialize_message(d, Odometry); q = m.pose.pose.orientation
            P.append((ts * 1e-9, m.pose.pose.position.x, m.pose.pose.position.y,
                      math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))))
    T0 = S[0][0]
    S = [(t - T0, m) for t, m in S]
    P = [(t - T0,) + p[1:] for t, p in ((p[0], p) for p in P)]

    def rear(m):
        return sum(1 for i, v in enumerate(m.ranges) if math.isfinite(v) and 0.1 < v < 1.2
                   and abs(math.degrees(m.angle_min + i * m.angle_increment)) > 135)

    def sec(a, b): return [s for s in S if a <= s[0] < b]
    for k in range(int(S[-1][0]) + 1):
        w = sec(k, k + 1)
        if not w: continue
        x = [p for p in P if k <= p[0] < k + 1]
        print('%3ds  front %s  back %s  rf2o n %d  rear pts median %d' % (
            k, med(w, 0), med(w, 180), len(x), sorted(rear(m) for _, m in w)[len(w) // 2]))
    if len(sys.argv) > 3:
        a, b = float(sys.argv[2]), float(sys.argv[3])
        dist, dyaw, n = window(P, a, b)
        f0, f1 = med(sec(a - 1, a), 0), med(sec(b, b + 1), 0)
        b0, b1 = med(sec(a - 1, a), 180), med(sec(b, b + 1), 180)
        print('window %g-%g s: rf2o dist %.3f m yaw %.1f deg n %d; front %s -> %s; back %s -> %s' % (a, b, dist, dyaw, n, f0, f1, b0, b1))
        rr = [rear(m) for _, m in sec(a, b)]
        print('rear pts in window: median %d max %d over %d scans' % (sorted(rr)[len(rr) // 2], max(rr), len(rr)) if rr else 'no scans')

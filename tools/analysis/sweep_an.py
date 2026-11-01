import glob, math, os, re, collections
for v in ['base','minrange0','noloop','travel005','travel020']:
    d=f'/tmp/sweep/{v}'
    if not os.path.exists(d+'/map.pgm'): print(v,'no map'); continue
    pg=open(d+'/map.pgm','rb').read();parts=pg.split(b'\n',3);w,h=map(int,parts[1].split());c=collections.Counter(parts[3])
    out=f'{v:10s} map {w}x{h} free {c[254]} occ {c[0]} occ/free {c[0]/max(c[254],1):.3f}'
    t=sorted(glob.glob(d+'/tum/slam_*.tum'))
    if t:
        L=[list(map(float,l.split())) for l in open(t[-1]) if l.strip()]
        a,b=L[0],L[-1];path=sum(math.hypot(L[i][1]-L[i-1][1],L[i][2]-L[i-1][2]) for i in range(1,len(L)))
        out+=f' | poses {len(L)} path {path:.1f} m closure {math.hypot(b[1]-a[1],b[2]-a[2]):.3f} m'
    lg=open(d+'/launch.log').read()
    out+=f" | rejected {len(re.findall('range readings',lg))} warn {len(re.findall(r'WARN',lg))}"
    print(out)

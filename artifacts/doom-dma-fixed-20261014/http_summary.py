#!/usr/bin/env python3
"""Match read-only HTTP receipts to saved PNGs; never claim browser paint timing."""
import hashlib,json,statistics,sys
from pathlib import Path
w=Path(sys.argv[1]);p=Path(sys.argv[2]);rows=[json.loads(l) for l in p.read_text().splitlines()]
by={}
for r in rows:
 name=r['frame'];assert hashlib.sha256((w/('play-'+name+'.png')).read_bytes()).hexdigest()==r['sha256'];by[int(name.rsplit('-',1)[1])]=r
blocks=[]
for a,b in ((5,10),(11,16),(17,22),(23,28)):
 selected=[i for i in range(a,b+1) if i in by]
 blocks.append(dict(first=a,last=b,observed=selected,fps=(len(selected)-1)/(by[selected[-1]]['received']-by[selected[0]]['received']) if len(selected)>1 else None))
print(json.dumps(dict(frames=len(rows),matching_named_pngs=len(by),mean_fetch_seconds=statistics.mean(r['fetch_seconds'] for r in rows),blocks=blocks,measurement='HTTP receipt, 250 ms polling; not browser paint'),indent=2))

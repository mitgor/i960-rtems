#!/usr/bin/env python3
import hashlib,json,statistics,sys
from pathlib import Path
live=Path(sys.argv[1]);rows=[json.loads(x) for x in Path(sys.argv[2]).read_text().splitlines()];by={}
for r in rows:
 g=int(r['frame'].split('-')[1]);packet=(live/f'play-{r["frame"]}.dfb').read_bytes()
 assert hashlib.sha256(packet).hexdigest()==r['sha256'] and hashlib.sha256(packet[32:]).hexdigest()==r['payload_sha256']
 assert g not in by;by[g]=r
blocks=[]
for a,b in ((5,16),(17,28),(29,40),(41,52)):
 selected=[g for g in range(a,b+1) if g in by]
 blocks.append(dict(first=a,last=b,observed=selected,fps=(len(selected)-1)/(by[selected[-1]]['received']-by[selected[0]]['received']) if len(selected)>1 else None))
print(json.dumps(dict(matching_packets=len(rows),missing_frames=sorted(set(range(1,53))-set(by)),mean_fetch_seconds=statistics.mean(r['fetch_seconds'] for r in rows),blocks=blocks,measurement='HTTP receipt with 50 ms polling; not browser paint FPS'),indent=2))

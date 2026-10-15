#!/usr/bin/env python3
"""Model larger direct-mapped caches from the accepted one-window miss stream.
This is a trace estimate, not a native-engine or physical cache benchmark.
"""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
requests=sorted((json.loads(x) for x in (a.capture/'wad-ring-results.jsonl').read_text().splitlines()),key=lambda r:r['sequence'])
frames=[json.loads(x) for x in (a.capture/'play-frames.jsonl').read_text().splitlines()]
lo,hi=frames[65]['wad_requests'],frames[67]['wad_requests'];out=[]
for windows in (1,2,4,8):
 cache={};misses=restart=0
 for row in requests:
  off=row['offset']
  if off%65536:continue
  slot=(off//65536)%windows
  if cache.get(slot)!=off:
   cache[slot]=off;misses+=1;restart+=lo<row['sequence']<=hi
 out.append(dict(windows=windows,cache_bytes=windows*65536,window_misses=misses,restart_window_misses=restart))
print(json.dumps(dict(kind='trace estimate, not physical acceptance',profiles=out),indent=2))

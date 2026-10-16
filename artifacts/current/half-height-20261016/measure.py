#!/usr/bin/env python3
"""Predeclared eight matched windows: A/B/C/D/D/C/B/A, after level reload."""
import json,statistics,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();r=a.capture
frames=list(map(json.loads,(r/'play-frames.jsonl').read_text().splitlines()))
published={x['frame']:x for x in map(json.loads,(r/'browser-publish.jsonl').read_text().splitlines())}
assert len(frames)==920
blocks=[]
for k,(name,h,flat) in enumerate([('A1',0,0),('B1',1,0),('C1',1,1),('D1',0,1),('D2',0,1),('C2',1,1),('B2',1,0),('A2',0,0)]):
 start=161+k*100;end=start+57;f=frames[start-1:end]
 assert all(x['profile']['half_height']==h and x['profile']['flat_planes']==flat for x in f)
 elapsed=f[-1]['seconds']-f[0]['seconds'];dt=published[end]['published']-published[start]['published']
 row=dict(name=name,half=h,flat=flat,first=start,last=end,frames=len(f),intervals=len(f)-1,elapsed_seconds=elapsed,fps=(len(f)-1)/elapsed,http_fps=(len(f)-1)/dt)
 row.update({key:statistics.mean(x['profile'][key] for x in f) for key in ('render_ms','planes_ms','bsp_ms','sprites_ms','screen_copy_ms')})
 row.update(renderer_cpu_ms=10*statistics.mean(x['profile']['cpu_samples']['render'] for x in f),observed_to_http_ms=1000*statistics.mean(published[x['frame']]['published']-published[x['frame']]['observed'] for x in f))
 blocks.append(row)
groups={}
for name,h,flat in [('normal',0,0),('half',1,0),('half_flat',1,1),('flat',0,1)]:
 b=[x for x in blocks if (x['half'],x['flat'])==(h,flat)]
 groups[name]={k:statistics.mean(x[k] for x in b) for k in ('render_ms','planes_ms','bsp_ms','sprites_ms','screen_copy_ms','renderer_cpu_ms','observed_to_http_ms')}
 groups[name]['fps']=sum(x['intervals'] for x in b)/sum(x['elapsed_seconds'] for x in b)
for name in groups:groups[name]['gain_vs_normal_percent']=100*(groups[name]['fps']/groups['normal']['fps']-1)
print(json.dumps(dict(blocks=blocks,groups=groups,half_over_flat_percent=100*(groups['half_flat']['fps']/groups['flat']['fps']-1),caveat='One stationary low-horizontal-detail workload, same binary/session, all full audits; not all levels or input-to-paint latency.'),indent=2))

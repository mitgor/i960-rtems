#!/usr/bin/env python3
"""Predeclared within-session textured/flat/flat/textured steady windows."""
import json,statistics,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();r=a.capture
frames=[json.loads(x) for x in (r/'play-frames.jsonl').read_text().splitlines()]
published={x['frame']:x for x in map(json.loads,(r/'browser-publish.jsonl').read_text().splitlines())}
assert len(frames)==520
blocks=[]
for name,start,end,mode in [('A1',141,218,0),('B1',241,318,1),('B2',341,418,1),('A2',441,518,0)]:
 f=frames[start-1:end];assert all(x['profile']['flat_planes']==mode for x in f)
 elapsed=f[-1]['seconds']-f[0]['seconds'];dt=published[end]['published']-published[start]['published']
 blocks.append(dict(name=name,mode=mode,first=start,last=end,frames=len(f),intervals=len(f)-1,elapsed_seconds=elapsed,fps=(len(f)-1)/elapsed,http_fps=(len(f)-1)/dt,renderer_ms=statistics.mean(x['profile']['render_ms'] for x in f),planes_ms=statistics.mean(x['profile']['planes_ms'] for x in f),bsp_ms=statistics.mean(x['profile']['bsp_ms'] for x in f),sprites_ms=statistics.mean(x['profile']['sprites_ms'] for x in f),renderer_cpu_ms=10*statistics.mean(x['profile']['cpu_samples']['render'] for x in f),planes_cpu_ms=10*statistics.mean(x['profile']['cpu_samples']['planes'] for x in f),observed_to_http_ms=1000*statistics.mean(published[x['frame']]['published']-published[x['frame']]['observed'] for x in f)))
groups={}
for name,mode in [('textured',0),('flat',1)]:
 b=[x for x in blocks if x['mode']==mode];groups[name]={k:statistics.mean(x[k] for x in b) for k in ('renderer_ms','planes_ms','bsp_ms','sprites_ms','renderer_cpu_ms','planes_cpu_ms','observed_to_http_ms')};groups[name]['fps']=sum(x['intervals'] for x in b)/sum(x['elapsed_seconds'] for x in b)
print(json.dumps(dict(blocks=blocks,groups=groups,fps_gain_percent=100*(groups['flat']['fps']/groups['textured']['fps']-1),caveat='One session and one stationary workload; full audits remain active. Cross-session/general-level performance not established.'),indent=2))

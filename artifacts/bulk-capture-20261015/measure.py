#!/usr/bin/env python3
"""Transport cost comparison, retaining all frames in the predeclared window."""
import argparse,hashlib,json,statistics,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--http',type=Path);a=p.parse_args()
def measure(path):
 rows=lambda n:[json.loads(x) for x in (path/n).read_text().splitlines()]
 frames=rows('play-frames.jsonl');assert len(frames)==100
 costs={};captures={}
 for e in rows('pingpong-journal.jsonl'):
  if 'errno' in e:continue
  op,epoch,g,off=struct.unpack_from('<4I',bytes.fromhex(e['request']))
  if 21<=g<=50:
   costs.setdefault(str(op),[]).append(e['ns']/1e6)
   if op in (3,8):captures.setdefault(g,[]).append(e['ns']/1e6)
 assert set(captures)==set(range(21,51))
 f=frames[20:50]
 return dict(fps=29/(frames[49]['seconds']-frames[20]['seconds']),capture_calls_per_frame=sorted(set(map(len,captures.values()))),capture_ioctl_mean_ms=statistics.mean(sum(v) for v in captures.values()),ready_to_release_mean_ms=1000*statistics.mean(x['ready_to_release_seconds'] for x in f),operations={k:dict(calls=len(v),mean_ms=statistics.mean(v)) for k,v in costs.items()})
b=measure(a.baseline);c=measure(a.candidate)
result=dict(baseline=b,candidate=c,fps_change_percent=100*(c['fps']/b['fps']-1),capture_ioctl_reduction_percent=100*(1-c['capture_ioctl_mean_ms']/b['capture_ioctl_mean_ms']),ready_to_release_reduction_percent=100*(1-c['ready_to_release_mean_ms']/b['ready_to_release_mean_ms']))
assert b['capture_calls_per_frame']==[72] and c['capture_calls_per_frame']==[1]
if a.http:
 rows=[json.loads(x) for x in a.http.read_text().splitlines()]
 for r in rows:
  session,g=map(int,r['frame'].split('-'));b=(a.candidate/f'play-{session}-{g}.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==r['payload_sha256']
 result['http_exact_frames']=len(rows)
print(json.dumps(result,indent=2))

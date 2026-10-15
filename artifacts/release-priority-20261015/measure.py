#!/usr/bin/env python3
import argparse,bisect,json,statistics,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path,nargs='+');a=p.parse_args()
result={}
def summary(v):
 v=sorted(v);return dict(mean=statistics.mean(v),p50=statistics.median(v),p95=v[int((len(v)-1)*.95)],max=max(v))
for out in a.captures:
 rows=lambda n:[json.loads(s) for s in (out/n).read_text().splitlines()]
 audit=rows('audit-gate.jsonl');starts=[r['acquired_ns'] for r in audit]
 def overlap(r):
  start,end=r['start_ns'],r['acquired_ns'];i=max(0,bisect.bisect_right(starts,start)-1);total=0
  while i<len(audit) and audit[i]['acquired_ns']<end:
   total+=max(0,min(end,audit[i]['end_ns'])-max(start,audit[i]['acquired_ns']));i+=1
  return total/1e6
 clocks=json.loads((out/'doom-pingpong-result.json').read_text())['clocks']
 windows=[(max(x['before']-(x['card_ms']+10)/1000 for x in batch),min(x['after']-x['card_ms']/1000 for x in batch)) for batch in clocks]
 assert all(lo<=hi for lo,hi in windows)
 offset_lo=min(x[0] for x in windows);offset_hi=max(x[1] for x in windows)
 frames={r['frame']:r for r in rows('play-frames.jsonl')};pub={r['frame']:r for r in rows('browser-publish.jsonl')};releases={}
 for r in rows('pingpong-journal.jsonl'):
  if 'request' in r:
   op,e,g,off=struct.unpack_from('<4I',bytes.fromhex(r['request']))
   if op==4:assert g not in releases;releases[g]=r
 blocks=[]
 for first,last in ((100,199),(200,299),(300,399),(400,499)):
  f=[frames[g] for g in range(first,last+1)];rr=[releases[g] for g in range(first,last+1)];pp=[pub[g] for g in range(first,last+1)]
  policy=f[0]['release_priority'];assert all(x['release_priority']==policy for x in f+rr)
  blocks.append(dict(first=first,last=last,priority=policy,host_fps=99/(f[-1]['seconds']-f[0]['seconds']),publication_fps=99000/(f[-1]['marker'][5]-f[0]['marker'][5]),card_start_to_browser_mean_bounds_ms=[statistics.mean(1000*max(0,pub[x["frame"]]["published"]-x["marker"][5]/1000-offset_hi-.010) for x in f),statistics.mean(1000*(pub[x["frame"]]["published"]-x["marker"][5]/1000-offset_lo) for x in f)],browser_publish_fps=99/(pp[-1]['published']-pp[0]['published']),audit_overlap_ms=summary([overlap(x) for x in rr]),gate_wait_ms=summary([x['gate_wait_ns']/1e6 for x in rr]),ioctl_ms=summary([x['ioctl_ns']/1e6 for x in rr]),observed_to_browser_ms=summary([1000*(x['published']-x['observed']) for x in pp]),observed_to_release_ms=summary([1000*x['ready_to_release_seconds'] for x in f]),renderer_components_ms={k:statistics.mean(x['profile'][k] for x in f) for k in ('bsp_ms','planes_ms','sprites_ms','screen_copy_ms','adapter_ms','previous_publish_wait_ms')},render_cpu_sample_ms=statistics.mean(10*x['profile']['cpu_samples']['render'] for x in f),render_ms=summary([x['profile']['render_ms'] for x in f])))
 result[out.name]=blocks
pooled={}
for policy in (False,True):
 b=[b for blocks in result.values() for b in blocks if b['priority']==policy]
 if not b:continue
 pooled[str(policy)]=dict(blocks=len(b),host_fps=len(b)/sum(1/x['host_fps'] for x in b),publication_fps=len(b)/sum(1/x['publication_fps'] for x in b),gate_wait_mean_ms=statistics.mean(x['gate_wait_ms']['mean'] for x in b),ioctl_mean_ms=statistics.mean(x['ioctl_ms']['mean'] for x in b),observed_to_browser_mean_ms=statistics.mean(x['observed_to_browser_ms']['mean'] for x in b),render_mean_ms=statistics.mean(x['render_ms']['mean'] for x in b))
print(json.dumps(dict(runs=result,pooled=pooled),indent=2))

#!/usr/bin/env python3
"""Compare optional peer scheduling against the accepted screen-copy baseline."""
import argparse, json, statistics, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--native',required=True,type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[2]
x=json.loads(subprocess.check_output([sys.executable,str(root/'artifacts/wad-ring-20261015/analyze.py'),str(a.baseline),str(a.candidate),'--native',str(a.native)]))
b,c=x[a.baseline.name],x[a.candidate.name]
for k in ('first_frame_requests','total_requests','warm_restart_requests'):assert b[k]==c[k],(k,b[k],c[k])
profiles=[json.loads(subprocess.check_output([sys.executable,str(root/'rtems/dma/wad_ring/verify_profile.py'),str(q)])) for q in (a.baseline,a.candidate)]
assert profiles[0]['final_cache']['wire_bytes']==profiles[1]['final_cache']['wire_bytes']
assert profiles[0]['final_cache']['copied_bytes']==profiles[1]['final_cache']['copied_bytes']
result=dict(runs=x,improvement={k:dict(before=b[k],after=c[k],reduction_percent=100*(1-c[k]/b[k]),speedup=b[k]/c[k]) for k in ('first_frame_seconds','warm_restart_seconds')},cache_seconds={q.name:v['final_cache']['seconds'] for q,v in zip((a.baseline,a.candidate),profiles)},warm_restart_cache_ms={q.name:v['warm_restart_cache_ms'] for q,v in zip((a.baseline,a.candidate),profiles)},fps_percent_change=100*(c['pingpong_fps']/b['pingpong_fps']-1))
result['scheduler']={q.name:{k:v[k] for k in ('peer_yield','peer_max_gap_ms','peer_completed_passes')} for q,v in zip((a.baseline,a.candidate),profiles)}
result['steady_profile']={}
for capture in (a.baseline,a.candidate):
 rows=[json.loads(l) for l in (capture/'play-frames.jsonl').read_text().splitlines()][20:50]
 result['steady_profile'][capture.name]={k:statistics.mean(r['profile'][k] for r in rows) for k in ('render_ms','bsp_ms','planes_ms','sprites_ms','screen_copy_ms','adapter_ms','previous_publish_wait_ms','display_ms')}
 result['steady_profile'][capture.name]['first_frame_previous_wait_ms']=rows[0]['profile']['previous_publish_wait_ms']
 result['steady_profile'][capture.name]['previous_wait_ms_frames_22_50']=statistics.mean(r['profile']['previous_publish_wait_ms'] for r in rows[1:])
 result['steady_profile'][capture.name]['cpu_sample_ms']={k:10*statistics.mean(r['profile']['cpu_samples'][k] for r in rows) for k in ('render','screen_copy','adapter')}
print(json.dumps(result,indent=2))

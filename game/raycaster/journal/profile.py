#!/usr/bin/env python3
"""Compare ABBA browser sessions, preserving each pacing class separately."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('reports',type=Path);a=p.parse_args()
sessions=[]
for name,mode in [('a1','rewrite'),('b1','journal'),('b2','journal'),('a2','rewrite')]:
 cap=a.root/('live-'+name)
 phases=json.loads((cap/'phases.json').read_text())
 times=[json.loads(line) for line in (cap/'metadata-timing.jsonl').read_text().splitlines()]
 assert len(times)==len(phases) and [r['sequence'] for r in times]==list(range(1,len(times)+1))
 values=[(r['intent_ns']+r['result_ns'])/1e6 for r in times]
 profile=json.loads((a.reports/('profile-'+name+'.json')).read_text())
 sessions.append(dict(name=name,mode=mode,requests=len(times),metadata_mean_ms=statistics.mean(values),metadata_first50_ms=statistics.mean(values[:50]),metadata_last50_ms=statistics.mean(values[-50:]),command_archive_mean_ms=statistics.mean(r['commands_ns']/1e6 for r in times),browser=profile))
result=dict(sessions=sessions,comparison={})
for pacing in ('legacy-delay','raf-single-flight'):
 modes={}
 for mode in ('rewrite','journal'):
  rows=[r for r in sessions if r['mode']==mode]
  interval=statistics.mean(r['browser']['pacing'][pacing]['draw_interval_ms']['mean'] for r in rows)
  modes[mode]=dict(mean_draw_interval_ms=interval,fps=1000/interval,metadata_ms=statistics.mean(r['metadata_mean_ms'] for r in rows),commands_ms=statistics.mean(r['command_archive_mean_ms'] for r in rows))
 modes['fps_improvement_percent']=(modes['journal']['fps']/modes['rewrite']['fps']-1)*100
 result['comparison'][pacing]=modes
print(json.dumps(result,indent=2))

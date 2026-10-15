#!/usr/bin/env python3
"""Compare identical frame positions with priority enabled in both builds."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('fast',type=Path);a=p.parse_args()
b=json.loads(a.baseline.read_text());f=json.loads(a.fast.read_text());old=[x for run in b['runs'].values() for x in run if x['priority']];new=list(f['runs'].values())[0]
assert sorted(x['first'] for x in old)==[100,200,300,400] and [x['first'] for x in new]==[100,200,300,400] and all(x['priority'] for x in new)
def aggregate(rows):
 return dict(host_fps=len(rows)/sum(1/x['host_fps'] for x in rows),publication_fps=len(rows)/sum(1/x['publication_fps'] for x in rows),renderer_ms=statistics.mean(x['render_ms']['mean'] for x in rows),render_cpu_sample_ms=statistics.mean(x['render_cpu_sample_ms'] for x in rows),components_ms={k:statistics.mean(x['renderer_components_ms'][k] for x in rows) for k in rows[0]['renderer_components_ms']},observed_to_browser_ms=statistics.mean(x['observed_to_browser_ms']['mean'] for x in rows))
x,y=aggregate(old),aggregate(new)
print(json.dumps(dict(baseline_priority=x,fast_memory_priority=y,host_fps_improvement_percent=100*(y['host_fps']/x['host_fps']-1),publication_fps_improvement_percent=100*(y['publication_fps']/x['publication_fps']-1),renderer_reduction_percent=100*(1-y['renderer_ms']/x['renderer_ms']),paired_blocks=[dict(first=n['first'],before=next(o['host_fps'] for o in old if o['first']==n['first']),after=n['host_fps']) for n in new]),indent=2))

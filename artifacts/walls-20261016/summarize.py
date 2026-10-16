#!/usr/bin/env python3
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);a=p.parse_args();r=Path(__file__).resolve().parent
rows=[]
for name in ('p0','a1','b1','b2','a2'):
 s=json.loads((r/name/(name+'-system.json')).read_text());f=json.loads((r/name/(name+'-frames.json')).read_text());c=a.captures/('live-'+name)
 rows.append(dict(run=name,frames=520,paired_audits=len(json.loads((c/'snapshots.json').read_text())),irq_max_gap_us=s['heap_diagnostics']['irq_max_gap_us'],held_stop=f['held_stop'],stall=json.loads((c/'doom-pingpong-stall.json').read_text()),heap_allocations_freed=s['heap_allocations_freed']))
print(json.dumps(dict(runs=rows,total_frames=sum(x['frames'] for x in rows),total_audits=sum(x['paired_audits'] for x in rows)),indent=2))

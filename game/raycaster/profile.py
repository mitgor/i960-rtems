#!/usr/bin/env python3
"""Summarize measured host phases; benchmark slopes are estimates, not CPU cycles."""
import argparse,json,statistics
from collections import defaultdict
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('phases',type=Path);a=p.parse_args()
rows=json.loads(a.phases.read_text());groups=defaultdict(list)
for row in rows:
 assert sum(row[k] for k in ['upload_ns','arm_ns','execute_ns','verify_ns','audit_ns'])==row['kernel_ns']
 # First callback includes RTEMS initialization and is not a steady-state sample.
 if row['sequence']>1:groups[row['label']].append(row)
summary={}
for name,values in groups.items():
 summary[name]=dict(n=len(values),**{key.replace('_ns','_ms'):statistics.median(v[key] for v in values)/1e6 for key in ['upload_ns','arm_ns','execute_ns','verify_ns','audit_ns','kernel_ns','wall_ns']},min_execute_ms=min(v['execute_ns'] for v in values)/1e6,max_execute_ms=max(v['execute_ns'] for v in values)/1e6)
def fit(points):
 xs=[x for x,y in points];ys=[y for x,y in points];mx=statistics.mean(xs);my=statistics.mean(ys)
 slope=sum((x-mx)*(y-my) for x,y in points)/sum((x-mx)**2 for x in xs)
 residual=sum((y-(my+slope*(x-mx)))**2 for x,y in points);total=sum((y-my)**2 for y in ys)
 return slope,1-residual/total if total else 0
names=['empty','memcpy4096-aligned','memcpy4096-unaligned','memset4096','memmove4096-overlap','memcmp4096-equal','strlen4095','semaphore-roundtrip','rtems-clock-tick']
base={r:summary[f'bench0x{r}']['execute_ms'] for r in (1,16,64,128)}
bench={}
for k in range(1,9):
 points=[(r,summary[f'bench{k}x{r}']['execute_ms']-base[r]) for r in (1,16,64,128)]
 slope,r2=fit(points)
 bench[names[k]]=dict(estimated_us_per_operation=slope*1000,fit_r_squared=r2,points_ms=points,resolved=slope>0 and r2>=0.9)
 if k<=6 and slope>0:bench[names[k]]['estimated_MiB_per_s']=(4095 if k==6 else 4096)/(1024*1024)/(slope/1000)
render=summary['render80'];snapshot=summary['snapshot4864']
print(json.dumps(dict(samples=len(rows),phases=summary,benchmarks=bench,render_increment_over_snapshot_ms=render['execute_ms']-snapshot['execute_ms'],frame_payload_bytes=4800,ordinary_paired_audit_bytes=2*471136,full_paired_audit_bytes=2*524288,limitations='Host command interval includes firmware dispatch, polling and validation overhead; differential slopes use warm repeated buffers. No cycle counter, CPU frequency or raw PCI bandwidth claim.'),indent=2))

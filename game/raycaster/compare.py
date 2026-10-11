#!/usr/bin/env python3
"""Compare independent raycaster profile reports; preserve individual runs."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--byte',type=Path,nargs='+',required=True)
p.add_argument('--word',type=Path,nargs='+',required=True)
a=p.parse_args()
byte=[json.loads(p.read_text()) for p in a.byte]
word=[json.loads(p.read_text()) for p in a.word]
def metric(getter):
 b=[getter(r) for r in byte];w=[getter(r) for r in word]
 before=statistics.median(b);after=statistics.median(w)
 return dict(byte_runs=b,word_runs=w,byte_median=before,word_median=after,
             reduction_percent=(1-after/before)*100,speedup=before/after)
out={'method':'Median of independent session medians/slopes; no CPU-cycle or isolated PCI-bandwidth claim.',
     'byte_reports':[p.name for p in a.byte],'word_reports':[p.name for p in a.word],
     'phases':{},'benchmarks':{}}
for name in ['render80','render10','snapshot64','snapshot4864']:
 out['phases'][name]={key:metric(lambda r,n=name,k=key:r['phases'][n][k])
   for key in ['upload_ms','arm_ms','execute_ms','verify_ms','audit_ms','kernel_ms','wall_ms']}
out['render_increment_ms']=metric(lambda r:r['render_increment_over_snapshot_ms'])
for name in byte[0]['benchmarks']:
 assert all(r['benchmarks'][name]['resolved'] for r in byte+word),name
 out['benchmarks'][name]=metric(lambda r,n=name:r['benchmarks'][n]['estimated_us_per_operation'])
print(json.dumps(out,indent=2))

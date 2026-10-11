#!/usr/bin/env python3
"""Combined upload wait per frame, avoiding sums of independent medians."""
import argparse,gzip,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);a=p.parse_args();runs={}
for name in ['base1','fast1','fast2','base2']:
 cap=a.captures/('live-'+name);phases=json.loads((cap/'phases.json').read_text())
 with gzip.open(cap/'commands.jsonl.gz','rt') as f:rows=[json.loads(x) for x in f]
 values=[]
 for phase,row in zip(phases,rows):
  assert phase['sequence']==row['sequence']
  if phase['label']=='render80':
   commands=[r for r in row['commands'] if r['op']==0x21];assert len(commands)==3
   values.append(sum(r['wait'] for r in commands)/1e6)
 runs[name]=dict(n=len(values),median_ms=statistics.median(values),min_ms=min(values),max_ms=max(values))
x=statistics.median(runs[n]['median_ms'] for n in ['base1','base2'])
y=statistics.median(runs[n]['median_ms'] for n in ['fast1','fast2'])
print(json.dumps(dict(runs=runs,baseline_ms=x,optimized_ms=y,reduction_percent=100*(1-y/x),ratio=x/y),indent=2))

#!/usr/bin/env python3
"""Diagnostic slopes and paired-session medians; no unaudited FPS estimate."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);p.add_argument('--baseline-only',action='store_true');a=p.parse_args();med=statistics.median
result={'diagnostics':{},'release':{}}
for mode in ['byte'] if a.baseline_only else ['byte','hash','words']:
 rows=json.loads((a.captures/('live-bench-'+mode)/'phases.json').read_text());data={}
 for which,name in [(1,'hash'),(2,'validation')]:
  counts=[0,1,4,8,16,32];points=[med(r['execute_ns']/1e6 for r in rows if r['label']==f'bench-{which}-{n}') for n in counts]
  mx=statistics.mean(counts);my=statistics.mean(points);slope=sum((x-mx)*(y-my) for x,y in zip(counts,points))/sum((x-mx)**2 for x in counts)
  intercept=my-slope*mx;residual=max(abs(y-(intercept+slope*x)) for x,y in zip(counts,points))
  data[name]=dict(counts=counts,median_execute_ms=points,ms_per_repeat=slope,intercept_ms=intercept,max_fit_residual_ms=residual)
 data['validation_minus_hash_ms']=data['validation']['ms_per_repeat']-data['hash']['ms_per_repeat'];result['diagnostics'][mode]=data
if not a.baseline_only:
 for mode in ['base','hash','words']:
  sessions=[]
  for suffix in ('1','2'):
   rows=json.loads((a.captures/('live-'+mode+suffix)/'phases.json').read_text());chosen=[r for r in rows if r['label']=='steady-combined'];assert len(chosen)==80
   sessions.append({k.replace('_ns','_ms'):med(r[k] for r in chosen)/1e6 for k in ['execute_ns','audit_ns','targeted_ns','full_audit_ns','kernel_ns','wall_ns','cpu_ns']})
  result['release'][mode]=dict(sessions_ms=sessions,median_ms={k:med(s[k] for s in sessions) for k in sessions[0]})
 base=result['release']['base']['median_ms']
 for mode in ['hash','words']:result['release'][mode]['reduction_percent']={k:100*(1-v/base[k]) for k,v in result['release'][mode]['median_ms'].items()}
result['limits']='Diagnostic slopes include loop/check overhead with warmed repeated data; residual validation-minus-hash is an estimate. Release targets contain no diagnostic opcode. Full paired audits retained on every request; host times are not target cycles or browser FPS.'
print(json.dumps(result,indent=2))

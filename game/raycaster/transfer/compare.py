#!/usr/bin/env python3
"""Compare repeated transport profiles with one unchanged target payload."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args()
load=lambda run,suffix:json.loads((a.artifacts/(run+'-'+suffix+'.json')).read_text())
base=[load(n,'profile') for n in ['base1','base2']];fast=[load(n,'profile') for n in ['fast1','fast2']]
def metric(b,f):
 x=statistics.median(b);y=statistics.median(f)
 return dict(baseline_runs=b,optimized_runs=f,baseline=x,optimized=y,reduction_percent=100*(1-y/x))
phases={label:{key:metric([r['phases'][label][key] for r in base],[r['phases'][label][key] for r in fast]) for key in ['upload_ms','arm_ms','execute_ms','verify_ms','audit_ms','kernel_ms','wall_ms']} for label in ['render80','render10','snapshot64','snapshot4864']}
bc=[load(n,'commands') for n in ['base1','base2']];fc=[load(n,'commands') for n in ['fast1','fast2']]
cmd={kind:{key:metric([r['render80'][kind][key] for r in bc],[r['render80'][kind][key] for r in fc]) for key in ['wait_ms','scan_ms','total_ms']} for kind in bc[0]['render80']}
print(json.dumps(dict(method='Median of two session medians, baseline/optimized/optimized/baseline order; same target and requests.',phases=phases,commands=cmd,unattributed_kernel_ms=metric([r['median_unattributed_kernel_ms'] for r in bc],[r['median_unattributed_kernel_ms'] for r in fc]),release=load('release','profile')['phases']['render80']),indent=2))

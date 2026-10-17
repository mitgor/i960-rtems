#!/usr/bin/env python3
"""Compare the predeclared first 32 generations of identical benchmark images."""
import argparse,json,statistics
from pathlib import Path
from verify import verify,NAMES
p=argparse.ArgumentParser();p.add_argument('old',type=Path);p.add_argument('new',type=Path);a=p.parse_args()
def rows(path):
 values=[verify(f.read_bytes()) for f in sorted(path.glob('frame-*.bin'))]
 values=[r for r in values if r['generation']<=32]
 assert [r['generation'] for r in values]==list(range(1,33))
 assert len({tuple(r['logical_registers']) for r in values})==1
 assert len({r['dcache_status'] for r in values})==1
 return values
old,new=rows(a.old),rows(a.new)
out=[]
for k in range(8):
 o=[r['ms'] for r in old if r['case']==k];n=[r['ms'] for r in new if r['case']==k]
 assert len(o)==len(n)==4
 om,nm=statistics.median(o),statistics.median(n)
 out.append(dict(case=k,name=NAMES[k],old_ms=o,new_ms=n,old_median_ms=om,new_median_ms=nm,speedup=om/nm))
print(json.dumps(dict(window=[1,32],old_cache=old[0],new_cache=new[0],cases=out,warning='Diagnostic workloads; not gameplay FPS or pure bus bandwidth.'),indent=2))

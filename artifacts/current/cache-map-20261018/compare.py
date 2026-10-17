#!/usr/bin/env python3
"""Compare identical admitted engine workloads before and after private mapping."""
import argparse,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'game/doom/runtime/cache_bench'))
from verify import verify,NAMES
p=argparse.ArgumentParser()
p.add_argument('uncached',type=Path,help='N1 32-frame live-frames directory')
p.add_argument('cached',type=Path,help='new 32-frame live-frames directory')
a=p.parse_args()
def records(path):
 rows=[]
 for n in range(1,33):
  data=(path/f'frame-{n:04d}.bin').read_bytes()
  r=verify(data)
  assert r['generation']==n
  rows.append(r)
 return rows
uncached,cached=records(a.uncached),records(a.cached)
assert all(not r['cache']['effective_cache_enabled'] for r in uncached)
assert all(r['cache']['effective_cache_enabled'] and r['cache']['template_matches']==1 for r in cached)
assert {tuple(r['logical_registers']) for r in uncached}=={('0x0','0xc0000002','0xffc00001','0xc0400002','0xffe00001')}
assert {tuple(r['logical_registers']) for r in cached}=={('0x0','0xc0000002','0xffc00001','0xc0800002','0xff800001')}
assert all(r['dcache_status']==0x8221 for r in uncached+cached)
out=[]
for k,name in enumerate(NAMES):
 u=[r['ms'] for r in uncached if r['case']==k]
 c=[r['ms'] for r in cached if r['case']==k]
 assert len(u)==len(c)==4
 out.append(dict(case=k,name=name,uncached_ms=u,cached_ms=c,
                 uncached_median_ms=statistics.median(u),
                 cached_median_ms=statistics.median(c),
                 speedup=statistics.median(u)/statistics.median(c)))
print(json.dumps(dict(frames=32,uncached_map=uncached[0]['logical_registers'],
                      cached_map=cached[0]['logical_registers'],cases=out),indent=2))

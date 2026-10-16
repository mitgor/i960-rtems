#!/usr/bin/env python3
"""Check admitted metadata, linked symbols, protected object and frame trailers."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('workspace',type=Path);p.add_argument('--captures',type=Path);a=p.parse_args();result={}
for name,fast in [('build',False),('build-fast',True)]:
 b=a.workspace/name;m=json.loads((b/'admission/manifest.json').read_text())
 assert bool(m.get('fast_fixed_div'))==fast and not m.get('fixed_div_profile')
 for key in ('frame_profile','cpu_profile','wad_profile','low_detail','direct_frame','no_fnv'):assert m.get(key),key
 obj=b/'engine-cross/i960/doom-engine.o'
 nm=subprocess.check_output(['/home/mit/i960/tools/bin/i960-coff-nm',str(obj)],text=True)
 for symbol in ('_doom_div_profile','_doom_div_check','_doom_div_record'):assert symbol not in nm,symbol
 assert ('_doom_div_fast' in nm)==fast and ('_doom_div_unsigned' in nm)==fast
 side=hashlib.sha256((b/'engine-cross/i960/r_point_side.o').read_bytes()).hexdigest()
 assert side=='beb7a66306aef9fa8a0cb4c0e18e81524b337c05f640897282c3f8bedcc6dd1b'
 result[name]=dict(fast_fixed_div=fast,fixed_div_profile=False,profiling_symbols_absent=True,point_side_sha256=side,options={key:m.get(key) for key in ('frame_profile','cpu_profile','wad_profile','low_detail','direct_frame','no_fnv')})
if a.captures:
 for run in ('a1','b1','b2','a2'):
  c=a.captures/('live-'+run)
  for g in range(1,521):
   raw=(c/f'play-0-{g}.bin').read_bytes();assert len(raw)==65536 and not any(raw[65024:]),(run,g)
  result[run]=dict(frames=520,reserved_tails_zero=True)
print(json.dumps(result,indent=2))

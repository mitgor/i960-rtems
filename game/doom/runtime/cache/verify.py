#!/usr/bin/env python3
"""Replay saved host frame digests and relocation checks against tracked oracles."""
import argparse,hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
runs=a.root/'reserved-runs';rows=json.loads((runs/'results.json').read_text());assert [r['case'] for r in rows]==[f'p{p}-demo{d}-0' for p in (1,2) for d in (1,2,3)]
binary=hashlib.sha256((a.root/'reserved-native/host32/doom-profile').read_bytes()).hexdigest()
for r in rows:
 d=runs/r['case'];expected=json.loads((a.reference/r['case']/'sha256-frames.json').read_text());actual=json.loads((d/'sha256-frames.json').read_text())
 assert actual==expected and len(actual)==r['frames']==2100 and r['matches_reference'] and r['binary_sha256']==binary
 c=json.loads((d/'cache.json').read_text());assert c==r['cache'] and c['errors']==0 and c['reserved_image']==1048576 and c['arena_peak']+c['reserved_image']<8388608
 assert 'reserved engine=1048576' in r['drain']
link=json.loads((a.root/'accepted-link/inventory.json').read_text());assert link['imports_after']==44 and len(link['resolved'])==9 and not link['loadable'] and link['final_link_correctly_refused']
assert hashlib.sha256((a.root/'accepted-link/doom-runtime.o').read_bytes()).hexdigest()==link['runtime_sha256']
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'relocate'));from pack import rebase
obj=(a.root/'relocate/probe.o').read_bytes()
for base in (0x10000,0x200000,0xc02d0050):assert rebase(obj,base)[0]==(a.root/f'relocate/{base:x}.bin').read_bytes()
try:rebase((a.root/'accepted-link/doom-runtime.o').read_bytes(),0x200000)
except AssertionError as e:assert str(e)=='unresolved symbol'
else:raise AssertionError('incomplete engine admitted')
result=dict(frames=12600,reference_matches=True,binary_sha256=binary,peak_dynamic=max(r['cache']['arena_peak'] for r in rows),image_reserved=1048576,peak_plus_image=max(r['cache']['arena_peak'] for r in rows)+1048576,imports=44,resolved_helpers=9,relocation_linker_match=True,incomplete_engine_refused=True,card_execution=False)
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

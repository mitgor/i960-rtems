#!/usr/bin/env python3
"""Verify retained batched host Doom digests against the accepted corpus."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
rows=json.loads((a.root/'host-runs/results.json').read_text());assert [r['case'] for r in rows]==[f'p{p}-demo{d}-0' for p in (1,2) for d in (1,2,3)]
sha=hashlib.sha256((a.root/'host-engine/host32/doom-profile').read_bytes()).hexdigest()
for r in rows:
 d=a.root/'host-runs'/r['case'];assert r['binary_sha256']==sha and r['frames']==2100 and r['matches_reference']
 assert json.loads((d/'sha256-frames.json').read_text())==json.loads((a.reference/r['case']/'sha256-frames.json').read_text())
 c=json.loads((d/'cache.json').read_text());assert c==r['cache'] and not c['errors'] and c['bounce_bytes']==4096 and c['cache_bytes']==16384 and c['reserved_image']==1048576
 assert c['arena_peak']+c['reserved_image']+4352<8388608
 assert 'Doom arena drained;' in r['drain'] and r['profile']['pointer_bytes']==4 and not r['profile']['failed_allocations']
result=dict(frames=12600,matches_reference=True,host_binary_sha256=sha,max_host_arena_peak=max(r['cache']['arena_peak'] for r in rows),reserved_image=1048576,additional_card_staging=4352,card_execution=False,private_newlib=False)
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

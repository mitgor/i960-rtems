#!/usr/bin/env python3
"""Check repeat identities without discarding a faster unchanged baseline."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);a=p.parse_args()
out=Path(__file__).resolve().parent;ans={}
for name in ('a1','b1','b2','a2'):
 root=a.captures/('live-'+name)
 def read(n):return json.loads((root/n).read_text())
 rows=[json.loads(x) for x in (root/'play-frames.jsonl').read_text().splitlines()]
 system=json.loads((out/name/(name+'-system.json')).read_text())
 ans[name]=dict(request=read('request.json'),presentation=read('presentation-options.json'),test_options=read('test-options.json'),frames=len(rows),detail_modes=sorted(set(x['profile']['detail'] for x in rows)),buffer_addresses=sorted(set(x['marker'][4] for x in rows if 'marker' in x)),mailbox_frames=[x['frame'] for x in rows if 'marker' not in x],irq_period_us=system['heap_diagnostics']['irq_mean_period_us'],irq_max_gap_us=system['heap_diagnostics']['irq_max_gap_us'])
for x,y in (('a1','a2'),('b1','b2')):
 for k in ('payload_sha256','image_sha256','module_sha256','autonomous','module_options'):assert ans[x]['request'][k]==ans[y]['request'][k],k
 for k in ('presentation','test_options','detail_modes','buffer_addresses','mailbox_frames'):assert ans[x][k]==ans[y][k],k
print(json.dumps(ans,indent=2))

#!/usr/bin/env python3
"""Count actual driver calls and successful wire exchanges without estimating FPS."""
import json,struct,sys
from pathlib import Path
p=Path(sys.argv[1]);counts={};exchanges=0
for name in ('wad-journal.jsonl','wad-dma-journal.jsonl'):
 f=p/name
 if not f.exists():continue
 for line in f.open():
  r=json.loads(line);q=bytes.fromhex(r['request']);op=int.from_bytes(q[:4],'little');key=f'{name}:{op}'+(':pending' if r.get('errno')==11 else '')
  c=counts.setdefault(key,dict(calls=0,total_ms=0));c['calls']+=1;c['total_ms']+=r['ns']/1e6
  if name=='wad-journal.jsonl':
   assert 'errno' not in r
   exchanges+=9 if op==3 else 2+struct.unpack_from('<I',q,8)[0]//4
  else:
   assert r.get('errno') in (None,11)
   exchanges+=11 if op==1 else 1 if r.get('errno')==11 else 14
for c in counts.values():c['mean_ms']=c['total_ms']/c['calls']
print(json.dumps(dict(driver_calls=counts,mailbox_control_exchanges=exchanges,payload_crc='wad-dma-journal.jsonl' not in [x.name for x in p.iterdir()]),indent=2))

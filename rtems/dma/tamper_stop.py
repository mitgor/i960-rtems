#!/usr/bin/env python3
"""Reject corrupted cancellation records without editing original evidence."""
import json,sys,tempfile
from pathlib import Path
from verify_stop import verify
src=Path(sys.argv[1]).resolve();rows=[json.loads(l) for l in (src/'dma-stop.jsonl').read_text().splitlines()]
with tempfile.TemporaryDirectory() as d:
 out=Path(d)
 for p in src.iterdir():
  if p.is_file() and p.name!='dma-stop.jsonl':(out/p.name).symlink_to(p)
 def save():(out/'dma-stop.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 save();verify(out)
 complete=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==3)
 read=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==2)
 cases=[(0,'request',n) for n in (4,8,12,16,20,28,32)]+[(complete,'response',n) for n in range(32,160,4)]+[(read,'response',n) for n in (12,32,1055)]
 for i,field,offset in cases:
  old=rows[i][field];b=bytearray.fromhex(old);b[offset]^=1;rows[i][field]=b.hex();save()
  try:verify(out)
  except AssertionError:pass
  else:raise AssertionError('corrupt cancellation accepted')
  rows[i][field]=old
 save();verify(out)
 print(json.dumps(dict(rejected=len(cases),mutations=cases),indent=2))

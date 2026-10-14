#!/usr/bin/env python3
"""Mutate copies of real DMA capture records; never modify original evidence."""
import json,sys,tempfile
from pathlib import Path
from verify import verify
root=Path(sys.argv[1]).resolve();src=root/'live';rows=[json.loads(l) for l in (src/'dma-journal.jsonl').read_text().splitlines()];passed=[]
with tempfile.TemporaryDirectory() as d:
 out=Path(d)
 for p in src.iterdir():
  if p.is_file() and p.name!='dma-journal.jsonl':(out/p.name).symlink_to(p)
 def save(): (out/'dma-journal.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 save();verify(root,out)
 success=next(i for i,r in enumerate(rows) if 'response' in r)
 readback=success+1
 cases=[(success,'request',n) for n in (4,8,12,16,20)]+[(success,'response',n) for n in (32,36,40,44,48,52,56,60,64,68,72,76,88,92)]+[(readback,'response',n) for n in (12,32,1055)]
 for i,field,offset in cases:
  old=rows[i][field];b=bytearray.fromhex(old);b[offset]^=1;rows[i][field]=b.hex();save()
  try:verify(root,out)
  except AssertionError:passed.append([i,field,offset])
  else:raise AssertionError('corrupt capture accepted')
  rows[i][field]=old
 old=rows[0]['errno'];rows[0]['errno']=5;save()
 try:verify(root,out)
 except AssertionError:passed.append([0,'errno'])
 else:raise AssertionError('bad refusal accepted')
 rows[0]['errno']=old;save();verify(root,out)
print(json.dumps(dict(rejected=len(passed),mutations=passed),indent=2))

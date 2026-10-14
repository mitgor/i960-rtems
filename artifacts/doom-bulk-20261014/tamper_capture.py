#!/usr/bin/env python3
import json,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'project/rtems/residentnet'))
from verify_play_bulk import verify
src=root/'live';passed=[]
with tempfile.TemporaryDirectory() as d:
 p=Path(d)
 for f in src.iterdir():
  if f.is_file() and f.name not in ('frame-journal.jsonl','upload-journal.jsonl'):(p/f.name).symlink_to(f)
 rows=[json.loads(l) for l in (src/'frame-journal.jsonl').read_text().splitlines()]
 controls=[json.loads(l) for l in (src/'upload-journal.jsonl').read_text().splitlines()]
 def save():
  (p/'frame-journal.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
  (p/'upload-journal.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in controls))
 def refuse(label):
  save()
  try:verify(p)
  except AssertionError:passed.append(label)
  else:raise AssertionError('tamper accepted: '+str(label))
 save();verify(p)
 for index,field,offset in [(3,'request',x) for x in (0,4,8,32,36,40)]+[(3,'response',x) for x in (0,4,8,12,16,20,24,28,32,36,1055)]+[(68,'response',32),(len(rows)-1,'response',32)]:
  old=rows[index][field];b=bytearray.fromhex(old);b[offset]^=1;rows[index][field]=b.hex();refuse([index,field,offset]);rows[index][field]=old
 for i in range(3):
  old=rows[i]['errno'];rows[i]['errno']=5;refuse([i,'errno']);rows[i]['errno']=old
 import struct
 indexes=[i for i,r in enumerate(controls) if r['op']==10 and struct.unpack_from('<I',bytes.fromhex(r['request']),32)[0] in (1,2)]
 for i in indexes[:2]:
  old=controls[i]['request'];b=bytearray.fromhex(old);b[36]^=1;controls[i]['request']=b.hex();refuse([i,'input-or-ack']);controls[i]['request']=old
 save();verify(p)
(root/'tamper-results.json').write_text(json.dumps(dict(rejected=len(passed),mutations=passed),indent=2)+'\n')
print('PASS',len(passed),'physical-capture mutations refused; original evidence unchanged')

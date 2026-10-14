#!/usr/bin/env python3
"""Tamper copies of real DMA/mailbox/ACK captures, never original evidence."""
import json,sys,tempfile
from pathlib import Path
from verify import verify
src=Path(sys.argv[1]).resolve();names=['frame-dma-journal.jsonl','frame-journal.jsonl','upload-journal.jsonl','stress-frames.jsonl','owned-journal.jsonl']
original={n:(src/n).read_text() for n in names};tables={n:[json.loads(l) for l in original[n].splitlines()] for n in names}
with tempfile.TemporaryDirectory() as d:
 out=Path(d)
 for p in src.iterdir():
  if p.is_file() and p.name not in names:(out/p.name).symlink_to(p)
 def save(name):(out/name).write_text(''.join(json.dumps(r)+'\n' for r in tables[name]))
 for name in names:save(name)
 verify(out);cases=[]
 rows=tables[names[0]]
 complete=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==2)
 read=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==3)
 cases += [(names[0],complete,'response',n) for n in range(32,96,4)]
 cases += [(names[0],read,'response',n) for n in (0,4,8,12,32,1055)]
 cases += [(names[1],0,'response',n) for n in (4,8,12,32,1055)]
 ack=next(i for i,r in enumerate(tables[names[2]]) if r['op']==10 and bytes.fromhex(r['request'])[32]==1)
 cases += [(names[2],ack,'request',36),(names[2],ack,'response',32)]
 counter=next(i for i,r in enumerate(tables[names[2]]) if r['op']==10 and bytes.fromhex(r['request'])[32]==5 and int.from_bytes(bytes.fromhex(r['response'])[32:36],'little')>0)
 stop=next(i for i,r in enumerate(tables[names[4]]) if r['op']==6)
 cases += [(names[2],counter,'request',36),(names[2],counter,'response',32),(names[4],stop,'request',36),(names[4],stop,'response',36)]
 for name,i,field,offset in cases:
  old=tables[name][i][field];b=bytearray.fromhex(old);b[offset]^=1;tables[name][i][field]=b.hex();save(name)
  try:verify(out)
  except AssertionError:pass
  else:raise AssertionError((name,i,field,offset,'corruption accepted'))
  tables[name][i][field]=old;save(name)
 old=tables[names[3]][0]['paired'];tables[names[3]][0]['paired']=False;save(names[3])
 try:verify(out)
 except AssertionError:pass
 else:raise AssertionError('wrong method accepted')
 tables[names[3]][0]['paired']=old;save(names[3]);verify(out)
 print(json.dumps(dict(rejected=len(cases)+1,mutations=cases+[(names[3],0,'paired')]),indent=2))

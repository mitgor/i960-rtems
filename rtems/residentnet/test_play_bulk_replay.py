#!/usr/bin/env python3
"""Adversarial replay fixtures, independent of live card access."""
import hashlib,json,struct,tempfile
from pathlib import Path
from verify_play_bulk import verify
from frame_client import png

def fixture(p):
 rows=[];frames=[]
 def row(op,g,off,data=None,error=0):
  q=struct.pack('<10I',op,42,8,0,0,0,0,0,g,off)+bytes(1016)
  r=dict(op=op,request=q.hex(),ns=1000000)
  if error:r['errno']=error
  else:r['response']=(struct.pack('<8I',op,42,1024,1,0,0,0,0)+data).hex()
  rows.append(r)
 for g in range(1,29):
  op=11 if g<=4 or 11<=g<=22 else 9
  data=bytes([g])*64000+bytes(range(256))*3+bytes(768)
  assert len(data)==65536
  if g==1:
   row(11,2,0,error=116);row(11,1,65536,error=22);row(11,1,4,error=22)
  for method in ([op,9] if g<=4 else [op]):
   for off in list(range(0,65536,1024))+[0]:row(method,g,off,data[off:off+1024])
  (p/f'play-0-{g}.bin').write_bytes(data);(p/f'play-0-{g}.png').write_bytes(png(data))
  frames.append(dict(frame=g,session=0,method=op,seconds=g*10,transfer_seconds=1,sha256=hashlib.sha256(data).hexdigest(),comparison=dict(bytes=65536,scalar_seconds=2,bulk_seconds=1) if g<=4 else None))
 controls=[]
 for g in range(1,29):
  for i,v in ([(2,429)] if g==2 else [(2,173)] if g==4 else [])+[(1,g)]:
   controls.append(dict(op=10,request=(struct.pack('<10I',10,42,8,0,0,0,0,0,i,v)+bytes(1016)).hex(),response=(struct.pack('<8I',10,42,4,1,0,0,0,0)+bytes(1024)).hex()))
 (p/'upload-journal.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in controls))
 (p/'play-frames.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in frames))
 (p/'play-sessions.jsonl').write_text(json.dumps(dict(result=[0]*9+[2,1,210]))+'\n')
 return rows
with tempfile.TemporaryDirectory() as d:
 p=Path(d);rows=fixture(p);journal=p/'frame-journal.jsonl'
 def save():journal.write_text(''.join(json.dumps(r)+'\n' for r in rows))
 save();assert verify(p)['successful_reads']==2080
 mutations=0
 # Mutate request generation/offset/epoch/padding and every response header
 # invariant, first and second payload words, and a different comparison read.
 for index,field,offset in [(3,'request',x) for x in (0,4,8,32,36,40)]+[(3,'response',x) for x in (0,4,8,12,16,20,24,28,32,36,1055)]+[(68,'response',32),(rows.__len__()-1,'response',32)]:
  original=rows[index][field];b=bytearray.fromhex(original);b[offset]^=1;rows[index][field]=b.hex();save()
  try:verify(p)
  except AssertionError:mutations+=1
  else:raise AssertionError(('tamper accepted',index,field,offset))
  rows[index][field]=original
 for i in range(3):
  old=rows[i]['errno'];rows[i]['errno']=5;save()
  try:verify(p)
  except AssertionError:mutations+=1
  else:raise AssertionError('wrong refusal accepted')
  rows[i]['errno']=old
 save();assert verify(p)['full_frames']==28
 controls=p/'upload-journal.jsonl';original=controls.read_text()
 for index in (0,1):
  records=[json.loads(l) for l in original.splitlines()];b=bytearray.fromhex(records[index]['request']);b[36]^=1;records[index]['request']=b.hex()
  controls.write_text(''.join(json.dumps(r)+'\n' for r in records))
  try:verify(p)
  except AssertionError:mutations+=1
  else:raise AssertionError('changed input/ACK accepted')
 controls.write_text(original);assert verify(p)['full_frames']==28
print('PASS complete synthetic replay and',mutations,'rejected journal mutations (not hardware evidence)')

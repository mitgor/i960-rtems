#!/usr/bin/env python3
"""Replay cancellation independently; full system/RAM replay remains mandatory."""
import argparse,json,struct
from pathlib import Path

def verify(out):
 rows=[json.loads(l) for l in (out/'dma-stop.jsonl').read_text().splitlines()]
 result=json.loads((out/'dma-stop-result.json').read_text())
 last=json.loads((out/'dma-results.json').read_text())[-1]['report']
 epoch=next(e['epoch'] for e in json.loads((out/'controls.json').read_text()) if 'words' in e)
 submitted=False;completed=False;chunks=[];pending=0
 for row in rows:
  a=bytes.fromhex(row['request']);assert len(a)==1056 and a[32:]==bytes(1024) and row['ns']>0
  op,e,n,off,seq,seed,z1,z2=struct.unpack_from('<8I',a)
  assert e==epoch and seq==25 and z1==z2==0
  if 'errno' in row:
   assert submitted and not completed and op==3 and n==off==seed==0 and row['errno']==11
   pending+=1;continue
  b=bytes.fromhex(row['response']);assert len(b)==1056 and b[:32]==a[:32]
  if op==1:
   assert not submitted and (n,off,seed)==(65536,0,0x13570019) and b[32:]==bytes(1024);submitted=True
  elif op==3:
   assert submitted and not completed and n==off==seed==0 and b[160:]==bytes(896)
   report=list(struct.unpack_from('<32I',b,32));expected=last.copy()
   expected[1:5]=[25,last[2]-4095,65536,0x13570019];expected[14:16]=[0,10]
   # Register samples are from the preceding completed DMA; cancellation does
   # not arm hardware or claim another hardware completion. System audits
   # independently validate all engines and ownership after worker drain.
   assert report==expected==result['report'];completed=True
  else:
   assert op==2 and completed and n==1024 and off==len(chunks)*1024 and seed==0
   chunks.append(b[32:])
 data=b''.join(chunks);assert submitted and completed and len(data)==73728
 assert data==b'\xa5'*73728==(out/'dma-stop-buffer.bin').read_bytes()
 assert result['untouched_bytes']==73728 and result['stop_ns']>0
 return dict(cancelled_sequence=25,untouched_bytes=len(data),pending_polls=pending,control_wait_ms=result['stop_ns']/1e6)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();print(json.dumps(verify(a.run),indent=2))

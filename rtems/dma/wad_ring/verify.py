#!/usr/bin/env python3
"""Replay all ring generations, WAD bytes and slot completions, including final slots."""
import argparse,hashlib,json,struct
from pathlib import Path

def verify(out,wad):
 out=Path(out);data=Path(wad).read_bytes();identity=json.loads((out/'play-wad.json').read_text())
 assert identity['bytes']==len(data) and identity['sha256']==hashlib.sha256(data).hexdigest()
 def record(raw,magic,g):
  w=struct.unpack('<16I',raw)
  assert w[0]==magic and w[1]==w[7]==g and w[2]==(g-1)&1 and w[5]==len(data) and w[6]==g^0xffffffff and not any(w[8:])
  assert w[3]%32768==0 and w[3]<len(data) and w[4]==min(32768,len(data)-w[3])
  return w
 epoch=None;registered=False;requests={};submitted={};completed=set();nextgen=[1,2];final=set();cost=0;polls=0
 for line in (out/'wad-ring-journal.jsonl').read_text().splitlines():
  row=json.loads(line);q=bytes.fromhex(row['request']);s=bytes.fromhex(row['response']);assert len(q)==len(s)==32800 and q[:32]==s[:32] and row['ns']>0
  op,e,slot,g,off,n,total,z=struct.unpack_from('<8I',q);assert not z and 0<e<=65535 and total==len(data) and slot<2
  if epoch is None:epoch=e
  assert e==epoch;cost+=row['ns'];payload=s[32:]
  if op==1:
   assert not registered and not slot and not g and not off and not n and not any(q[32:]) and not any(payload[8:])
   a,b=struct.unpack_from('<2I',payload);assert a and b and a%64==b%64==0 and max(a,b)<=0xffffffff-40960 and (a+40960<=b or b+40960<=a);registered=True;continue
  assert registered and g and slot==(g-1)&1
  if op==2:
   assert not any(q[32:]) and not off and not n and g==nextgen[slot] and g not in requests and not any(payload[128:]);requests[g]=record(payload[:64],0x31515257,g);polls+=1
   if g>2:
    c=record(payload[64:128],0x31435257,g-2);assert c[1:]==submitted[g-2][1:];completed.add(g-2)
   else:assert not any(payload[64:128])
  elif op==3:
   assert g==nextgen[slot] and g in requests and g not in submitted and not any(payload[64:])
   r=record(payload[:64],0x31535257,g);assert r[1:]==requests[g][1:] and (off,n)==r[3:5]
   assert q[32:]==data[off:off+n].ljust(32768,b'\0');submitted[g]=r;nextgen[slot]+=2
  elif op==4:
   assert not any(q[32:]) and not off and not n and g==nextgen[slot]-2 and slot not in final and not any(payload[192:])
   for i,magic in enumerate((0x31515257,0x31535257,0x31435257)):
    r=record(payload[i*64:(i+1)*64],magic,g);assert r[1:]==submitted[g][1:]
   completed.add(g);final.add(slot)
  else:raise AssertionError('unknown ring operation')
 results=[json.loads(x) for x in (out/'wad-ring-results.jsonl').read_text().splitlines()]
 assert submitted and set(requests)==set(submitted)==completed==set(range(1,len(submitted)+1)) and len(results)==identity['requests']==len(submitted)
 assert len(final)==min(2,len(submitted))
 assert {r['sequence'] for r in results}==set(submitted)
 for r in results:
  q=submitted[r['sequence']];assert (r['slot'],r['offset'],r['wanted'])==q[2:5] and r['seconds']>0
 return dict(blocks=len(submitted),logical_bytes=sum(q[4] for q in submitted.values()),dma_payload_bytes=32768*len(submitted),successful_ioctl_seconds=cost/1e9,source_sha256=identity['sha256'],complete_generations=len(completed),payload_crc=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture');p.add_argument('--wad',required=True);a=p.parse_args();print(json.dumps(verify(a.capture,a.wad),indent=2))

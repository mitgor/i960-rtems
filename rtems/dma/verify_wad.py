#!/usr/bin/env python3
"""Replay every immutable WAD source block and hardware completion contract.
No CRC is claimed: source identity is checked offline against the pinned WAD.
This complements full system audits and independent rendered-frame comparisons.
"""
import argparse,hashlib,json,struct
from pathlib import Path
def verify(out,wad):
 out=Path(out);data=Path(wad).read_bytes();identity=json.loads((out/'play-wad.json').read_text())
 assert len(data)==identity['bytes'] and hashlib.sha256(data).hexdigest()==identity['sha256']
 results=[json.loads(x) for x in (out/'wad-dma-results.jsonl').read_text().splitlines()]
 rows=iter(json.loads(x) for x in (out/'wad-dma-journal.jsonl').read_text().splitlines())
 epoch=base=descriptor=None;last=0;polls=0;total=0
 live_requests={}
 journal=out/'wad-journal.jsonl'
 assert journal.exists(), 'missing live request capture'
 for line in journal.read_text().splitlines():
  row=json.loads(line);assert row['op']==3 and 'errno' not in row and row['ns']>0
  q=bytes.fromhex(row['request']);s=bytes.fromhex(row['response']);assert len(q)==len(s)==1056
  h=struct.unpack_from('<8I',q);assert h[0]==3 and 0<h[1]<=65535 and h[2:]==(0,0,0,0,0,0) and not any(q[32:])
  rh=struct.unpack_from('<8I',s);assert rh[:4]==(3,h[1],32,1) and not rh[4]&1 and rh[5:]==(0,0,0) and not any(s[64:])
  w=struct.unpack_from('<8I',s,32);assert w[0] in (0x31424157,0x31444157)
  if w[2]==1:
   assert w[0]==0x31424157 and w[3]==1 and w[7]==0
   geometry=(h[1],w[4],w[5],w[6])
   assert w[1] not in live_requests or live_requests[w[1]]==geometry
   live_requests[w[1]]=geometry
 for r in results:
  g=r['sequence'];off=r['offset'];n=r['wanted'];assert g>last and r['mode']=='dma-no-crc' and 0<n<=4096 and off<len(data) and r['seconds']>0;last=g
  row=next(rows);q=bytes.fromhex(row['request']);assert len(q)==4128 and row['ns']>0
  h=struct.unpack_from('<8I',q);assert h[0]==1 and h[2:]==(g,off,n,len(data),0,0) and 0<h[1]<=65535
  if epoch is None:epoch=h[1]
  assert live_requests[g]==(epoch,off,n,len(data))
  assert h[1]==epoch and q[32:]==data[off:off+n].ljust(4096,b'\0') and 'errno' not in row
  s=bytes.fromhex(row['response']);assert s==q[:32]+bytes(4096)
  while True:
   row=next(rows);q=bytes.fromhex(row['request']);assert q==struct.pack('<8I',2,epoch,g,off,n,len(data),0,0)+bytes(4096) and row['ns']>0
   if 'errno' in row:assert row['errno']==11 and 'response' not in row;polls+=1;continue
   break
  s=bytes.fromhex(row['response']);assert len(s)==4128 and s[:32]==q[:32] and s[80:]==bytes(4048)
  w=list(struct.unpack_from('<12I',s,32));assert w==r['report'] and w[0]==g and w[3]==4096 and w[4]==w[6]==w[7]==w[11]==0 and w[5]==w[10] and w[8]==6 and w[9]<200000
  assert 4096<w[1]<=0xffffffff-4096 and not w[1]&3 and 0xc0241000<=w[2]<=0xc0e2e000 and not w[2]&3
  assert 0xc0f4c010<=w[10]<=0xc0f8bfe0 and not w[10]&31
  if base is None:base=w[1];descriptor=w[10]
  assert w[1]==base and w[10]==descriptor;total+=min(n,len(data)-off)
 assert next(rows,None) is None and len(results)==identity['requests']
 return dict(blocks=len(results),logical_bytes=total,dma_bytes=4096*len(results),pending_polls=polls,payload_crc=False,source_sha256=identity['sha256'],total_service_seconds=sum(r['seconds'] for r in results))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture');p.add_argument('--wad',required=True);a=p.parse_args();print(json.dumps(verify(a.capture,a.wad),indent=2))

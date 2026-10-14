#!/usr/bin/env python3
"""Independent exact-byte replay of DMA captures; system audits stay separate."""
import argparse,json,struct,statistics
from pathlib import Path

def verify(root,out):
 symbols={p[2]:int(p[0],16) for l in (root/'residentnet/kernel.symbols').read_text().splitlines() if len(p:=l.split())==3}
 desc=(symbols['_dma_desc_storage']+31)&~31;source=symbols['_dma_source']+64
 assert 0xc0f4c010<=desc<0xc0f9bff0 and 0xc0f4c010<=source<source+65536<0xc0f9bff0
 rows=[json.loads(l) for l in (out/'dma-journal.jsonl').read_text().splitlines()];results=json.loads((out/'dma-results.json').read_text());assert len(results)==24
 cases=[(1,0),(3,1),(4,2),(31,3),(64,0),(511,1),(1024,0),(2048,0),(4095,3),(4096,0),(65536,0),(65536,4095)]*2
 epoch=next(e['epoch'] for e in json.loads((out/'controls.json').read_text()) if 'words' in e)
 pending=None;pending_ns=0;polls=0;async_mode=any(struct.unpack_from("<I",bytes.fromhex(r["request"]))[0]==3 for r in rows)
 current=0;chunks=[];refusals=[];times=[];base=None
 def finish():
  if current:
   data=b''.join(chunks);assert len(data)==73728 and data==(out/f'dma-{current:03}.bin').read_bytes()
   n,off=cases[current-1];seed=0x13570000+current
   expected=bytearray(b'\xa5'*73728);expected[4096+off:4096+off+n]=bytes((i*13^seed^(i>>8))&255 for i in range(n));assert data==expected
 for row in rows:
  a=bytes.fromhex(row['request']);assert len(a)==1056 and a[32:]==bytes(1024) and row['ns']>0
  op,e,n,off,seq,seed,z1,z2=struct.unpack_from('<8I',a);assert z1==z2==0
  if 'errno' in row:
   if op==3 and row['errno']==11:
    assert pending and e==epoch and n==off==seed==0 and seq==current+1
    pending_ns+=row['ns'];polls+=1;continue
   if (op==1 and (n==0 or n>65536 or off>4095)) or (op==2 and (off>73728-1024 or off&1023)):expected=22 # Linux ioctl ABI, not the replay host errno table
   else:assert e!=epoch or (op==1 and seq==current) or (op==2 and (current==0 or seq<current));expected=116 # Linux ESTALE
   assert row['errno']==expected;refusals.append(expected);continue
  b=bytes.fromhex(row['response']);assert len(b)==1056 and b[:32]==a[:32] and e==epoch
  if async_mode and op==1:
   assert pending is None and seq==current+1 and (n,off)==cases[seq-1] and seed==0x13570000+seq and b[32:]==bytes(1024)
   pending=(n,off,seed);pending_ns=row['ns'];continue
  if op==(3 if async_mode else 1):
   if async_mode:
    assert pending and n==off==seed==0
    n,off,seed=pending;pending=None
   finish();current+=1;chunks=[];assert seq==current and (n,off)==cases[seq-1] and seed==0x13570000+seq
   r=list(struct.unpack_from('<32I',b,32));assert b[160:]==bytes(896)
   assert r[:2]==[0x31414d44,seq] and r[3:6]==[n,seed,0] and r[6]<200000
   assert r[7:16]==[desc,0,0,7,2,0,0,1,0]
   assert r[16:]==([0]*15+[2] if async_mode else [0]*16)
   candidate=r[2]-4096-off
   if base is None:base=candidate
   assert candidate==base and 0<base<=0xffffffff-73728
   assert results[seq-1]['report']==r and results[seq-1]['length']==n and results[seq-1]['offset']==off and results[seq-1]['seed']==seed and results[seq-1]['seq']==seq
   times.append((row['ns']+pending_ns)/1e6)
  else:
   assert op==2 and seq==current and n==1024 and off==len(chunks)*1024 and not seed;chunks.append(b[32:])
 finish();assert pending is None and current==24 and len(refusals)==54
 snaps=json.loads((out/'snapshots.json').read_text());assert len(snaps)>=2*24+4 and snaps[-1]['words'][2]==2
 return dict(async_completion=async_mode,pending_polls=polls,transfers=current,captured_bytes=73728*current,refusals=len(refusals),full_audit_pairs=len(snaps),dma_address=hex(base),descriptor=hex(desc),source=hex(source),transaction_ms=dict(min=min(times),median=statistics.median(times),max=max(times)),note='Includes target pattern generation/check, mailbox exchanges and host full-buffer check; not DMA throughput or Doom FPS')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('run',type=Path);a=p.parse_args();print(json.dumps(verify(a.root,a.run),indent=2))

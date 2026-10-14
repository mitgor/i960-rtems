#!/usr/bin/env python3
"""Full byte reconstruction of the DMA/mailbox A/B run. Also run verify.py."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
from frame_client import png

def verify(out):
 out=Path(out);frames=[json.loads(l) for l in (out/'play-frames.jsonl').read_text().splitlines()]
 dma=[json.loads(l) for l in (out/'frame-dma-journal.jsonl').read_text().splitlines()]
 mailbox=[json.loads(l) for l in (out/'frame-journal.jsonl').read_text().splitlines()]
 reports=[json.loads(l) for l in (out/'frame-dma-results.jsonl').read_text().splitlines()]
 assert len(frames)==28 and len(mailbox)==1040 and len(reports)==16
 cursor=mc=ri=0;epoch=None;source=desc=base=None;pending=0;times={11:[],12:[]};compared=[]
 def dcall(op,g,off=0,error=None):
  nonlocal cursor,epoch
  row=dma[cursor];cursor+=1;q=bytes.fromhex(row['request']);assert len(q)==1056 and q[32:]==bytes(1024) and row['ns']>0
  h=struct.unpack_from('<8I',q);assert h[0]==op and h[2:]==(g,off,0,0,0,0) and 0<h[1]<=65535
  if epoch is None:epoch=h[1]
  assert h[1]==epoch
  if error is not None:assert row['errno']==error and 'response' not in row;return
  assert 'errno' not in row;b=bytes.fromhex(row['response']);assert len(b)==1056 and b[:32]==q[:32];return b[32:]
 def mcall(g,off):
  nonlocal mc
  row=mailbox[mc];mc+=1;q=bytes.fromhex(row['request']);b=bytes.fromhex(row['response'])
  assert row['op']==11 and row['ns']>0 and 'errno' not in row and len(q)==len(b)==1056
  assert struct.unpack_from('<8I',q)==(11,epoch,8,0,0,0,0,0) and struct.unpack_from('<2I',q,32)==(g,off) and not any(q[40:])
  h=struct.unpack_from('<8I',b);assert h[:4]==(11,epoch,1024,1) and not h[4]&1 and h[5:]==(0,0,0)
  return b[32:]
 def mread(g):
  b=b''.join(mcall(g,i) for i in range(0,65536,1024));assert mcall(g,0)==b[:1024];return b
 dcall(1,2,error=116);dcall(3,1,73728,error=22);dcall(3,1,4,error=22)
 for g,f in enumerate(frames,1):
  method=12 if g<=4 or 11<=g<=22 else 11
  assert f['frame']==g and f['session']==0 and f['method']==method
  if method==12:
   assert dcall(1,g)==bytes(1024)
   while 'errno' in dma[cursor]:dcall(2,g,error=11);pending+=1
   b=dcall(2,g);r=list(struct.unpack_from('<16I',b));assert b[64:]==bytes(960)
   assert r[:3]==[0x314d4446,2,g] and r[5]==r[6] and r[7]==r[9]==r[10]==r[13]==r[14]==0 and r[8]==r[15] and r[11]==7 and r[12]<200000
   if source is None:source,desc,base=r[4],r[15],r[3]-4096
   assert r[4]==source and 0xc0240000<=source<=0xc0e30000
   assert r[15]==desc and not desc&31 and 0xc0f4c010<=desc<=0xc0f8bfe0
   assert r[3]==base+4096 and 0<base<=0xffffffff-73728
   capture=b''.join(dcall(3,g,i) for i in range(0,73728,1024));assert capture==(out/f'frame-dma-{g:03}.bin').read_bytes()
   assert capture[:4096]==capture[69632:]==b'\xa5'*4096
   data=capture[4096:69632];assert dcall(3,g,4096)==data[:1024] and zlib.crc32(data)==r[5]
   assert reports[ri]['frame']==g and reports[ri]['report']==r and reports[ri]['seconds']>0;ri+=1
  else:data=mread(g)
  assert data==(out/f'play-0-{g}.bin').read_bytes() and png(data)==(out/f'play-0-{g}.png').read_bytes()
  assert hashlib.sha256(data).hexdigest()==f['sha256'] and f['transfer_seconds']>0 and f['png_seconds']>0
  if g<=4:
   assert mread(g)==data
   c=f['comparison'];assert c['bytes']==65536 and c['mailbox_seconds']>0 and c['dma_seconds']>0;compared.append(c)
  else:assert f['comparison'] is None;times[method].append(f['transfer_seconds'])
 assert cursor==len(dma) and mc==len(mailbox) and ri==len(reports)
 controls=[]
 for line in (out/'upload-journal.jsonl').read_text().splitlines():
  r=json.loads(line)
  if r['op']!=10:continue
  assert 'errno' not in r;q=bytes.fromhex(r['request']);s=bytes.fromhex(r['response']);assert len(q)==len(s)==1056
  assert struct.unpack_from('<8I',q)==(10,epoch,8,0,0,0,0,0) and not any(q[40:])
  h=struct.unpack_from('<8I',s);assert h[:4]==(10,epoch,4,1) and not h[4]&1 and h[5:]==(0,0,0) and not any(s[36:])
  i,v=struct.unpack_from('<2I',q,32);result=struct.unpack_from('<I',s,32)[0];assert i in (0,1,2)
  if i==0:assert v==0 and result!=0xffffffff
  else:assert result==0;controls.append((i,v))
 expected=[]
 for g in range(1,29):
  if g==2:expected.append((2,429))
  if g==4:expected.append((2,173))
  expected.append((1,g))
 assert controls==expected
 sessions=[json.loads(l) for l in (out/'play-sessions.jsonl').read_text().splitlines()];assert len(sessions)==1 and sessions[0]['result'][9:]==[2,1,210]
 blocks=[]
 for a,b in ((5,10),(11,16),(17,22),(23,28)):
  f=frames[a-1:b];elapsed=f[-1]['seconds']-f[0]['seconds'];assert elapsed>0
  blocks.append(dict(method=f[0]['method'],first=a,last=b,fps=5/elapsed,mean_transfer_seconds=sum(x['transfer_seconds'] for x in f)/6))
 fps={op:10/sum(5/b['fps'] for b in blocks if b['method']==op) for op in (11,12)}
 return dict(full_frames=28,paired_comparisons=4,refusals=3,dma_frames=16,full_guarded_bytes=16*73728,pending_polls=pending,mailbox_reads=1040,blocks=blocks,paired_seconds=compared,mean_transfer_seconds={k:sum(v)/len(v) for k,v in times.items()},fps=fps,fps_speedup=fps[12]/fps[11],epoch=epoch,source=hex(source),descriptor=hex(desc),dma_base=hex(base))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();print(json.dumps(verify(a.capture),indent=2))

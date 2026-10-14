#!/usr/bin/env python3
"""Independent reconstruction of the bounded bulk acceptance's complete frames.
Run alongside verify.py: this does not replace any RAM, owner or system audit.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from frame_client import png

def verify(out):
 out=Path(out);frames=[json.loads(l) for l in (out/'play-frames.jsonl').read_text().splitlines()]
 rows=[json.loads(l) for l in (out/'frame-journal.jsonl').read_text().splitlines()]
 assert len(frames)==28 and len(rows)==2083
 epoch=None;cursor=0;durations={9:[],11:[]};comparisons=[]
 def request(op,g,off,error=0):
  nonlocal cursor,epoch
  r=rows[cursor];cursor+=1;q=bytes.fromhex(r['request']);assert len(q)==1056
  w=struct.unpack_from('<8I',q);assert w[0]==op and w[2:]==(8,0,0,0,0,0) and 0<w[1]<=65535
  if epoch is None:epoch=w[1]
  assert w[1]==epoch and struct.unpack_from('<2I',q,32)==(g,off) and not any(q[40:])
  assert r['op']==op and r['ns']>0
  if error:assert r['errno']==error and 'response' not in r;return
  assert 'errno' not in r;s=bytes.fromhex(r['response']);assert len(s)==1056
  h=struct.unpack_from('<8I',s);assert h[:4]==(op,epoch,1024,1) and not h[4]&1 and h[5:]==(0,0,0)
  return s[32:]
 def read(op,g):
  data=b''.join(request(op,g,off) for off in range(0,65536,1024))
  assert request(op,g,0)==data[:1024];return data
 for g,f in enumerate(frames,1):
  op=11 if g<=4 or 11<=g<=22 else 9
  assert f['session']==0 and f['frame']==g and f['method']==op
  if g==1:
   request(11,2,0,116);request(11,1,65536,22);request(11,1,4,22)
  data=read(op,g);assert data==(out/f'play-0-{g}.bin').read_bytes()
  assert (out/f'play-0-{g}.png').read_bytes()==png(data)
  assert hashlib.sha256(data).hexdigest()==f['sha256']
  if g<=4:
   assert read(9,g)==data
   c=f['comparison'];assert c['bytes']==65536 and min(c['scalar_seconds'],c['bulk_seconds'])>0;comparisons.append(c)
  else:
   assert f['comparison'] is None;durations[op].append(f['transfer_seconds'])
 assert cursor==len(rows)
 # The benchmark is meaningful only with the planned input and one ACK per
 # captured frame. Reconstruct these independently from actual control ioctls.
 controls=[]
 for line in (out/'upload-journal.jsonl').read_text().splitlines():
  r=json.loads(line)
  if r['op']!=10:continue
  assert 'errno' not in r
  q=bytes.fromhex(r['request']);s=bytes.fromhex(r['response'])
  assert len(q)==len(s)==1056
  assert struct.unpack_from('<8I',q)==(10,epoch,8,0,0,0,0,0) and not any(q[40:])
  h=struct.unpack_from('<8I',s);assert h[:4]==(10,epoch,4,1) and not h[4]&1 and h[5:]==(0,0,0) and not any(s[36:])
  index,value=struct.unpack_from('<2I',q,32);result=struct.unpack_from('<I',s,32)[0]
  assert index in (0,1,2)
  if index==0:assert value==0 and result!=0xffffffff
  else:assert result==0;controls.append((index,value))
 expected=[]
 for g in range(1,29):
  if g==2:expected.append((2,256+173))
  if g==4:expected.append((2,173))
  expected.append((1,g))
 assert controls==expected, 'unexpected input or ACK changes the benchmark'
 sessions=[json.loads(l) for l in (out/'play-sessions.jsonl').read_text().splitlines()]
 assert len(sessions)==1 and sessions[0]['result'][9:]==[2,1,210]
 blocks=[]
 for a,b in ((5,10),(11,16),(17,22),(23,28)):
  samples=frames[a-1:b];elapsed=samples[-1]['seconds']-samples[0]['seconds'];assert elapsed>0
  blocks.append(dict(method=samples[0]['method'],first=a,last=b,fps=(b-a)/elapsed,mean_transfer_seconds=sum(f['transfer_seconds'] for f in samples)/len(samples)))
 return dict(full_frames=28,paired_comparisons=4,refusals=3,successful_reads=2080,blocks=blocks,paired_seconds=comparisons,mean_transfer_seconds={str(k):sum(v)/len(v) for k,v in durations.items()},epoch=epoch)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();print(json.dumps(verify(a.capture),indent=2))

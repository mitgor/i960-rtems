#!/usr/bin/env python3
"""Exercise real frame capture/replay code and reject damaged evidence."""
import argparse,errno,json,shutil,struct,tempfile
from pathlib import Path
from frame_client import capture_frames,verify_frames
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--capture',type=Path);a=p.parse_args();data=(a.build/'visible-frames.bin').read_bytes();rows=[]
class Fake:
 def __init__(self,out):self.out=out;self.active=0
 def io(self,op,b):
  assert op==9;g,off=struct.unpack('<2I',b);e=dict(op=op,ns=12345,request=(struct.pack('<8I',9,42,8,0,0,0,0,0)+b+bytes(1016)).hex())
  error=errno.EINVAL if off>=len(data) else errno.ESTALE if g!=self.active or not g else 0
  if error:e['errno']=error
  else:e['response']=(struct.pack('<8I',9,42,1024,1,0,0,0,0)+data[off:off+1024]).hex()
  with (self.out/'engine-frame-journal.jsonl').open('a') as f:f.write(json.dumps(e)+'\n')
  if error:raise OSError(error,'expected rejection')
  return data[off:off+1024]
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);base=root/'capture';base.mkdir();u=Fake(base)
 (base/'engine-owned-journal.jsonl').write_text(json.dumps(dict(request=struct.pack('<8I',5,42,0,0,0,0,0,0).hex()))+'\n')
 for g in (1,0,2):u.active=g;capture_frames(u,a.build,g)
 if a.capture:
  shutil.rmtree(base);base.mkdir()
  for name in ('engine-owned-journal.jsonl','engine-frame-journal.jsonl','visible-1.bin','visible-2.bin'):shutil.copy2(a.capture/name,base/name)
  shutil.copytree(a.capture/'browser',base/'browser')
 assert verify_frames(base,a.build)['accepted']
 original=[json.loads(x) for x in (base/'engine-frame-journal.jsonl').read_text().splitlines()]
 for case in ('payload','epoch','generation','offset','request_padding','response_header','wrong_errno','missing','duplicate','reorder','uncertain','saved_bytes','png'):
  out=root/case;shutil.copytree(base,out);events=json.loads(json.dumps(original));e=events[2]
  if case in ('payload','response_header'):
   b=bytearray.fromhex(e['response']);b[32 if case=='payload' else 12]^=1;e['response']=b.hex()
  elif case in ('epoch','generation','offset','request_padding'):
   b=bytearray.fromhex(e['request']);b[dict(epoch=4,generation=32,offset=36,request_padding=40)[case]]^=1;e['request']=b.hex()
  elif case=='wrong_errno':events[0]['errno']=5
  elif case=='missing':events.pop(2)
  elif case=='duplicate':events.insert(2,events[2])
  elif case=='reorder':events[2],events[3]=events[3],events[2]
  elif case=='uncertain':e['errno']=110
  else:
   p=out/('visible-1.bin' if case=='saved_bytes' else 'browser/card-1-0.png');b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
  (out/'engine-frame-journal.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
  try:verify_frames(out,a.build)
  except AssertionError:rows.append(dict(case=case,rejected=True))
  else:raise AssertionError('mutation accepted: '+case)
a.output.write_text(json.dumps(rows,indent=2)+'\n');print('PASS actual host capture/replay, full byte comparison and 13 evidence mutations')

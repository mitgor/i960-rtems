#!/usr/bin/env python3
"""Exercise actual client/replay, source identity and completion tamper rejection."""
import json,struct,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'residentnet'))
import wad_dma_client as client
from types import SimpleNamespace
client.errno=SimpleNamespace(EAGAIN=11) # Linux capture ABI, including on macOS
from verify_wad import verify
class U:
 fd=7;epoch=42;gate=threading.RLock()
 def __init__(self,p):self.out=p;self.i=0
 def io(self,op):
  assert op==3
  if self.i==3:return struct.pack('<8I',0x31424157,3,0,1,0,0,10000,0)
  off,n=[(0,512),(512,4096),(9963,512)][self.i]
  reply=struct.pack('<8I',0x31424157,self.i+1,1,1,off,n,10000,0)
  q=struct.pack('<8I',3,42,0,0,0,0,0,0)+bytes(1024);r=struct.pack('<8I',3,42,32,1,0,0,0,0)+reply+bytes(992)
  with (self.out/'wad-journal.jsonl').open('a') as f:f.write(json.dumps(dict(op=3,ns=1,request=q.hex(),response=r.hex()))+'\n')
  return reply
with tempfile.TemporaryDirectory() as d:
 p=Path(d);wad=p/'test.wad';data=bytearray((i*7)%256 for i in range(10000));data[:12]=struct.pack('<4sII',b'IWAD',1,9000);wad.write_bytes(data)
 u=U(p);s=client.BulkServer(u,wad);pending=[0];calls=[0]
 def ioctl(fd,cmd,b,mutate):
  assert fd==7 and cmd==0xd0204d09 and mutate and len(b)==4128
  op,e,g,o,n,total,_,_=struct.unpack_from('<8I',b)
  assert e==42 and g==u.i+1 and total==10000
  if op==1:
   assert not pending[0] and b[32:]==data[o:o+n].ljust(4096,b'\0');pending[0]=1;calls[0]=0;b[32:]=bytes(4096)
  else:
   assert pending[0] and b[32:]==bytes(4096);calls[0]+=1
   if calls[0]==1:raise BlockingIOError(11,'pending')
   r=[g,0x101000,0xc0801000,4096,0,0xc0f80000,0,0,6,4,0xc0f80000,0];b[32:80]=struct.pack('<12I',*r);pending[0]=0;u.i+=1
 client.fcntl.ioctl=ioctl
 for _ in range(3):assert s.serve()
 assert not s.serve()
 (p/'play-wad.json').write_text(json.dumps(dict(bytes=len(data),sha256=s.sha,requests=3)))
 assert verify(p,wad)['blocks']==3
 path=p/'wad-dma-journal.jsonl';original=path.read_text();rows=[json.loads(l) for l in original.splitlines()];rejected=0
 for index,field,offset in [(0,'request',x) for x in (0,4,8,12,16,20,24,28,32,4096)]+[(2,'response',x) for x in range(32,80,4)]:
  changed=json.loads(json.dumps(rows));b=bytearray.fromhex(changed[index][field]);b[offset]^=1;changed[index][field]=b.hex();path.write_text(''.join(json.dumps(x)+'\n' for x in changed))
  try:verify(p,wad)
  except (AssertionError,IndexError,StopIteration):rejected+=1
  else:raise AssertionError((index,field,offset))
 path.write_text(original);assert rejected==22
print('PASS actual bulk WAD client, EOF padding, pending completion, offline source replay, 22 corruptions rejected')

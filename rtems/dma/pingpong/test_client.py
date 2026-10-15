#!/usr/bin/env python3
"""Run the real client flow, including Upload.command deadline validation.
Modeled transport only; does not replace target/driver or physical acceptance.
"""
import errno,hashlib,json,struct,sys,tempfile,threading
from pathlib import Path
from unittest.mock import patch
r=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(r/'rtems/residentnet'),str(r/'rtems/dma/stress')]
import pingpong_client as client
from upload_client import Upload
class Model:
 def __init__(self):self.seen=0;self.stop=False;self.running=False;self.clock=1;self.next=[17,18];self.read=[set(),set()];self.caps={};self.errors=[];self.queries=[]
 def tick(self):self.clock+=.01;return self.clock
 def data(self,g):
  if g not in self.caps:
   mark=struct.pack('<8I',0x31505044,g,(g-1)&1,65536,0xc0800000+((g-1)&1)*65536,100+g,(~g)&0xffffffff,g)
   self.caps[g]=b'\xa5'*4096+client.pattern(g)+b'\xa5'*4064+mark
  return self.caps[g]
m=Model()
class U(Upload):
 def begin(self,*a):pass
 def write(self,*a):pass
 def prepare(self):pass
 def io(self,op,data=b'',epoch=None):
  if op==1:m.running=True;return b''
  if op==10:
   i,g=struct.unpack('<2I',data)
   if i==0:return struct.pack('<I',m.seen+1 if m.running else 0)
   assert i==1 and g==m.seen+1;m.seen=g;return bytes(4)
  assert op==11;g,off=struct.unpack('<2I',data);return client.pattern(g)[off:off+1024]
 def query(self):
  m.queries.append(m.seen);return (0x31525055,self.sequence,0,0 if m.stop else 1,0,0x454e4702)+(0,)*10
 def command(self,c,a=0,*args,**kw):
  if c==18:return super().command(c,a,*args,**kw)
  result=[0]*16
  if c==8:result[5]=0x444c4942
  elif c==19:result[5]=[0x454e4750,3,65536,0,0,83,0,0,0,2,1,210][a]
  else:assert c in (5,10)
  return result
class D:
 def __init__(self,*a):pass
 def read(self,g,crc=True):assert not crc;return client.pattern(g),.01
class C:
 def __init__(self,*a):pass
 def query(self):return [0x3252444f,123,1]
 def request(self,g):assert g==123;m.stop=True
class P(client.PingPong):
 def call(self,op,g=0,off=0):
  slot=(g-1)&1;b=bytes(1024)
  if op==1:return struct.pack('<2I',0x100000,0x200000)+b[8:]
  if op==6:assert g==17;return b
  if op==7:return struct.pack('<I',int(m.tick()*1000))+b[4:]
  if op==5:return struct.pack('<6I',m.seen,100,*m.next,2,1)+b[24:]
  if g!=m.next[slot]:m.errors.append(errno.ESTALE);raise OSError(errno.ESTALE,'stale')
  if op==2:return m.data(g)[73696:]+b[32:]
  if op==3:m.read[slot].add(off);return m.data(g)[off:off+1024]
  assert op==4
  if len(m.read[slot])!=72:m.errors.append(errno.EBUSY);raise OSError(errno.EBUSY,'unread')
  m.read[slot].clear();m.next[slot]+=2;m.seen=g;return b
with tempfile.TemporaryDirectory() as d:
 d=Path(d);root=d/'image';root.mkdir();out=d/'capture';out.mkdir()
 for name in ('template.bin','relocations.bin'):(root/name).write_bytes(b'')
 manifest=dict(pingpong=True,double_buffer=True,template_sha256=hashlib.sha256(b'').hexdigest(),metadata_sha256=hashlib.sha256(b'').hexdigest(),sections=[],metadata_offset=0,entry=0)
 (root/'manifest.json').write_text(json.dumps(manifest));(d/'wad').write_bytes(b'IWAD')
 with patch.multiple(client,Upload=U,FrameDMA=D,Control=C,PingPong=P),patch.object(client.time,'monotonic',m.tick),patch.object(client.time,'sleep',lambda x:None):
  client.exercise(0,42,out,threading.RLock(),d/'wad',root,threading.Event(),80)
 assert m.stop and m.seen==80 and m.next==[81,82] and m.errors==[errno.ESTALE,errno.EBUSY,errno.ESTALE]
 assert json.loads((out/'pingpong-result.json').read_text())['stalled_stop']
 assert sum(16<=g<=80 for g in m.queries)<20, 'per-frame command polling returned'
print('PASS real client flow: accepted command deadline, 80 frames, stalled slots, premature release, resumed delivery and STOP')

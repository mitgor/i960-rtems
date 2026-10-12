#!/usr/bin/env python3
"""Real host server emits exact ordered fragments and one-shot faults/STOP."""
import errno,struct,tempfile,zlib
from pathlib import Path
from batch_client import BatchServer,MAGIC
class IO:
 gate=None
 def __init__(self):self.calls=[];self.wanted=4096;self.offset=512;self.request=True
 def io(self,op,data=b''):
  self.calls.append((op,data))
  if op==3:return struct.pack('<8I',MAGIC,1,int(self.request),1,self.offset,self.wanted,20037,0)
  if op==5:return struct.pack('<8I',0x3252444f,12,1,0,0,0,0,0)
  if op==6:
   if struct.unpack_from('<I',data,4)[0]==11:raise OSError(errno.ESTALE,'stale')
  return data
with tempfile.TemporaryDirectory() as d:
 wad=bytearray(i%251 for i in range(20037));wad[:12]=struct.pack('<4sII',b'IWAD',1,1000);path=Path(d)/'test.wad';path.write_bytes(wad)
 for mode in ('normal','crc','short','host-error','timeout','stop'):
  u=IO();s=BatchServer(u,path);s.mode=mode;assert s.serve();packets=[x[1] for x in u.calls if x[0]==4];assert len(packets)==(3 if mode in ('timeout','stop') else 8)
  for i,p in enumerate(packets):
   w=struct.unpack_from('<8I',p);assert w[:4]==(MAGIC,1,1,512+512*i) and w[7]==4096
   expected=bytes(wad[512+512*i:1024+512*i]);last=i==7
   if last and mode=='short':expected=expected[:-1]
   if last and mode=='host-error':expected=b''
   assert w[4]==len(expected) and w[5]==int(last and mode=='host-error') and w[6]==(zlib.crc32(expected)^(last and mode=='crc')) and p[32:32+w[4]]==expected and not any(p[32+w[4]:])
  before=len(packets);assert s.serve();assert len([x for x in u.calls if x[0]==4])==before
  if mode=='stop':assert s.stop_generation==12 and [struct.unpack_from('<I',p,4)[0] for op,p in u.calls if op==6]==[11,12]
 u=IO();u.offset=20000;u.wanted=4096;s=BatchServer(u,path);assert s.serve();p=next(p for op,p in u.calls if op==4);assert struct.unpack_from('<I',p,16)[0]==37 and p[32:69]==wad[20000:]
print('PASS batch host: immutable bytes, eight ordered fragments, late CRC/short/error, partial timeout/STOP, stale generation, EOF and no duplicate reply')

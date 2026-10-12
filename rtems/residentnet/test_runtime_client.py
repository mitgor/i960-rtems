#!/usr/bin/env python3
"""The request/reply pair shares the audit gate; no stale write retries."""
import struct,tempfile,zlib
from pathlib import Path
from runtime_client import WadServer,MAGIC
class Gate:
 def __init__(self):self.depth=0;self.entries=0
 def __enter__(self):assert not self.depth;self.depth=1;self.entries+=1
 def __exit__(self,*args):self.depth=0
class Upload:
 def __init__(self):self.gate=Gate();self.calls=[];self.sequence=1;self.state=1
 def io(self,op,data=b''):
  assert self.gate.depth==1;self.calls.append((op,data))
  if op==3:return struct.pack('<8I',MAGIC,self.sequence,self.state,1,0,12,2048,0)
  assert op==4
with tempfile.TemporaryDirectory() as tmp:
 path=Path(tmp)/'test.wad';data=bytearray(2048);data[:12]=struct.pack('<4sII',b'IWAD',32,1024);path.write_bytes(data);u=Upload();s=WadServer(u,path)
 path.write_bytes(b'changed after snapshot');assert s.data==data
 assert s.serve() and [op for op,_ in u.calls]==[3,4] and u.gate.entries==1
 packet=u.calls[1][1];assert packet[32:]==data[:12] and struct.unpack_from('<I',packet,24)[0]==zlib.crc32(data[:12])
 assert s.serve() and [op for op,_ in u.calls]==[3,4,3] # no duplicate write
 u.sequence=2;s.mode='timeout';s.injected=False;assert s.serve() and u.calls[-1][0]==3
 u.state=0;assert s.serve() is False
print('PASS host WAD: immutable snapshot, atomic query/reply audit gate, duplicate suppression, timeout without write')

# Invalid completion bounds must be refused before any command publication or
# sequence consumption; otherwise local validation can leave ownership uncertain.
from upload_client import Upload as ResidentUpload
with tempfile.TemporaryDirectory() as tmp:
 u=ResidentUpload(None,1,tmp);calls=[];u.io=lambda *args:calls.append(args)
 for timeout in (0,-1,61,float('nan')):
  try:u.command(6,timeout=timeout)
  except AssertionError:pass
  else:raise AssertionError('invalid completion bound accepted')
  assert not calls and u.sequence==0
print('PASS upload: invalid completion bounds publish nothing and consume no sequence')

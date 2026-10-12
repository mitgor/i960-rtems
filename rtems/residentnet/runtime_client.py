"""One immutable host WAD snapshot. Card requests can never select a pathname."""
import hashlib,json,struct,time,zlib
from pathlib import Path
from contextlib import nullcontext
MAGIC=0x31444157
class WadServer:
 def __init__(self,u,path):
  self.u=u;self.data=Path(path).read_bytes();assert 512<=len(self.data)<=268435456 and self.data[:4]==b'IWAD'
  count,offset=struct.unpack_from('<II',self.data,4);assert count and offset<=len(self.data) and count<=(len(self.data)-offset)//16
  self.sha=hashlib.sha256(self.data).hexdigest();self.seen=set();self.mode='normal';self.injected=False;self.records=[]
 def serve(self):
  # Keep the frozen request and its reply together relative to long paired
  # audits. The driver still locks/checks each ioctl and never retries writes.
  with self.u.gate if self.u.gate is not None else nullcontext():
   return self.serve_locked()
 def serve_locked(self):
  w=struct.unpack('<8I',self.u.io(3));assert w[0]==MAGIC
  if w[2]!=1:return False
  if w[1] in self.seen:return True
  _,seq,_,file,offset,wanted,total,_=w;assert file==1 and total==len(self.data) and 0<wanted<=512 and offset<=total
  self.seen.add(seq);mode=self.mode if not self.injected else 'normal';self.injected=True
  self.records.append(dict(sequence=seq,offset=offset,wanted=wanted,mode=mode))
  if mode=='timeout':return True
  data=self.data[offset:offset+wanted];status=0
  if mode=='short':data=data[:-1]
  if mode=='host-error':data=b'';status=1
  crc=zlib.crc32(data) ^ (1 if mode=='crc' else 0)
  packet=struct.pack('<8I',MAGIC,seq,file,offset,len(data),status,crc,0)+data
  self.u.io(4,packet+b'\0'*((-len(packet))%4))
  return True
 def expected(self):
  offset=struct.unpack_from('<I',self.data,8)[0];h=2166136261
  for b in self.data[:12]+self.data[offset:offset+512]+self.data[-37:]:h=((h^b)*16777619)&0xffffffff
  return h

def exercise_runtime(u,wad_path,probe_path):
 server=WadServer(u,wad_path);probe=Path(probe_path).read_bytes();assert len(probe)<=4096 and not len(probe)%4
 u.begin([(0,len(probe),len(probe),1,zlib.crc32(probe))]);u.write(0,probe);u.prepare()
 # Entry refused until file binding. Duplicate binding does not replace identity.
 u.command(11,expected=1)
 binding=struct.pack('<3I',MAGIC,1,len(server.data))+bytes.fromhex(server.sha)
 u.command(10,data=binding);u.command(10,data=binding,expected=1)
 u.service=server.serve;rows=[]
 try:
  for mode in ('normal','crc','short','host-error','timeout','normal'):
   server.mode=mode;server.injected=False;start=time.monotonic();reply=u.command(11);expected=server.expected() if mode=='normal' else 3
   assert reply[5]==expected,(mode,reply)
   rows.append(dict(mode=mode,seconds=time.monotonic()-start,result=reply[5]))
 finally:u.service=None
 stats=[u.command(12,i)[5] for i in range(8)]
 assert stats[0]==MAGIC and stats[1:]==[10,6,2,1,0,0,len(server.data)],stats
 u.command(5)
 result=dict(wad_sha256=server.sha,file_bytes=len(server.data),probe_sha256=hashlib.sha256(probe).hexdigest(),probe_bytes=len(probe),oracle=server.expected(),runs=rows,requests=server.records,report=stats)
 (u.out/'runtime-results.json').write_text(json.dumps(result,indent=2)+'\n');(u.out/'runtime-probe.bin').write_bytes(probe)

 # New builds carry a closed relocation recipe beside the PIC probe.
 root=Path(probe_path).parent/"relocate"
 if root.exists():
  from relocate_client import exercise
  exercise(u,root)

 root=Path(probe_path).parent/"cache"
 if root.exists():
  from cache_client import exercise
  exercise(u,wad_path,root)

 root=Path(probe_path).parent/"owned"
 if root.exists():
  from owned_client import exercise
  exercise(u,root)

 root=Path(probe_path).parent/"engine"
 if root.exists():
  from engine_client import exercise
  exercise(u,root,wad_path)

 # Opt-in manifest marker; old binaries and their exact 512-byte proofs remain.
 root=Path(probe_path).parent/"cache"
 if (root/'batch-enabled').exists():
  from batch_client import exercise as exercise_batch
  exercise_batch(u,wad_path,root)

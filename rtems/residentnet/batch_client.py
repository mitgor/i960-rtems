"""Opt-in WAB1: immutable host snapshot, one request and ordered fragments."""
import errno,hashlib,json,struct,time,zlib
from pathlib import Path
from runtime_client import WadServer
from owned_client import Control
MAGIC=0x31424157
class BatchServer(WadServer):
 def serve_locked(self):
  w=struct.unpack('<8I',self.u.io(3))
  if w[0]!=MAGIC:assert w[0]==0x31444157 and w[2]==0;return False
  if w[2]!=1:return False
  if w[1] in self.seen:return True
  _,seq,_,file,offset,wanted,total,_=w;assert file==1 and total==len(self.data) and 0<wanted<=4096 and offset<total
  self.seen.add(seq);mode=self.mode if not self.injected and wanted==4096 else 'normal'
  if mode!='normal':self.injected=True
  data=self.data[offset:offset+wanted]
  self.records.append(dict(sequence=seq,offset=offset,wanted=wanted,mode=mode))
  for part in range(0,len(data),512):
   if mode in ('timeout','stop') and part==1536:
    if mode=='stop':
     ctl=Control(self.u,False);state=ctl.query();assert state[2];ctl.request(state[1]-1,errno.ESTALE);ctl.request(state[1]);self.stop_generation=state[1]
    return True
   block=data[part:part+512];status=0;corrupt=part+512>=len(data)
   if corrupt and mode=='short':block=block[:-1]
   if corrupt and mode=='host-error':block=b'';status=1
   crc=zlib.crc32(block)^(corrupt and mode=='crc')
   packet=struct.pack('<8I',MAGIC,seq,1,offset+part,len(block),status,crc,wanted)+block
   self.u.io(4,packet+b'\0'*((-len(packet))%4))
  return True

def exercise(u,wad,root):
 root=Path(root);m=json.loads((root/'manifest.json').read_text());blob=(root/'template.bin').read_bytes();assert hashlib.sha256(blob).hexdigest()==m['sha256']
 server=BatchServer(u,wad);s=m['sections'][0];u.journal_namespace='batch-';rows=[]
 try:
  u.command(20,expected=1)
  u.begin([(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags'],zlib.crc32(blob))],m['entry']);u.write(0,blob);u.prepare();base=u.command(14)[5]
  d=server.data;directory=struct.unpack_from('<I',d,8)[0];oracle=2166136261
  for b in d[:12]+d[499:1610]+d[directory:directory+512]+d[4099:12291]+d[-37:]:oracle=((oracle^b)*16777619)&0xffffffff
  u.service=server.serve
  for limit,mode in [(512,'normal'),(4096,'normal'),(4096,'crc'),(4096,'short'),(4096,'host-error'),(4096,'timeout'),(4096,'stop'),(4096,'normal'),(512,'normal')]:
   server.mode=mode;server.injected=False;start=time.monotonic();w=u.command(20 if limit==4096 else 22,timeout=60);assert w[5]==(oracle if mode=='normal' else 3) and w[4]==3,(mode,w)
   u.service=None;report=[u.command(21,i)[5] for i in range(8)];assert report[0]==MAGIC and report[5:7]==[0,0]
   rows.append(dict(mode=mode,limit=limit,seconds=time.monotonic()-start,result=w[5],report=report));u.service=server.serve
  u.service=None;u.command(5)
  (u.out/'batch-results.json').write_text(json.dumps(dict(manifest=m,wad_sha256=server.sha,base=0xc02d0040+base,oracle=oracle,runs=rows,requests=server.records,stop_generation=server.stop_generation),indent=2)+'\n')
 finally:u.service=None;u.journal_namespace=''

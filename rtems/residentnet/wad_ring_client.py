"""Two shared slots, immutable host WAD, no per-read mailbox operation."""
import errno,fcntl,json,struct,time
from batch_client import BatchServer
class RingServer(BatchServer):
 def __init__(self,u,wad):
  super().__init__(u,wad);self.next=[1,2];self.pending_polls=0;self.pending_ns=0;self.successful_ns=0
 def call(self,op,slot=0,g=0,offset=0,n=0,data=b''):
  raw=bytearray(struct.pack('<8I',op,self.u.epoch,slot,g,offset,n,len(self.data),0)+data+bytes(32768-len(data)))
  before=raw.hex();start=time.monotonic_ns()
  try:fcntl.ioctl(self.u.fd,0xc0204d0b,raw,True)
  except OSError as e:
   if e.errno==errno.EAGAIN:
    self.pending_polls+=1;self.pending_ns+=time.monotonic_ns()-start;return None
   raise
  elapsed=time.monotonic_ns()-start;self.successful_ns+=elapsed
  with (self.u.out/'wad-ring-journal.jsonl').open('a') as f:
   f.write(json.dumps(dict(request=before,response=raw.hex(),ns=elapsed))+'\n')
  return raw[32:]
 def enable(self):
  with self.u.gate:self.call(1)
 def finish(self):
  with self.u.gate:
   for slot,g in enumerate(self.next):
    if g>slot+1:assert self.call(4,slot,g-2) is not None
  (self.u.out/'wad-ring-service.json').write_text(json.dumps(dict(pending_polls=self.pending_polls,pending_ns=self.pending_ns,successful_ns=self.successful_ns))+'\n')
 def serve_locked(self):
  found=False
  for slot in range(2):
   g=self.next[slot];raw=self.call(2,slot,g)
   if raw is None:continue
   q=struct.unpack_from('<16I',raw)
   assert q[0]==0x31515257 and q[1]==q[7]==g and q[2]==slot and q[5]==len(self.data) and q[6]==g^0xffffffff
   offset,n=q[3:5];assert offset%32768==0 and n==min(32768,len(self.data)-offset) and n>0 and not any(q[8:])
   start=time.monotonic();self.call(3,slot,g,offset,n,self.data[offset:offset+n]);self.next[slot]+=2
   row=dict(sequence=g,slot=slot,offset=offset,wanted=n,seconds=time.monotonic()-start)
   self.records.append(row)
   with (self.u.out/'wad-ring-results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
   found=True
  return found

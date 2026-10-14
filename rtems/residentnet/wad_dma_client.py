"""Immutable 4 KiB WAD snapshot delivery; no payload CRC, no caller addresses."""
import errno,fcntl,json,struct,time
from batch_client import BatchServer,MAGIC
class BulkServer(BatchServer):
 def call(self,op,seq,offset,wanted,total,data=b''):
  raw=bytearray(struct.pack('<8I',op,self.u.epoch,seq,offset,wanted,total,0,0)+data+bytes(4096-len(data)))
  before=raw.hex();t=time.monotonic_ns()
  try:fcntl.ioctl(self.u.fd,0xd0204d09,raw,True)
  except OSError as e:
   self.log(dict(request=before,errno=e.errno,ns=time.monotonic_ns()-t));raise
  self.log(dict(request=before,response=raw.hex(),ns=time.monotonic_ns()-t));return raw[32:]
 def log(self,row):
  with (self.u.out/'wad-dma-journal.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 def serve_locked(self):
  w=struct.unpack('<8I',self.u.io(3))
  if w[0]!=MAGIC:assert w[0]==0x31444157 and w[2]==0;return False
  if w[2]!=1:return False
  if w[1] in self.seen:return True
  _,seq,_,file,offset,wanted,total,_=w
  assert file==1 and total==len(self.data) and 0<wanted<=4096 and offset<total
  data=self.data[offset:offset+wanted];t=time.monotonic()
  self.call(1,seq,offset,wanted,total,data);deadline=t+5
  while True:
   try:r=self.call(2,seq,offset,wanted,total);break
   except OSError as e:
    assert e.errno==errno.EAGAIN and time.monotonic()<deadline
    time.sleep(.001)
  report=list(struct.unpack_from('<12I',r));assert report[0]==seq and report[3]==4096 and not report[11]
  self.seen.add(seq);row=dict(sequence=seq,offset=offset,wanted=wanted,mode='dma-no-crc',seconds=time.monotonic()-t,report=report)
  self.records.append(row)
  with (self.u.out/'wad-dma-results.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  return True

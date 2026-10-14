"""Complete guarded-frame capture. Hold the audit gate only for this bounded job."""
import errno,fcntl,json,struct,time,zlib
from pathlib import Path
class FrameDMA:
 def __init__(self,fd,epoch,out,gate):self.fd=fd;self.epoch=epoch;self.out=Path(out);self.gate=gate
 def call(self,op,g,off=0):
  raw=bytearray(struct.pack('<8I',op,self.epoch,g,off,0,0,0,0)+bytes(1024));before=raw.hex();t=time.monotonic_ns()
  try:fcntl.ioctl(self.fd,0xc4204d08,raw,True)
  except OSError as e:
   self.log(dict(request=before,errno=e.errno,ns=time.monotonic_ns()-t));raise
  self.log(dict(request=before,response=raw.hex(),ns=time.monotonic_ns()-t));return raw[32:]
 def log(self,row):
  with (self.out/'frame-dma-journal.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 def read(self,g,crc=True,service=None):
  with self.gate:
   t=time.monotonic();self.call(1,g,0 if crc else 1);deadline=t+10
   while True:
    try:r=self.call(2,g);break
    except OSError as e:
     assert e.errno==errno.EAGAIN and time.monotonic()<deadline
     # A two-buffer engine can need WAD data before it reaches its next
     # task-level DMA service point. Keep that independent channel live.
     if service:service()
     time.sleep(.001)
   report=list(struct.unpack_from('<16I',r));assert report[0:3]==[0x314d4446,2,g] and report[13]==0
   data=b''.join(self.call(3,g,i) for i in range(0,73728,1024))
   assert data[:4096]==data[69632:]==b'\xa5'*4096
   payload=data[4096:69632];assert self.call(3,g,4096)==payload[:1024]
   assert report[14]==(0 if crc else 1)
   if crc:assert zlib.crc32(payload)==report[5]==report[6]
   else:assert report[5]==report[6]==0
   (self.out/f'frame-dma-{g:03}.bin').write_bytes(data)
   with (self.out/'frame-dma-results.jsonl').open('a') as f:f.write(json.dumps(dict(frame=g,report=report,seconds=time.monotonic()-t))+'\n')
   return payload,time.monotonic()-t

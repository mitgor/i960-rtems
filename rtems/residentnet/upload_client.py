"""Resident UPL1 ioctl client. Never retries an uncertain write."""
import errno,fcntl,json,struct,time,zlib
from contextlib import nullcontext
from pathlib import Path
MAGIC=0x314c5055
class Upload:
 def __init__(self,fd,epoch,out,gate=None,abort=None):self.fd=fd;self.epoch=epoch;self.out=Path(out);self.sequence=0;self.gate=gate;self.service=None;self.journal_namespace='';self.abort=abort
 def io(self,op,data=b'',epoch=None):
  raw=bytearray(struct.pack('<8I',op,self.epoch if epoch is None else epoch,len(data),0,0,0,0,0)+data.ljust(1024,b'\0'))
  before=bytes(raw);start=time.monotonic_ns()
  try:
   with self.gate if self.gate is not None else nullcontext():fcntl.ioctl(self.fd,0xc4204d06,raw,True)
  except OSError as e:
   self.record(dict(op=op,start_ns=start,request=before.hex(),errno=e.errno,ns=time.monotonic_ns()-start));raise
  self.record(dict(op=op,start_ns=start,request=before.hex(),response=raw.hex(),ns=time.monotonic_ns()-start))
  w=struct.unpack_from('<8I',raw);assert w[3]==1 and not w[4]&1 and w[5:]==(0,0,0)
  return bytes(raw[32:32+w[2]])
 def record(self,event):
  with (self.out/(self.journal_namespace+'frame-journal.jsonl' if event['op'] in (9,11) else self.journal_namespace+'checkpoint-journal.jsonl' if event['op'] in (7,8) else self.journal_namespace+'owned-journal.jsonl' if event['op'] in (5,6) else self.journal_namespace+'wad-journal.jsonl' if event['op'] in (3,4) else 'upload-journal.jsonl')).open('a') as f:f.write(json.dumps(event)+'\n')
 def query(self):return struct.unpack('<16I',self.io(2))
 def command(self,command,a=0,b=0,c=0,data=b'',expected=0,sequence=None,timeout=30):
  if self.abort is not None and self.abort.is_set():raise RuntimeError("card audit failed; stop new uploads, retain until reboot")
  assert 0<timeout<=60 or (command==18 and timeout in (1860,3660)) # reviewed 30-minute startup + 60 s completion/audit allowance
  if sequence is None:self.sequence+=1;sequence=self.sequence
  packet=struct.pack('<8I',MAGIC,sequence,command,a,b,c,0,0)+data
  packet+=b'\0'*((-len(packet))%4);self.io(1,packet)
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:

   if self.service and self.service():
    time.sleep(.002);continue
   w=self.query()
   if w[0]==0x31525055 and w[1]==sequence and not w[3]:
    assert w[2]==expected,(command,w);return w
   time.sleep(.002)
  raise TimeoutError('upload completion uncertain; do not retry or reclaim')
 def begin(self,segments,entry=0,expected=0):
  words=[1,len(segments),entry]
  for row in segments:words+=list(row)
  words+=[0]*((8-len(segments))*5)
  return self.command(1,data=struct.pack('<43I',*words),expected=expected)
 def write(self,index,data):
  for off in range(0,len(data),992):
   chunk=data[off:off+992];self.command(2,index,off,len(chunk),chunk)
 def prepare(self):
  for _ in range(8192+32): # 8 MiB / 1 KiB plus per-segment transitions
   w=self.command(3)
   if w[5]==2:return w
   assert w[5]==1
  raise AssertionError('unbounded preparation')
def exercise(fd,epoch,out,gate=None,doom_heap=False,doom_shared=False,runtime=None,abort=None):
 u=Upload(fd,epoch,out,gate,abort)
 try:u.io(2,epoch=epoch^0x8000);raise AssertionError('stale epoch accepted')
 except OSError as e:assert e.errno==errno.ESTALE
 assert u.command(6)[5]==1
 # Invalid overlap must not consume an allocation; replayed sequence is rejected.
 u.begin([(0,20,20,1,0),(0,4,32,2,0)],expected=4)
 u.command(6,sequence=u.sequence,expected=1)
 # Code and data each exceed 64 KiB; only the reviewed returning prefix executes.
 code=struct.pack('<5I',0x90841000,0x8c883000,0xa5a5a5a5,0x58844310,0x0a000000)
 code=code+bytes(i%251 for i in range(98304-len(code)))
 data=b'DATA'+bytes((i*7)%251 for i in range(98309-4))
 # Hold 1 MiB during the initial heap/peer proof so retained proof buffers
 # land beyond the future engine + contiguous 6 MiB zone, rather than inside it.
 memory_bytes=1048576-0x20000 if runtime and (Path(runtime[1]).parent/'engine').exists() else 196608
 segments=[(0,len(code),len(code),1,zlib.crc32(code)),(0x20000,len(data),memory_bytes,2,zlib.crc32(data))]
 u.begin(segments)
 u.command(3,expected=4) # incomplete image cannot prepare or execute
 u.command(4,expected=1)
 u.command(2,0,1,4,b'abcd',expected=4)
 u.write(0,code);u.write(1,data)
 u.command(2,0,0,4,b'abcd',expected=4)
 ready=u.prepare();assert ready[4]==3
 proof=u.command(7);assert proof[10:12]==(6291456,1)
 if doom_heap:
  start=time.monotonic();libc=u.command(8);assert libc[5]==0x444c4942
  (Path(out)/'doom-heap.json').write_text(json.dumps(dict(result=list(libc),seconds=time.monotonic()-start,retained_until_stop=65536),indent=2)+'\n')
 if doom_shared:
  stats=[u.command(9,i)[5] for i in range(10)]
  assert stats[0]==0x53484152 and stats[1]==4 and min(stats[2:6])>0 and stats[8:10]==[1,1]
  (Path(out)/'doom-shared.json').write_text(json.dumps(dict(magic=hex(stats[0]),phase=stats[1],peer_checks=stats[2],wrong_task_rejections=stats[3],peer_enters=stats[4],owner_enters=stats[5],max_wait_ticks=stats[6],max_hold_ticks=stats[7],timeout_rejections=stats[8],recursive_rejections=stats[9],peer_retained_bytes=98304),indent=2)+'\n')
 result=u.command(4);assert result[5]==0xe4f1e4e1 and result[4]==3
 u.command(5);assert u.command(6)[5]==1
 if runtime:
  from runtime_client import exercise_runtime
  exercise_runtime(u,*runtime)
 # Cancel incomplete upload, then allocate again: no stale image survives.
 u.begin(segments);u.command(5)
 # Keep one partial image pinned until RTEMS STOP drains the worker contexts.
 u.begin(segments);u.command(2,0,0,4,code[:4])
 results=dict(code_bytes=len(code),data_bytes=len(data),bss_bytes=196608-len(data),image_span=327680,simultaneous_proof_bytes=6291456,result=hex(result[5]),commands=u.sequence,final=list(u.query()))
 (Path(out)/'upload-results.json').write_text(json.dumps(results,indent=2)+'\n')
 (Path(out)/'uploaded-code.bin').write_bytes(code);(Path(out)/'uploaded-data.bin').write_bytes(data)
 return results

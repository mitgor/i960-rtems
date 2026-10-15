"""Bounded baseline/ping-pong comparison; no WAD reads or browser claim."""
import errno,fcntl,hashlib,json,struct,sys,time,zlib
from pathlib import Path
from upload_client import Upload
from owned_client import Control
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from frame_dma_client import FrameDMA
from stress_client import pattern
class PingPong:
 def __init__(self,fd,epoch,out,gate):self.fd=fd;self.epoch=epoch;self.out=Path(out);self.gate=gate
 def call(self,op,g=0,off=0):
  b=bytearray(struct.pack('<8I',op,self.epoch,g,off,0,0,0,0)+bytes(73728 if op==8 else 1024));request=b.hex();t=time.monotonic_ns()
  with self.gate:
   try:fcntl.ioctl(self.fd,0xc4204d0a,b,True)
   except OSError as e:
    self.log(dict(op=op,g=g,off=off,errno=e.errno,ns=time.monotonic_ns()-t));raise
  self.log(dict(request=request,response=b.hex(),ns=time.monotonic_ns()-t));return b[32:]
 def log(self,row):
  with (self.out/'pingpong-journal.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 def ready(self,g):return list(struct.unpack_from('<8I',self.call(2,g)))
 def capture(self,g,synthetic=True):
  b=bytes(self.call(8,g,73728))
  assert b[:4096]==b'\xa5'*4096 and b[69632:73696]==b'\xa5'*4064
  m=list(struct.unpack_from('<8I',b,73696));assert m[:4]==[0x31505044,g,(g-1)&1,65536] and m[6:]==[(~g)&0xffffffff,g]
  if synthetic:assert b[4096:69632]==pattern(g)
  (self.out/f'pingpong-{g:03}.bin').write_bytes(b)
  return b,m

def exercise(fd,epoch,out,gate,wad,root,abort,count):
 assert 64<=count<=512 and count%2==0
 out=Path(out);root=Path(root);m=json.loads((root/'manifest.json').read_text());assert m.get('pingpong') and m.get('double_buffer')
 blob=(root/'template.bin').read_bytes();meta=(root/'relocations.bin').read_bytes()
 assert hashlib.sha256(blob).hexdigest()==m['template_sha256'] and hashlib.sha256(meta).hexdigest()==m['metadata_sha256']
 u=Upload(fd,epoch,out,gate,abort);dma=FrameDMA(fd,epoch,out,gate);pp=PingPong(fd,epoch,out,gate)
 u.begin([(0,4,4,1,0),(16,0,1048576-16,2,0)]);assert u.command(8)[5]==0x444c4942;u.command(5)
 wad=Path(wad).read_bytes();u.command(10,data=struct.pack('<3I',0x31444157,1,len(wad))+hashlib.sha256(wad).digest())
 control=Control(u,False);parts=[blob[s['offset']:s['offset']+s['file_bytes']] for s in m['sections']]+[meta]
 geometry=[(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags']) for s in m['sections']]+[(m['metadata_offset'],len(meta),len(meta),2)]
 u.begin([(*s,zlib.crc32(p)) for s,p in zip(geometry,parts)],m['entry'])
 for i,p in enumerate(parts):
  if p:u.write(i,p)
 u.prepare();addresses=list(struct.unpack_from('<2I',pp.call(1)));seen=0;stop_sent=False;started=time.monotonic();stalled=False;held=None;rows=[]
 def ctl(i=0,v=0):return struct.unpack('<I',u.io(10,struct.pack('<2I',i,v)))[0]
 def expect_error(op,g,allowed):
  try:pp.call(op,g)
  except OSError as e:assert e.errno in allowed;return e.errno
  raise AssertionError('invalid ownership accepted')
 def calibrate():
  samples=[]
  for i in range(3):
   t0=time.monotonic();ticks=struct.unpack_from('<I',pp.call(7))[0];t1=time.monotonic();assert ticks!=0xffffffff
   samples.append(dict(before=t0,after=t1,card_ms=ticks))
  with (out/'pingpong-clocks.jsonl').open('a') as f:f.write(json.dumps(samples)+'\n')
 def serve():
  nonlocal seen,stop_sent,stalled,held
  if abort.is_set():raise RuntimeError('full audit failed; retain mappings')
  if stop_sent:return False
  g=seen+1;t=time.monotonic()
  if g<=16:
   current=ctl()
   if current!=g:assert current in (0,seen);return False
   raw,elapsed=dma.read(g,crc=False)
   assert raw==pattern(g)
   paired=g<=4 or g==16
   if paired:assert b''.join(u.io(11,struct.pack('<2I',g,i)) for i in range(0,65536,1024))==raw
   assert ctl(1,g)==0;seen=g
   row=dict(frame=g,mode='host-started',seconds=time.monotonic()-started,service_seconds=time.monotonic()-t,transfer_seconds=elapsed,paired=paired)
   rows.append(row)
   if g==16:calibrate();pp.call(6,17)
  else:
   try:marker=pp.ready(g)
   except OSError as e:assert e.errno==errno.EAGAIN;return False
   detected=time.monotonic()
   # Hold both complete slots for three seconds, while outer full audits continue.
   if g in (17,count+1):
    try:pp.ready(g+1)
    except OSError as e:assert e.errno==errno.EAGAIN;return False
    if held is None:
     a,_=pp.capture(g);b,_=pp.capture(g+1);held=(time.monotonic(),a,b)
     assert expect_error(4,g-2,(errno.ESTALE,))==errno.ESTALE
     return False
    if time.monotonic()-held[0]<3:return False
    a,_=pp.capture(g);b,_=pp.capture(g+1);assert (a,b)==held[1:]
    stats=list(struct.unpack_from('<6I',pp.call(5)));assert stats[1]>0 and stats[2:4]==[g,g+1]
    with (out/'pingpong-stalls.jsonl').open('a') as f:f.write(json.dumps(dict(first=g,seconds=time.monotonic()-held[0],unchanged=True,stats=stats))+'\n')
    if g==count+1:
     calibrate()
     q=control.query();assert q[2];control.request(q[1]);stop_sent=True;return False
    held=None;stalled=True
   if g==19:expect_error(4,g,(errno.EBUSY,))
   raw,marker=pp.capture(g);pp.call(4,g);seen=g
   row=dict(detected_monotonic=detected,frame=g,mode='card-started',seconds=time.monotonic()-started,service_seconds=time.monotonic()-t,ready_to_copy_release_seconds=time.monotonic()-detected,marker=marker,sha256=hashlib.sha256(raw).hexdigest())
   rows.append(row)
  with (out/'pingpong-frames.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  if g<=4 or g%16==0:print(json.dumps(row),flush=True)
  return False
 # DMA completion is in host RAM. Engine command completion is separate and
 # bounded to one query/second while streaming; STOP queries immediately.
 last_query=started
 def service():
  nonlocal last_query
  serve();now=time.monotonic()
  if seen<16 or stop_sent or now-last_query>=1:
   last_query=now;return False
  return True
 u.service=service
 try:reply=u.command(18,timeout=1860)
 finally:u.service=None
 result=[u.command(19,i)[5] for i in range(12)]
 assert seen==count and stop_sent and stalled and reply[5]==0x454e4702
 assert result[:3]==[0x454e4750,3,65536] and count+2<=result[5]<=count+3 and result[9:]==[2,1,210],result
 # STOP does not recycle or mutate the two host-owned completed slots.
 assert pp.capture(count+1)[0]==held[1] and pp.capture(count+2)[0]==held[2]
 stats=list(struct.unpack_from('<6I',pp.call(5)));assert stats[4]!=1 and stats[5]>0, 'need a full system audit during an exact DMA lease'
 (out/'pingpong-result.json').write_text(json.dumps(dict(protocol_version=2,frames=count,held_frames=2,stalled_stop=True,stats=stats,result=result,reply=list(reply),addresses=addresses,manifest=m,zero_wad_reads=True),indent=2)+'\n')

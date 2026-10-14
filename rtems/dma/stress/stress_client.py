"""Finite deterministic producer through the real admission/pin/DMA/ACK path."""
import hashlib,json,struct,sys,time,zlib
from pathlib import Path
from upload_client import Upload
from owned_client import Control
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from frame_dma_client import FrameDMA

def pattern(g):return bytes(((i*13)^(i>>8)^(g*37))&255 for i in range(65536))
def exercise(fd,epoch,out,gate,wad,root,abort,count):
 out=Path(out);root=Path(root);m=json.loads((root/'manifest.json').read_text());assert m.get('dma_stress')==1 and 1<=count<=2048
 blob=(root/'template.bin').read_bytes();meta=(root/'relocations.bin').read_bytes()
 assert hashlib.sha256(blob).hexdigest()==m['template_sha256'] and hashlib.sha256(meta).hexdigest()==m['metadata_sha256']
 u=Upload(fd,epoch,out,gate,abort);dma=FrameDMA(fd,epoch,out,gate)
 # Same shared arena admission and WAD metadata binding; zero WAD reads.
 u.begin([(0,4,4,1,0),(16,0,1048576-16,2,0)]);assert u.command(8)[5]==0x444c4942;u.command(5)
 wad=Path(wad).read_bytes();u.command(10,data=struct.pack('<3I',0x31444157,1,len(wad))+hashlib.sha256(wad).digest())
 control=Control(u,False);parts=[blob[s['offset']:s['offset']+s['file_bytes']] for s in m['sections']]+[meta]
 geometry=[(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags']) for s in m['sections']]+[(m['metadata_offset'],len(meta),len(meta),2)]
 u.begin([(*s,zlib.crc32(p)) for s,p in zip(geometry,parts)],m['entry'])
 for i,p in enumerate(parts):
  if p:u.write(i,p)
 u.prepare();seen=0;stop_sent=False;isolation_checks=0;started=time.monotonic()
 def ctl(i=0,v=0):return struct.unpack('<I',u.io(10,struct.pack('<2I',i,v)))[0]
 assert ctl(5,16)==0, 'fresh producer requires an unused DMA isolation counter'
 def serve():
  nonlocal seen,stop_sent,isolation_checks
  if abort.is_set():raise RuntimeError('full audit failed; retain resources')
  if seen==count and not stop_sent:
   isolation_checks=ctl(5,16);assert 0<isolation_checks<0xffffffff
   q=control.query();assert q[2];control.request(q[1]);stop_sent=True
  if stop_sent:return False
  g=ctl();assert g!=0xffffffff
  if not g or g==seen:return False
  assert g==seen+1
  raw,elapsed=dma.read(g);assert raw==pattern(g) and ctl()==g
  paired=g<=4 or g%32==0 or g==count
  if paired:
   other=b''.join(u.io(11,struct.pack('<2I',g,off)) for off in range(0,65536,1024))
   assert other==raw and u.io(11,struct.pack('<2I',g,0))==raw[:1024] and ctl()==g
  assert ctl(1,g)==0;seen=g
  row=dict(frame=g,seconds=time.monotonic()-started,transfer_seconds=elapsed,paired=paired,sha256=hashlib.sha256(raw).hexdigest())
  with (out/'stress-frames.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  if g<=4 or g%32==0:print(json.dumps(row),flush=True)
  return False
 u.service=serve
 try:reply=u.command(18,timeout=3660)
 finally:u.service=None
 result=[u.command(19,i)[5] for i in range(12)]
 assert seen==count and stop_sent and reply[5]==0x454e4702
 assert result[:3]==[0x454e4750,3,65536] and result[5]==count and result[9:]==[2,1,210],result
 assert not (out/'wad-journal.jsonl').exists()
 (out/'stress-result.json').write_text(json.dumps(dict(isolation_checks=isolation_checks,frames=count,seconds=time.monotonic()-started,result=result,reply=list(reply),manifest=m,zero_wad_reads=True),indent=2)+'\n')

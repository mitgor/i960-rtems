#!/usr/bin/env python3
"""Actual DMA client against a model, then independent complete-frame replay."""
import errno,json,struct,sys,tempfile,zlib
from pathlib import Path
from types import SimpleNamespace
import frame_dma_client as client
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'residentnet'))
from verify_play_dma import verify
from frame_client import png
from contextlib import nullcontext
client.errno=SimpleNamespace(EAGAIN=11)
def header(op,g,off=0):return struct.pack('<8I',op,42,g,off,0,0,0,0)
with tempfile.TemporaryDirectory() as d:
 out=Path(d);fdma=client.FrameDMA(1,42,out,nullcontext());generation=1;pending=False;report=None;capture=None
 def data(g):return bytes((i*7+g+(i>>8))&255 for i in range(64768))+bytes(768)
 def ioctl(fd,cmd,raw,mutate):
  global pending,report,capture
  op,e,g,off,*zero=struct.unpack_from('<8I',raw);assert cmd==0xc4204d08 and e==42 and not any(zero) and not any(raw[32:])
  if op==3 and (off>72704 or off&1023):raise OSError(22,'bounds')
  if g!=generation:raise OSError(116,'stale')
  if op==1:
   b=data(g);capture=b'\xa5'*4096+b+b'\xa5'*4096;c=zlib.crc32(b);report=[0x314d4446,2,g,0x101000,0xc0800000,c,c,0,0xc0f80000,0,0,7,5,0,0,0xc0f80000];pending=True
  elif op==2:
   if pending:pending=False;raise OSError(11,'pending')
   struct.pack_into('<16I',raw,32,*report)
  else:assert op==3;raw[32:]=capture[off:off+1024]
 client.fcntl.ioctl=ioctl
 for op,g,off,code in ((1,2,0,116),(3,1,73728,22),(3,1,4,22)):
  try:fdma.call(op,g,off)
  except OSError as e:assert e.errno==code
 frames=[];mail=[];controls=[];time=0
 def mailbox(g):
  b=data(g)
  for off in list(range(0,65536,1024))+[0]:
   q=struct.pack('<10I',11,42,8,0,0,0,0,0,g,off)+bytes(1016)
   r=struct.pack('<8I',11,42,1024,1,0,0,0,0)+b[off:off+1024]
   mail.append(dict(op=11,request=q.hex(),response=r.hex(),ns=100))
  return b
 for g in range(1,29):
  generation=g;method=12 if g<=4 or 11<=g<=22 else 11
  b,_=fdma.read(g) if method==12 else (mailbox(g),.5)
  comparison=None
  if g<=4:assert mailbox(g)==b;comparison=dict(mailbox_seconds=.5,dma_seconds=.1,bytes=65536)
  time+=.7 if method==12 else 1.2
  import hashlib
  frames.append(dict(session=0,frame=g,method=method,comparison=comparison,seconds=time,transfer_seconds=.1 if method==12 else .5,png_seconds=.02,sha256=hashlib.sha256(b).hexdigest()))
  (out/f'play-0-{g}.bin').write_bytes(b);(out/f'play-0-{g}.png').write_bytes(png(b))
  events=([(2,429)] if g==2 else [(2,173)] if g==4 else [])+[(1,g)]
  for i,v in events:
   q=struct.pack('<10I',10,42,8,0,0,0,0,0,i,v)+bytes(1016);r=struct.pack('<8I',10,42,4,1,0,0,0,0)+bytes(1024)
   controls.append(dict(op=10,request=q.hex(),response=r.hex(),ns=100))
 for name,rows in [('play-frames',frames),('frame-journal',mail),('upload-journal',controls),('play-sessions',[dict(result=[0]*9+[2,1,210])])]:
  (out/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
 result=verify(out);assert result['dma_frames']==16 and result['paired_comparisons']==4 and result['pending_polls']==16
 # Mutate actual produced records, not the source oracle or raw files.
 path=out/'frame-dma-journal.jsonl';rows=[json.loads(l) for l in path.read_text().splitlines()]
 complete=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==2)
 read=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==3)
 cases=[(complete,'response',n) for n in range(32,96,4)]+[(read,'response',n) for n in (0,4,8,12,32,1055)]
 for i,field,offset in cases:
  old=rows[i][field];b=bytearray.fromhex(old);b[offset]^=1;rows[i][field]=b.hex();path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
  try:verify(out)
  except AssertionError:pass
  else:raise AssertionError('corrupt DMA record accepted')
  rows[i][field]=old
 print('PASS actual client: 16 guarded DMA buffers; 28 frames, four exact pairs, A/B/B/A, all ACK/input events; 22 mutations rejected')

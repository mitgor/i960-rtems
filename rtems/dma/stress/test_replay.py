#!/usr/bin/env python3
"""Actual DMA capture client, independent replay, and corruption rejection."""
import hashlib,json,struct,sys,tempfile,zlib
from pathlib import Path
from contextlib import nullcontext
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import frame_dma_client as client
import importlib.util
spec=importlib.util.spec_from_file_location('stress_verify',Path(__file__).with_name('verify.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);verify=module.verify
from types import SimpleNamespace
client.errno=SimpleNamespace(EAGAIN=11)
with tempfile.TemporaryDirectory() as directory:
 out=Path(directory);dma=client.FrameDMA(1,42,out,nullcontext());pending=False
 def pattern(g):return bytes(((i*13)^(i>>8)^(g*37))&255 for i in range(65536))
 def ioctl(fd,cmd,raw,mutate):
  global pending,capture,report
  op,e,g,off,*zero=struct.unpack_from('<8I',raw);assert cmd==0xc4204d08 and e==42 and not any(zero) and not any(raw[32:])
  if op==1:
   b=pattern(g);capture=b'\xa5'*4096+b+b'\xa5'*4096;c=zlib.crc32(b);report=[0x314d4446,2,g,0x101000,0xc0800000,c,c,0,0xc0f80000,0,0,7,5,0,0,0xc0f80000];pending=True
  elif op==2:
   if pending:pending=False;raise OSError(11,'pending')
   struct.pack_into('<16I',raw,32,*report)
  else:assert op==3;raw[32:]=capture[off:off+1024]
 client.fcntl.ioctl=ioctl
 frames=[];mail=[];controls=[]
 q=struct.pack('<10I',10,42,8,0,0,0,0,0,5,16)+bytes(1016);r=struct.pack('<8I',10,42,4,1,0,0,0,0)+bytes(1024)
 controls.append(dict(op=10,request=q.hex(),response=r.hex(),ns=100))
 for g in range(1,34):
  b,elapsed=dma.read(g);paired=g<=4 or g%32==0 or g==33
  frames.append(dict(frame=g,seconds=g,transfer_seconds=elapsed,paired=paired,sha256=hashlib.sha256(b).hexdigest()))
  if paired:
   for off in list(range(0,65536,1024))+[0]:
    q=struct.pack('<10I',11,42,8,0,0,0,0,0,g,off)+bytes(1016);r=struct.pack('<8I',11,42,1024,1,0,0,0,0)+b[off:off+1024]
    mail.append(dict(op=11,request=q.hex(),response=r.hex(),ns=100))
  q=struct.pack('<10I',10,42,8,0,0,0,0,0,1,g)+bytes(1016);r=struct.pack('<8I',10,42,4,1,0,0,0,0)+bytes(1024)
  controls.append(dict(op=10,request=q.hex(),response=r.hex(),ns=100))
 q=struct.pack('<10I',10,42,8,0,0,0,0,0,5,16)+bytes(1016);r=struct.pack('<9I',10,42,4,1,0,0,0,0,7)+bytes(1020)
 controls.append(dict(op=10,request=q.hex(),response=r.hex(),ns=100))
 owned=[]
 for op in (5,6):
  payload=struct.pack('<8I',0x3252444f,1,0,0,0,0,0,0)
  q=struct.pack('<8I',op,42,32 if op==6 else 0,0,0,0,0,0)+(payload+bytes(992) if op==6 else bytes(1024))
  r=struct.pack('<8I',op,42,32,1,0,0,0,0)+(struct.pack('<8I',0x3252444f,1,1,0,0,0,0,0) if op==5 else payload)+bytes(992)
  owned.append(dict(op=op,request=q.hex(),response=r.hex(),ns=100))
 for name,rows in [('stress-frames' ,frames),('frame-journal',mail),('upload-journal',controls),('owned-journal',owned)]:
  (out/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
 (out/'stress-result.json').write_text(json.dumps(dict(isolation_checks=7,frames=33,zero_wad_reads=True,manifest=dict(dma_stress=1),result=[0x454e4750,3,65536,0,0,33,0,0,0,2,1,210],reply=[0,0,0,0,0,0x454e4702])))
 assert verify(out)['paired']==6
 path=out/'frame-dma-journal.jsonl';rows=[json.loads(l) for l in path.read_text().splitlines()]
 complete=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==2)
 read=next(i for i,r in enumerate(rows) if 'response' in r and bytes.fromhex(r['request'])[0]==3)
 cases=[(complete,n) for n in range(32,96,4)]+[(read,n) for n in (0,4,8,12,32,1055)]
 for i,offset in cases:
  old=rows[i]['response'];b=bytearray.fromhex(old);b[offset]^=1;rows[i]['response']=b.hex();path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
  try:verify(out)
  except AssertionError:pass
  else:raise AssertionError('corrupt DMA record accepted')
  rows[i]['response']=old
 print('PASS 33 real-client captures, six full mailbox pairs, 22 corruptions rejected')

#!/usr/bin/env python3
"""Actual client and independent replay, with malformed evidence rejection."""
import errno,json,struct,sys,tempfile,threading
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'rtems/residentnet'));sys.path.insert(0,str(Path(__file__).resolve().parent))
import wad_ring_client as client
from verify import verify

def record(m,g,off,n,total):return struct.pack('<16I',m,g,(g-1)&1,off,n,total,g^0xffffffff,g,*([0]*8))
with tempfile.TemporaryDirectory() as d:
 p=Path(d)
 data=bytearray((i*7^(i>>9))&255 for i in range(100003));struct.pack_into('<4sII',data,0,b'IWAD',1,96)
 (p/'test.wad').write_bytes(data);served={};pending=[1,2]
 def ioctl(fd,command,raw,mutable):
  assert command==0xc0204d0b and mutable
  op,e,slot,g,off,n,total,z=struct.unpack_from('<8I',raw);assert e==42 and total==len(data) and not z
  payload=bytearray(32768)
  if op==1:struct.pack_into('<2I',payload,0,0x100000,0x110000)
  elif op==2:
   if g>4 or g!=pending[slot]:raise OSError(errno.EAGAIN,'pending')
   off=(g-1)*32768;n=min(32768,total-off);payload[:64]=record(0x31515257,g,off,n,total)
   if g>2:payload[64:128]=record(0x31435257,g-2,(g-3)*32768,32768,total)
  elif op==3:
   assert raw[32:]==data[off:off+n].ljust(32768,b'\0');assert g==pending[slot] and g not in served
   served[g]=(off,n);pending[slot]+=2;payload[:64]=record(0x31535257,g,off,n,total)
  elif op==4:
   off,n=served[g]
   for i,m in enumerate((0x31515257,0x31535257,0x31435257)):payload[64*i:64*(i+1)]=record(m,g,off,n,total)
  else:assert False
  raw[32:]=payload
 client.fcntl.ioctl=ioctl
 u=SimpleNamespace(fd=1,epoch=42,out=p,gate=threading.RLock())
 s=client.RingServer(u,p/'test.wad');s.enable();assert s.serve() and s.serve() and not s.serve();s.finish()
 (p/'play-wad.json').write_text(json.dumps(dict(sha256=s.sha,bytes=len(data),requests=len(s.records))))
 assert verify(p,p/'test.wad')['blocks']==4
 path=p/'wad-ring-journal.jsonl';rows=[json.loads(x) for x in path.read_text().splitlines()];mutations=[]
 for index,row in enumerate(rows):
  op=struct.unpack_from('<I',bytes.fromhex(row['request']))[0]
  if op in (2,3,4):
   for byte in (32,36,40,44,48,52,56,60,64):mutations.append((index,'response',byte))
  if op==3:mutations.append((index,'request',100))
 def rejected(changed):
  path.write_text(''.join(json.dumps(x)+'\n' for x in changed))
  try:verify(p,p/'test.wad')
  except (AssertionError,KeyError,ValueError):return
  raise AssertionError('tampered evidence accepted')
 for index,field,byte in mutations:
  changed=[dict(x) for x in rows];b=bytearray.fromhex(changed[index][field]);b[byte]^=1;changed[index][field]=b.hex();rejected(changed)
 rejected(rows[:-1]);rejected(rows[:3]+rows[4:]);rejected(rows+[rows[-1]])
print(f'PASS actual ring client/replay: two slots, EOF, RAM-only polling; {len(mutations)+3} evidence mutations rejected')

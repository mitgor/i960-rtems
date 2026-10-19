import tempfile,socket,struct,json,time
from pathlib import Path
from host import Runtime,ADDRESS
with tempfile.TemporaryDirectory() as tmp:
 path=str(Path(tmp)/'runtime.sock');r=Runtime(path,Path(tmp)/'log');page=bytearray(4096);writes=[]
 struct.pack_into('<4I',page,416*4,0x31525041,0,0,23)
 def snap(a):assert a==ADDRESS;return bytes(page)
 def write(a,off,data):
  assert a==ADDRESS and off+len(data)<=4096;writes.append((off,data));page[off:off+len(data)]=data
 def connect(msg):
  c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(path);c.setblocking(False);c.sendall((json.dumps(msg)+'\n').encode());return c
 c=connect(dict(op=5,data=b'ping'.hex()));r.pump(snap,write)
 assert [x[0] for x in writes]==[64,4,0] and r.pending==5
 assert struct.unpack_from('<4I',page)==(1,23,5,4)
 struct.pack_into('<11I',page,416*4,0x31525041,1,0,23,4,3,257,0,0,10,1);page[432*4:432*4+4]=b'pong'
 r.pump(snap,write);r.pump(snap,write);reply=json.loads(c.recv(4096));assert bytes.fromhex(reply['data'])==b'pong';c.close()
 c=connect(dict(op=7));r.pump(snap,write);c.close()
 struct.pack_into('<11I',page,416*4,0x31525041,2,0,23,0,3,257,0,0,11,1)
 r.pump(snap,write);r.pump(snap,write)
 assert r.client is None and not r.disabled and r.pending is None
 c=connect(dict(op=5,data=''));r.pump(snap,write);r.until=0;r.pump(snap,write);r.pump(snap,write)
 assert r.disabled and 'retained' in json.loads(c.recv(4096))['error'];c.close()
 before=len(writes);c=connect(dict(op=6));r.pump(snap,write);r.pump(snap,write)
 assert 'quarantined' in json.loads(c.recv(4096))['error'] and len(writes)==before;c.close();r.close()
print('owner RPC: bounded publication, exact reply payload, uncertain timeout quarantine, no release writes after uncertainty passed')
# DMA completion cannot fall back to a PIO payload or accept an old generation.
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);r=Runtime(p/'s',p/'log');r.pin=p
 page=bytearray(4096);struct.pack_into('<4I',page,416*4,0x31525041,0,0,23);struct.pack_into('<I',page,427*4,0x31414d44)
 snaps=[];writes=[]
 def snap(a):snaps.append(a);return bytes(page)
 def write(a,o,b):writes.append((o,b));page[o:o+len(b)]=b
 c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(p/'s'));c.sendall(b'{"op":7,"transport":"dma"}\n');r.pump(snap,write)
 assert r.pending_dma and struct.unpack_from('<I',page,20)[0]==1
 (p/'marker0.bin').write_bytes(bytes(32));count=len(snaps);r.pump(snap,write);assert r.pending and len(snaps)==count
 struct.pack_into('<11I',page,416*4,0x31525041,1,0,23,4,3,257,0,0,10,1);page[1728:1732]=b'test'
 (p/'frame0.bin').write_bytes(bytes(4096)+page)
 marker=struct.pack('<8I',0x31525044,23,1,0,4096,ADDRESS+4096,(~23)&0xffffffff,(~1)&0xffffffff)
 (p/'marker0.bin').write_bytes(marker);r.pump(snap,write);r.pump(snap,write)
 result=json.loads(c.recv(8192));assert result['transport']=='dma' and result['data']==b'test'.hex() and len(snaps)==count;c.close()
 c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(p/'s'));c.sendall(b'{"op":7,"transport":"dma"}\n');r.pump(snap,write);r.until=0;r.pump(snap,write);assert r.disabled and len(snaps)==count
 r.pump(snap,write);assert 'retained' in json.loads(c.recv(8192))['error'];c.close();r.close()
print('packet DMA host: capability, exact sequence/epoch, stale-marker wait, no PIO fallback and timeout quarantine passed')
# A successful CLOSE increments the runtime epoch; arbitrary epoch changes do not.
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);r=Runtime(p/'s',p/'log');page=bytearray(4096)
 struct.pack_into('<4I',page,416*4,0x31525041,0,0,23)
 def snap(a):return bytes(page)
 def write(a,o,b):page[o:o+len(b)]=b
 c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(p/'s'));c.sendall(b'{"op":6}\n');r.pump(snap,write)
 struct.pack_into('<11I',page,416*4,0x31525041,1,0,24,0,0,0,0,0,0,0)
 r.pump(snap,write);r.pump(snap,write);assert json.loads(c.recv(8192))['epoch']==24 and r.epoch==24;c.close();r.close()
print('owner RPC: successful CLOSE epoch transition accepted')
for corrupt in (False,True):
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);r=Runtime(p/'s',p/'log');r.pin=p;page=bytearray(4096)
  struct.pack_into('<4I',page,416*4,0x31525041,0,0,23);struct.pack_into('<I',page,427*4,0x31414d44)
  def snap(a):return bytes(page)
  def write(a,o,b):page[o:o+len(b)]=b
  c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(p/'s'));c.sendall(b'{"op":7,"transport":"dma-check"}\n');r.pump(snap,write)
  struct.pack_into('<11I',page,416*4,0x31525041,1,0,23,0,3,257,0,0,10,1)
  copied=bytearray(page)
  if corrupt:copied[2000]^=1
  (p/'frame0.bin').write_bytes(bytes(4096)+copied)
  (p/'marker0.bin').write_bytes(struct.pack('<8I',0x31525044,23,1,0,4096,ADDRESS+4096,(~23)&0xffffffff,(~1)&0xffffffff))
  r.pump(snap,write);r.pump(snap,write);result=json.loads(c.recv(8192))
  assert r.disabled==corrupt
  if corrupt:assert 'mismatch' in result['error']
  else:assert result['transport']=='dma'
  c.close();r.close()
print('DMA/PIO diagnostic: complete page comparison, corruption detection and quarantine passed')
# A matching sequence with malformed marker fields is fail-closed; it is never
# enough to read/reuse a target. This also documents conservative torn-read policy.
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);r=Runtime(p/'s',p/'log');r.pin=p;page=bytearray(4096)
 struct.pack_into('<4I',page,416*4,0x31525041,0,0,23);struct.pack_into('<I',page,427*4,0x31414d44)
 def snap(a):return bytes(page)
 def write(a,o,b):page[o:o+len(b)]=b
 c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(p/'s'));c.sendall(b'{"op":7,"transport":"dma"}\n');r.pump(snap,write)
 (p/'marker0.bin').write_bytes(struct.pack('<8I',0x31525044,23,1,0,4096,ADDRESS+4096,(~23)&0xffffffff,0))
 r.pump(snap,write);r.pump(snap,write);assert r.disabled and 'marker identity' in json.loads(c.recv(8192))['error'];c.close();r.close()
print('DMA malformed/partially matching marker: fail-closed before target read')

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

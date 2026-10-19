#!/usr/bin/env python3
"""Root console-side client. All PCI is performed by the existing owner."""
import os,argparse,json,socket,struct,zlib,time
from pathlib import Path
class Client:
 def __init__(self,path=None):self.path=path or os.environ.get('I960_RUNTIME_SOCKET','/run/i960-rtems-runtime.sock')
 def call(self,op,data=b''):
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
   s.settimeout(12);s.connect(self.path);s.sendall((json.dumps(dict(op=op,data=data.hex()))+'\n').encode());reply=b''
   while b'\n' not in reply:
    chunk=s.recv(8192)
    if not chunk:raise RuntimeError('runtime disconnected')
    reply+=chunk
    if len(reply)>16384:raise RuntimeError('oversize runtime reply')
  result=json.loads(reply)
  if 'error' in result:raise RuntimeError(result['error'])
  if result['status']:raise RuntimeError(result)
  return result
 def upload(self,path):
  path=Path(path);m=json.loads((path/'manifest.json').read_text());b=(path/'module.bin').read_bytes()
  import hashlib
  assert hashlib.sha256(b).hexdigest()==m['sha256']
  segs=m['segments'];assert 1<=len(segs)<=8
  manifest=[1,len(segs),m['entry']]
  for seg in segs:manifest.extend(seg[k] for k in ('offset','file_bytes','memory_bytes','flags','crc32'))
  manifest.extend([0]*(5*(8-len(segs))))
  self.call(1,struct.pack('<%dI'%(3+len(manifest)),m['board'],m['abi'],m['base'],*manifest))
  for i,seg in enumerate(segs):
   for off in range(0,seg['file_bytes'],1016):
    part=b[seg['offset']+off:seg['offset']+min(seg['file_bytes'],off+1016)]
    self.call(2,struct.pack('<II',i,off)+part)
  for _ in range(1024):
   r=self.call(3)
   if r['value']==2:break
  else:raise RuntimeError('bounded prepare did not finish')
  return self.call(4)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=('query','stop','upload'));p.add_argument('module',nargs='?');a=p.parse_args();c=Client()
 print(json.dumps(c.upload(a.module) if a.operation=='upload' else c.call(7 if a.operation=='query' else 6),indent=2))

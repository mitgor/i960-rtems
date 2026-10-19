#!/usr/bin/env python3
import json,tempfile,threading,socket,time
from pathlib import Path
from broker import Broker,Scheduler
s=Scheduler()
for i in range(9):s.put(('n',i),True)
for i in range(3):s.put(('a',i),False)
assert [s.pop()[0] for _ in range(12)]==list('nnnannnannna')
with tempfile.TemporaryDirectory() as d:
 calls=[];stop=threading.Event()
 def backend(op,payload):calls.append((op,payload));return dict(status=0,op=op,data=payload.hex())
 b=Broker(Path(d)/'s',backend,Path(d)/'log')
 def serve():
  while not stop.is_set():b.once()
 t=threading.Thread(target=serve);t.start()
 try:
  from client import Client
  c=Client(str(Path(d)/'s'));assert c.call(5,b'\x60abc')['data']=='60616263'
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as peer:
   peer.connect(str(Path(d)/'s'));peer.sendall(b'{"op":7}\n')
  time.sleep(.05);assert c.call(7)['status']==0
  try:c.call(99)
  except RuntimeError:pass
  else:raise AssertionError('invalid op accepted')
  assert not any(op==99 for op,_ in calls)
  assert c.call(5,b'\xf1APP')['status']==0
 finally:stop.set();t.join(2);b.close()
print('broker: 3:1 arbitration, request bounds, completed disconnect, reconnect and no retry passed')
# Every peer is queued before the first poll: ingress classification must finish
# before dispatch. Accept-one/dispatch-one would service the first application.
with tempfile.TemporaryDirectory() as d:
 order=[]
 def backend(op,payload):order.append('n' if op==5 else 'a');return dict(status=0)
 b=Broker(Path(d)/'s',backend,Path(d)/'log');peers=[]
 try:
  for op in [7]*3+[5]*9:
   peer=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);peer.settimeout(1);peer.connect(str(Path(d)/'s'));peer.sendall((json.dumps(dict(op=op,data='60' if op==5 else ''))+'\n').encode());peers.append(peer)
  for _ in range(30):b.once()
  assert order==list('nnnannnannna'),order
  for peer in peers:assert json.loads(peer.recv(1024))['status']==0
 finally:
  for peer in peers:peer.close()
  b.close()
print('broker: actual socket ingress batch observes the 3:1 scheduling order')

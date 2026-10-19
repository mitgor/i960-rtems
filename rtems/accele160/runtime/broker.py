#!/usr/bin/env python3
"""Bounded scheduling in front of the existing owner; never maps PCI itself."""
import types,argparse,collections,json,selectors,socket,time,logging,logging.handlers,os
from pathlib import Path
from client import Client
class Scheduler:
 def __init__(self):self.q={'network':collections.deque(),'application':collections.deque()};self.credit=3
 def put(self,item,network):self.q['network' if network else 'application'].append(item)
 def pop(self):
  n,a=self.q['network'],self.q['application']
  if n and (self.credit or not a):self.credit=max(0,self.credit-1);return n.popleft()
  if a:self.credit=3;return a.popleft()
  return None
class Broker:
 def __init__(self,path,backend,journal):
  self.path=Path(path);self.backend=backend;self.schedule=Scheduler();self.sel=selectors.DefaultSelector();self.peers={};self.sequence=0
  self.log=logging.getLogger('combined-broker');self.log.setLevel(logging.INFO)
  self.handler=logging.handlers.RotatingFileHandler(journal,maxBytes=2*1024*1024,backupCount=1);self.log.addHandler(self.handler)
  self.listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.listener.bind(str(path));os.chmod(path,0o600);self.listener.listen(16);self.listener.setblocking(False);self.sel.register(self.listener,selectors.EVENT_READ,None)
 def retire(self,p):
  if not p['live']:return
  p['live']=False;self.peers.pop(p['sock'],None)
  try:self.sel.unregister(p['sock'])
  except KeyError:pass
  p['sock'].close()
 def reply(self,p,result):
  p['reply']=(json.dumps(result)+'\n').encode();p['until']=time.monotonic()+2
  self.sel.modify(p['sock'],selectors.EVENT_WRITE,p)
 def once(self):
  events=self.sel.select(.01)
  for key,mask in events:
   if key.data is None:
    # Classify all already-arrived requests before choosing the next backend
    # operation; otherwise accept-one/dispatch-one defeats queue priorities.
    for _ in range(16):
     try:conn,_=self.listener.accept()
     except BlockingIOError:break
     conn.setblocking(False)
     if len(self.peers)>=16:conn.close();continue
     p=dict(sock=conn,live=True,data=b'',reply=b'',queued=False,until=time.monotonic()+2)
     self.peers[conn]=p;self.sel.register(conn,selectors.EVENT_READ,p)
     events.append((types.SimpleNamespace(data=p),selectors.EVENT_READ))
    continue
   p=key.data
   try:
    if mask&selectors.EVENT_WRITE:
     n=p['sock'].send(p['reply']);p['reply']=p['reply'][n:]
     if not p['reply']:self.retire(p)
    else:
     b=p['sock'].recv(4097-len(p['data']))
     if not b:self.retire(p);continue
     if p['queued']:self.retire(p);continue
     p['data']+=b
     if len(p['data'])>4096:raise ValueError('request too large')
     if b'\n' not in p['data']:continue
     req=json.loads(p['data']);op=req['op'];data=bytes.fromhex(req.get('data',''))
     if type(op)!=int or not 1<=op<=9 or len(data)>1500:raise ValueError('request bounds')
     network=op==5 and (not data or data[0]>>4 in (4,6))
     p.update(op=op,payload=data,kind='network' if network else 'application',queued=True,arrival=time.monotonic(),until=time.monotonic()+5)
     self.schedule.put(p,network)
   except BlockingIOError:pass
   except (ValueError,KeyError,TypeError) as e:self.reply(p,dict(error=str(e)))
   except OSError:self.retire(p)
  for p in list(self.peers.values()):
   if time.monotonic()>p['until']:self.retire(p)
  for kind,q in self.schedule.q.items():self.schedule.q[kind]=collections.deque(p for p in q if p['live'])
  p=self.schedule.pop()
  if p is None or not p['live']:return
  # Before dispatch a dead/expired peer can be forgotten. After dispatch the
  # owner's actual result is authoritative; no automatic operation retry.
  start=time.monotonic();self.sequence+=1
  try:result=self.backend(p['op'],p['payload'])
  except RuntimeError as e:result=e.args[0] if e.args and isinstance(e.args[0],dict) else dict(error=str(e))
  except OSError as e:result=dict(error=str(e))
  self.log.info(json.dumps(dict(sequence=self.sequence,kind=p['kind'],op=p['op'],wait_ms=(start-p['arrival'])*1000,backend_ms=(time.monotonic()-start)*1000,status=result.get('status'),error=result.get('error'))))
  self.reply(p,result)
 def close(self):
  for p in list(self.peers.values()):self.retire(p)
  self.sel.unregister(self.listener);self.listener.close();self.sel.close();self.path.unlink(missing_ok=True);self.handler.close();self.log.removeHandler(self.handler)
def main():
 p=argparse.ArgumentParser();p.add_argument('--socket',default='/run/i960-combined.sock');p.add_argument('--journal',required=True);a=p.parse_args()
 client=Client('/run/i960-rtems-runtime.sock');b=Broker(a.socket,client.call,a.journal)
 try:
  while True:b.once()
 finally:b.close()
if __name__=='__main__':main()

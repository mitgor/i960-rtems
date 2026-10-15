#!/usr/bin/env python3
"""Temporary host-only keyboard correction for an already-running play owner.
Duplicate its existing file description; never open a new card session. The
kernel session mutex serializes status/key ioctls with the owner's frame reader.
No upload, frame selection, ACK or direct STOP is issued by this bridge.
"""
import argparse,ctypes,fcntl,json,os,re,secrets,select,signal,struct,threading,time,urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--fd',type=int,required=True);p.add_argument('--epoch',type=int,required=True);p.add_argument('--port',type=int,default=8088);p.add_argument('--upstream',default='http://127.0.0.1:8087');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert os.geteuid()==0 and 0<a.epoch<65536 and 1024<=a.port<=65535
assert os.readlink(f'/proc/{a.pid}/fd/{a.fd}')=='/dev/i960-auto'
a.output.mkdir(exist_ok=False,parents=True)
pidfd=os.pidfd_open(a.pid);lib=ctypes.CDLL(None,use_errno=True);fd=lib.syscall(438,pidfd,a.fd,0)
if fd<0:raise OSError(ctypes.get_errno(),'pidfd_getfd')
page=urllib.request.urlopen(a.upstream,timeout=2).read().decode();oldtoken=re.search("const token='([^']+)'",page)[1];token=secrets.token_hex(24)
page=(Path(__file__).with_name('index.html').read_text().replace('__TOKEN__',token)).encode()
# This legacy bridge cannot attest the running image's runtime-detail option.
page=page.replace(b'<button id="detail">Toggle detail (F5)</button>',b'')
keys=deque();held=set();deadline=0.;lock=threading.Lock();stop=threading.Event();reason=[]
allowed=(173,175,172,174,163,162,182,191,13,27,9,121,110,49,50,51,52,53,54,55)
def upstream(path,data=None):
 req=urllib.request.Request(a.upstream+path,data=data,headers={'X-Session-Token':oldtoken,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=2) as r:return r.read(),r.headers.get('Content-Type','application/json')
def ctl(action=0,value=0):
 raw=bytearray(struct.pack('<10I',10,a.epoch,8,0,0,0,0,0,action,value)+bytes(1016));before=raw.hex();start=time.monotonic_ns()
 try:fcntl.ioctl(fd,0xc4204d06,raw,True)
 except OSError as e:
  with (a.output/'keys.jsonl').open('a') as f:f.write(json.dumps(dict(request=before,errno=e.errno,start_ns=start))+'\n')
  raise
 with (a.output/'keys.jsonl').open('a') as f:f.write(json.dumps(dict(request=before,response=raw.hex(),start_ns=start,ns=time.monotonic_ns()-start))+'\n')
 w=struct.unpack_from('<9I',raw);assert w[2]==4 and w[3]==1 and not w[4]&1 and w[5:8]==(0,0,0),w
 return w[8]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,code,data,kind='application/json'):
  self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers()
  try:self.wfile.write(data)
  except (BrokenPipeError,ConnectionResetError):pass
 def do_GET(self):
  try:
   if self.path=='/':self.reply(200,page,'text/html; charset=utf-8')
   elif self.path=='/status' or self.path.startswith('/frame.png?'):self.reply(200,*upstream(self.path))
   else:self.reply(404,b'not found')
  except Exception:self.reply(503,b'upstream session ended')
 def do_POST(self):
  global deadline
  if self.headers.get('X-Session-Token')!=token or self.headers.get('Origin') not in (None,'http://'+self.headers.get('Host','')):self.reply(403,b'forbidden');return
  try:
   n=int(self.headers.get('Content-Length','0'));assert 0<n<=128;b=json.loads(self.rfile.read(n))
   if self.path=='/stop':
    stop.set()
    try:
     worker.join(12)
     if worker.is_alive():self.reply(503,b'input worker still closing');return
     upstream('/stop',b'{}');self.reply(200,b'{}')
    finally:threading.Thread(target=http.shutdown,daemon=True).start()
    return
   with lock:
    if stop.is_set():self.reply(409,b'input stopped');return
    if self.path=='/heartbeat':deadline=time.monotonic()+3
    elif self.path=='/key':
     assert type(b['key']) is int and b['key'] in allowed and type(b['down']) is int and b['down'] in (0,1)
     if len(keys)>=96:
      stop.set();threading.Thread(target=stop_and_close,daemon=True).start();self.reply(429,b'key queue full; stopping');return
     keys.append(b['key']+(b['down']<<8));deadline=time.monotonic()+3
     if b['down']:held.add(b['key'])
     else:held.discard(b['key'])
    else:self.reply(404,b'not found');return
   self.reply(200,b'{}')
  except (ValueError,KeyError,AssertionError):self.reply(400,b'invalid request')
  except Exception:self.reply(503,b'upstream session ended')
http=ThreadingHTTPServer(('0.0.0.0',a.port),Handler)
def pump():
 lastg=0;lastcheck=0;session=None
 try:
  while not stop.wait(.1):
   if select.select([pidfd],[],[],0)[0]:raise RuntimeError('owner process exited')
   if time.monotonic()-lastcheck>1:
    st=json.loads(upstream('/status')[0]);new=st.get('frame','').split('-')[0];lastcheck=time.monotonic()
    if session is not None and new!=session:
     with lock:keys.clear();held.clear()
     lastg=0
    session=new
   with lock:
    if held and time.monotonic()>deadline:keys.extend(sorted(held));held.clear()
    pending=bool(keys)
   if not pending:continue
   g=ctl()
   if not g or g==lastg:continue
   if g==0xffffffff:raise RuntimeError('frame channel refused')
   lastg=g;changed=set()
   with lock:
    while keys and not stop.is_set():
     value=keys[0];key=value&255
     if key in changed:break # preserve short taps across game updates
     result=ctl(2,value)
     if result==0xffffffff:break # explicit bounded refusal only
     assert result==0
     keys.popleft();changed.add(key)
 except BaseException as e:
  reason.append(repr(e));stop.set()
  try:upstream('/stop',b'{}') # no further direct ioctls; original owner handles cancellation
  except Exception as failure:reason.append('upstream STOP: '+repr(failure))
  threading.Thread(target=http.shutdown,daemon=True).start()
def stop_and_close():
 stop.set();worker.join()
 try:upstream('/stop',b'{}')
 except Exception as failure:reason.append('upstream STOP: '+repr(failure))
 finally:http.shutdown()
worker=threading.Thread(target=pump,daemon=True);worker.start()
for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:threading.Thread(target=stop_and_close,daemon=True).start())
(a.output/'identity.json').write_text(json.dumps(dict(pid=a.pid,source_fd=a.fd,epoch=a.epoch,port=a.port,boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),note='duplicated existing file description; main remains sole ACK/STOP owner'))+'\n')
try:http.serve_forever()
finally:
 stop.set();worker.join();http.server_close();os.close(fd);os.close(pidfd)
 (a.output/'closed.json').write_text(json.dumps(dict(reason=reason,closed=time.time()))+'\n')

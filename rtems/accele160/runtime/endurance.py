#!/usr/bin/env python3
"""Bounded mixed card traffic; fixed acceptance limits, no silent retry."""
import argparse,json,time,threading,urllib.request,socket,struct
from pathlib import Path
from service import Service
p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=600);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
if not 10<=a.seconds<=28800:raise SystemExit('duration 10..28800 seconds')
end=time.monotonic()+a.seconds;rows=[];errors=[];lock=threading.Lock()
def record(kind,start,**data):
 row=dict(kind=kind,time=time.monotonic(),ms=(time.monotonic()-start)*1000,**data)
 with lock:rows.append(row)
def traffic():
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 while time.monotonic()<end:
  for url in ('http://10.196.0.2/','http://[fd96:196:960::2]/'):
   start=time.monotonic()
   with opener.open(url,timeout=5) as r:
    b=r.read();assert r.status==200 and b'AcceleRAID 160' in b
   assert time.monotonic()-start<5;record('http',start,url=url,bytes=len(b))
  for family,ip in ((socket.AF_INET,'10.196.0.2'),(socket.AF_INET6,'fd96:196:960::2')):
   start=time.monotonic()
   with socket.socket(family,socket.SOCK_DGRAM) as s:
    s.settimeout(3);s.sendto(b'combined-endurance',(ip,9601));b,_=s.recvfrom(1500);assert b==b'combined-endurance'
   record('udp',start,ip=ip)
  time.sleep(.1)
def console():
 s=Service()
 while time.monotonic()<end:
  for command in ('uptime','tasks','mem','apps'):
   start=time.monotonic();text=s.console(command);assert text and 'error' not in text
   if command=='tasks':assert 'fault=0' in text
   assert time.monotonic()-start<5;record('console',start,command=command,text=text)
  time.sleep(.3)
def apps():
 s=Service();rounds=0;last_updates=0
 for i in (1,2):
  r=s.app(3,i)
  if not r['running']:s.app(1,i,r['generation'])
 while time.monotonic()<end:
  start=time.monotonic();r=s.app(3,1);assert r['running'] and r['updates']>=last_updates;last_updates=r['updates'];record('counter',start,**r)
  start=time.monotonic();g=s.app(3,2)['generation'];r=s.app(4,2,g,b'hello from concurrent app');assert r['text']=='HELLO FROM CONCURRENT APP';assert time.monotonic()-start<3;record('echo',start,**r)
  rounds+=1
  if rounds%10==0:
   start=time.monotonic();old=s.app(3,1)['generation'];s.app(2,1,old);stopped=s.app(3,1);assert not stopped['running']
   new=s.app(1,1,old);assert new['generation']==old+1
   stale=s.app(2,1,old,allow_error=True);assert stale['status']==4 and stale['running'];last_updates=0
   record('restart',start,generation=new['generation'],stale_stop=stale)
  time.sleep(.2)
def guarded(fn):
 try:fn()
 except BaseException as e:
  with lock:errors.append(dict(worker=fn.__name__,error=repr(e)))
threads=[threading.Thread(target=guarded,args=(fn,)) for fn in (traffic,console,apps)]
start=time.monotonic()
for t in threads:t.start()
while any(t.is_alive() for t in threads):
 with lock:a.out.write_text(json.dumps(dict(duration_s=time.monotonic()-start,limits=dict(http_s=5,console_s=5,app_echo_s=3),errors=errors,rows=rows),indent=2)+'\n')
 for t in threads:t.join(.1)
with lock:a.out.write_text(json.dumps(dict(duration_s=time.monotonic()-start,limits=dict(http_s=5,console_s=5,app_echo_s=3),errors=errors,rows=rows),indent=2)+'\n')
for kind in ('http','udp','console','counter','echo','restart'):
 assert any(r['kind']==kind for r in rows),kind
assert not errors,errors
print(json.dumps(dict(duration_s=time.monotonic()-start,events=len(rows),errors=errors,max_ms={kind:max(r['ms'] for r in rows if r['kind']==kind) for kind in ('http','udp','console','counter','echo','restart')}),indent=2))

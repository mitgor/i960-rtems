#!/usr/bin/env python3
"""Actual uninterrupted IRQ execution inside a renewable parked-callback lease."""
import argparse,concurrent.futures,errno,json,struct,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'switch'))
from live_concurrent import ioctl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture

def session(a,name,commands):
 b=Board(a.payload,a.module,a.output/name);rows=[];identity=None;frozen=None
 def call(gen,op,duration=0,expire=False,grant=True,arg=0,silent=False,cap=False):
  nonlocal identity,frozen
  request=struct.pack('<4I',0x31515250,gen,op,arg);epoch=b.sequence+1;controls=[]
  def ctl(action,e=epoch):
   t=time.monotonic()
   try:r=ioctl(b.fd,action,e)
   except OSError as error:
    controls.append(dict(action=action,epoch=e,seconds=t,errno=error.errno));raise
   controls.append(dict(action=action,epoch=e,seconds=t,reply=r));return r
  if op in (1,2,3):
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    work=pool.submit(b.step,request);deadline=time.monotonic()+3
    while True:
     assert not work.done(),'callback returned before lease control'
     try:
      if ctl(0)[4]==0x71000000|epoch:break
     except OSError as e:assert e.errno==errno.EAGAIN
     assert time.monotonic()<deadline;time.sleep(.005)
    for action in (0,2,3):
     try:ctl(action,epoch+123);raise AssertionError('stale epoch accepted')
     except OSError as e:assert e.errno==errno.ESTALE
    try:ctl(3);raise AssertionError('renew before grant accepted')
    except OSError as e:assert e.errno==errno.EPERM
    if grant:
     ctl(2)
     try:ctl(2);raise AssertionError('duplicate grant accepted')
     except OSError as e:assert e.errno==errno.EALREADY
    start=time.monotonic();next_renew=start
    if silent:time.sleep(duration)
    else:
     while True:
      now=time.monotonic();r=ctl(0)
      if r[4]==0x75000000|epoch:
       assert expire or cap,'unexpected local expiry';break
      if not expire and not cap and now-start>=duration:break
      if grant and not expire and now>=next_renew:ctl(3);next_renew=now+.2
      assert now-start<120;assert not work.done();time.sleep(.01)
    reply=ctl(1);assert reply[6:8]==[0x75000000|epoch,1]
    data=work.result(timeout=3)
   (b.out/f'control-{epoch:06d}.json').write_text(json.dumps(dict(grant=grant,expire=expire,silent=silent,cap=cap,duration=duration,elapsed=time.monotonic()-start,records=controls),indent=2)+'\n')
  else:data=b.step(request)
  w=list(struct.unpack('<352I',data));assert w[:3]==[0x31515250,1,0] and w[4]==epoch
  ident=w[60:64]+w[72:76]+w[288:291]
  if identity is None:identity=ident
  assert ident==identity
  if w[33]==4:
   if frozen is None:frozen=w[80:84]
   assert w[80:88]==frozen*2
  if op in (1,2,3):
   assert w[323]==(3 if cap else 2 if expire else 1)
   assert bool(w[324])==grant
   assert not w[331] and w[330]==w[8]-w[9]
  rows.append(dict(request=[gen,op,arg],words=w));(b.out/'reports.json').write_text(json.dumps(rows,indent=2)+'\n');(b.out/'last-step.txt').write_text((b.debugfs/'result.txt').read_text())
  print(json.dumps(dict(run=name,seq=epoch,op=op,ticks=w[8],lease_ticks=w[347]-w[346],renewals=w[326],reason=w[323],hw_checks=w[330])),flush=True)
  return w
 try:
  for command in commands:call(**command)
  print(json.dumps(b.close()),flush=True)
 except BaseException:
  import os
  if b.fd is not None:os.close(b.fd);b.fd=None;capture(b.out/'failed-close',b.debugfs)
  if b.records:b.records.close()
  if b.lock:b.lock.close()
  raise

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--cap-only',action='store_true');p.add_argument('--matrix',action='store_true');p.add_argument('--soak',type=float,default=30);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 if a.cap_only:
  session(a,'cap',[dict(gen=1,op=1,cap=True),dict(gen=1,op=5)]);return
 session(a,'smoke',[dict(gen=1,op=1,duration=1),dict(gen=1,op=5)])
 if not a.matrix:return
 for grant in (True,False):session(a,'expiry-'+str(grant),[dict(gen=1,op=1,expire=True,grant=grant),dict(gen=1,op=5)])
 session(a,'silent',[dict(gen=1,op=1,duration=1,silent=True),dict(gen=1,op=5)])
 session(a,'chain',[dict(gen=1,op=1,duration=1),dict(gen=2,op=1,duration=2),dict(gen=3,op=2,duration=1),dict(gen=3,op=3,duration=1),dict(gen=3,op=4,arg=3),dict(gen=3,op=3,expire=True),dict(gen=3,op=5)])
 session(a,'soak',[dict(gen=1,op=1,duration=a.soak),dict(gen=1,op=5)])
if __name__=='__main__':main()

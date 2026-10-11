#!/usr/bin/env python3
"""Persistent card sessions: actual dependency chains and asynchronous epochs."""
import argparse,concurrent.futures,errno,json,os,struct,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'switch'))
from live_concurrent import ioctl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture

def exchange(b,gen,op,arg):
 request=struct.pack('<4I',0x31515250,gen,op,arg);epoch=b.sequence+1
 if op not in (1,2,3):return b.step(request)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  work=pool.submit(b.step,request);deadline=time.monotonic()+3
  while True:
   assert not work.done(),'callback returned before control'
   try:
    status=ioctl(b.fd,0,epoch)
    if status[4]==0x71000000|epoch:break
   except OSError as e:assert e.errno==errno.EAGAIN
   assert time.monotonic()<deadline;time.sleep(.001)
  reply=ioctl(b.fd,1,epoch)
  (b.out/f'control-{epoch:06d}.json').write_text(json.dumps(dict(status=status,reply=reply,epoch=epoch),indent=2)+'\n')
  assert reply[6]==0x75000000|epoch and reply[7]==1 and not(reply[3]&1) and not(reply[5]&1)
  return work.result(timeout=3)

def session(a,index):
 b=Board(a.payload,a.module,a.output/f'run-{index}');rows=[];identity=None;frozen=None
 def call(gen,op,arg=0,status=0):
  nonlocal identity,frozen
  data=exchange(b,gen,op,arg);w=list(struct.unpack('<320I',data));assert w[:3]==[0x31515250,1,status],w[:8]
  assert w[3:5]==[op,b.sequence] and w[319]==b.sequence
  ident=w[60:64]+w[72:76]+w[288:291]
  if identity is None:identity=ident
  assert identity==ident
  if w[33]==4:
   if frozen is None:frozen=w[80:84]
   assert w[80:88]==frozen*2 and w[49:56]==[7,0,1,0,1,2,0]
  rows.append(dict(request=[gen,op,arg],words=w));(b.out/'reports.json').write_text(json.dumps(rows,indent=2)+'\n')
  (b.out/'last-step.txt').write_text((b.debugfs/'result.txt').read_text())
  print(json.dumps(dict(run=index,seq=b.sequence,generation=w[5],op=op,status=status,phase=w[6],refs=w[36],starts=w[68:72],ticks=w[8])),flush=True)
  return w
 try:
  for gen in range(1,a.clean+1):call(gen,1,gen%3)
  gen=a.clean+1;w=call(gen,2,1);ticket=w[37]
  call(gen,0);call(gen,6,status=3)
  for _ in range(a.follow):call(gen,3)
  if a.early_close:
   os.close(b.fd);b.fd=None;capture(b.out/'retained',b.debugfs)
   retained=Path('/sys/module/dac960rtems/parameters/resident_retained').read_text().strip()
   assert retained=='1,0,0,1,1,1,1,1',retained
   result=subprocess.run(['rmmod','dac960rtems'],capture_output=True,text=True)
   (b.out/'early-close.json').write_text(json.dumps(dict(retained=retained,rmmod_rc=result.returncode,stderr=result.stderr),indent=2)+'\n')
   assert result.returncode and Path('/sys/module/dac960rtems').exists()
   b.records.close();b.lock.close();return
  call(gen-1,4,ticket,status=1);call(gen,4,ticket+1,status=1);call(gen,5,status=2)
  call(gen,4,ticket);call(gen,4,ticket,status=1)
  for _ in range(a.follow):call(gen,3)
  call(gen,5);print(json.dumps(b.close()),flush=True)
 except BaseException:
  if b.fd is not None:
   os.close(b.fd);b.fd=None
   capture(b.out/'failed-close',b.debugfs)
  if b.records:b.records.close()
  if b.lock:b.lock.close()
  raise

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--sessions',type=int,default=1);p.add_argument('--clean',type=int,default=2);p.add_argument('--follow',type=int,default=2);p.add_argument('--early-close',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 assert not a.early_close or a.sessions==1
 for i in range(a.sessions):session(a,i)
if __name__=='__main__':main()

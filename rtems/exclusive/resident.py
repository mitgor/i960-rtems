#!/usr/bin/env python3
"""One-way RAM resident experiment. Completion ALWAYS retains until host reboot."""
import argparse,errno,fcntl,json,os,secrets,struct,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture
import wire

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--ticks',type=int,default=1200);p.add_argument('--stop-after',type=float,default=0);a=p.parse_args()
 assert 200<=a.ticks<=6000 and 0<=a.stop_after<a.ticks/100
 b=Board(a.payload,a.module,a.output,autonomous=True);epoch=secrets.randbelow(65535)+1;events=[];snapshots=[]
 def call(op,arg=0,e=epoch):
  raw=bytearray(struct.pack('<8I',op,e,arg,0,0,0,0,0));t=time.monotonic_ns()
  try:fcntl.ioctl(b.fd,0xc0204d04,raw,True)
  except OSError as error:
   events.append(dict(op=op,arg=arg,epoch=e,errno=error.errno));(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n');raise
  w=list(struct.unpack('<8I',raw));assert w[3]==1 and w[6:]==[0,0] and not w[4]&1
  tags={4:0x8b000000,5:0x92000000|(arg<<16),6:0x94000000,7:0x95000000};assert w[5]==tags[op]|e
  events.append(dict(op=op,arg=arg,epoch=e,ns=time.monotonic_ns()-t,words=w));(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n');return w
 def snapshot():
  call(7);w=[call(5,i)[2] for i in range(64)];snapshots.append(dict(seconds=time.monotonic()-started,words=w));(b.out/'snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n');assert w[0]==0x31525845 and w[2] in (1,2) and w[4]==w[11]==w[52]==0 and w[36:42]==[0]*6 and w[42:46]==[2,18,514,81916]
  assert w[56]==epoch and not any(w[57:])
  print(json.dumps(dict(seconds=snapshots[-1]['seconds'],state=w[2],reason=w[3],ticks=w[5],work=w[6:8],done=w[8:10],irq=w[12:16])),flush=True);return w
 try:
  raw=b.step(struct.pack('<4I',0x31415452,1,epoch,2|(a.ticks<<8)));assert len(raw)==640
  call(4);started=time.monotonic()
  try:os.write(b.fd,wire.block(struct.pack('<4I',0x31415452,0,epoch,0),2));raise AssertionError('firmware write accepted')
  except OSError as e:assert e.errno==errno.EIO;(b.out/'write-denied.txt').write_text(f'errno={e.errno}; sequence remains 1\n')
  for op,arg,e in [(5,64,epoch),(7,0,epoch^0x8000 or 1),(4,0,epoch)]:
   try:call(op,arg,e);raise AssertionError('invalid control accepted')
   except OSError as error:assert error.errno in (errno.EINVAL,errno.ESTALE,errno.EBUSY)
  previous=snapshot();assert previous[2]==1
  stop_sent=False
  while time.monotonic()-started<a.ticks/100+5:
   time.sleep(.5)
   if a.stop_after and not stop_sent and time.monotonic()-started>=a.stop_after:call(6);stop_sent=True
   w=snapshot();assert w[1]>previous[1] and w[5]>=previous[5] and w[6]>=previous[6] and w[7]>=previous[7];previous=w
   if w[2]==2:break
  assert w[2]==2 and w[3]==(1 if a.stop_after else 2) and w[8:10]==[1,1] and w[12]==w[13]>0 and w[14]==w[15]>0 and w[53]==0
  frozen=w[4:36];time.sleep(.2);last=snapshot();assert last[4:36]==frozen
  call(6) # idempotent STOP while parked
  (b.out/'last-control.txt').write_text((b.debugfs/'result.txt').read_text())
 finally:
  if b.fd is not None:os.close(b.fd);b.fd=None;capture(b.out/'retained-close',b.debugfs)
  if b.records:b.records.close()
  if b.lock:b.lock.close()
 print('Resident experiment parked; allocation/module retained. Reboot required.',flush=True)
if __name__=='__main__':main()

#!/usr/bin/env python3
import argparse,fcntl,json,os,secrets,struct,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--phase',type=int,choices=range(3),default=0);p.add_argument('--ticks',type=int,default=0);p.add_argument('--hold',type=int,default=5);a=p.parse_args();assert 0<=a.ticks<=1000 and 0<=a.hold<=20
 b=Board(a.payload,a.module,a.output,autonomous=True);epoch=secrets.randbelow(65535)+1;events=[]
 def action(op):
  raw=bytearray(struct.pack('<8I',op,epoch,a.hold if op==0 else 0,0,0,0,0,0));t=time.monotonic_ns();fcntl.ioctl(b.fd,0xc0204d04,raw,True)
  w=list(struct.unpack('<8I',raw));assert w[3]==1 and w[6:]==[0,0] and not w[4]&1
  events.append(dict(op=op,ns=time.monotonic_ns()-t,words=w));(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n');return w
 try:
  raw=b.step(struct.pack('<4I',0x31415452,1,epoch,a.phase|(a.ticks<<8)));assert len(raw)==640 and struct.unpack_from('<I',raw,60)[0]==1
  assert action(0)[5]==0x87000000|epoch
  assert action(3)[5]==0x89000000|epoch
  (b.out/'monitor-log.txt').write_text((b.debugfs/'result.txt').read_text())
  raw=b.step(struct.pack('<4I',0x31415452,0,epoch,0));(b.out/'report.bin').write_bytes(raw);w=list(struct.unpack('<160I',raw));(b.out/'report.json').write_text(json.dumps(w,indent=2)+'\n')
  assert w[16:21]==[0x31464f48,4,1,0,0] and w[46]==w[48]==0 and w[64:67]==[0x31435845,a.phase,0]
  assert w[68:84]==w[100:116]
  if a.ticks:assert w[116]==w[123]==w[148]==0 and w[117]>=a.ticks and w[118]>0 and w[119]>0 and w[120:122]==[1,1] and w[124]==w[125]>0 and w[126]==w[127]>0
  print(json.dumps(dict(phase=a.phase,runtime=w[116:128],before=w[68:84],during=w[84:100],after=w[100:116])),flush=True);print(json.dumps(b.close()),flush=True)
 except BaseException:
  if b.fd is not None:os.close(b.fd);b.fd=None;capture(b.out/'failed-close',b.debugfs)
  if b.records:b.records.close()
  if b.lock:b.lock.close()
  raise
if __name__=='__main__':main()

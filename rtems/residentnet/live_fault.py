#!/usr/bin/env python3
"""Irreversible exception containment experiment; close retains module for reboot."""
import argparse,errno,fcntl,json,os,secrets,struct,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture
import wire

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--kind',type=int,choices=(1,2,3,4),required=True);a=p.parse_args()
 b=Board(a.payload,a.module,a.output,autonomous=True);epoch=secrets.randbelow(65535)+1;events=[]
 def control(op,arg=0):
  raw=bytearray(struct.pack('<8I',op,epoch,arg,0,0,0,0,0));fcntl.ioctl(b.fd,0xc0204d04,raw,True);w=list(struct.unpack('<8I',raw));events.append(dict(op=op,arg=arg,words=w));(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n');assert w[3]==1 and w[6:]==[0,0] and not w[4]&1;return w
 def snap():control(7);return [control(5,i)[2] for i in range(64)]
 try:
  assert len(b.step(struct.pack('<4I',0x31415452,1,epoch,2|(1200<<8))))==640
  control(4);time.sleep(2)
  if a.kind==2:
   raw=bytearray(struct.pack('<8I',1,epoch,0,0,0,0,0,0));fcntl.ioctl(b.fd,0xc0204d06,raw,True)
   (b.out/'nmi-trigger.json').write_text(json.dumps(list(struct.unpack('<8I',raw)))+'\n');time.sleep(.1)
  w=snap();(b.out/'fault.json').write_text(json.dumps(w,indent=2)+'\n')
  assert w[0:3]==[0x31464d4e,epoch,a.kind] and w[16:20]==[1,1,1,0]
  assert w[20:26]==[0]*6 and w[26:30]==[2,0,0x242,0x13ffc] and w[31]==0
  assert w[9]==w[12] and w[13]==0xc004e190
  if a.kind==4:
   assert w[48:52]==[0x31504548,0xc022ee80,69952,1] and w[63] in (1,2,3,4)
   assert w[52]=={1:1,2:3,3:2,4:2}[w[63]] and w[62]==(4 if w[63]==1 else 0)
   assert w[53]>w[54] and w[55]>0 and w[58:60]==[1,0] and w[60]>0 and w[61]>0
  if a.kind==1:assert (w[6]>>16)&255==5 and w[6]&65535==1 and 0xc0f2c000<=w[7]<0xc0f4c000
  try:os.write(b.fd,wire.block(struct.pack('<4I',0x31415452,0,epoch,0),2));raise AssertionError('callback accepted')
  except OSError as exc:assert exc.errno==errno.EIO
  control(6);time.sleep(1);assert snap()==w
  (b.out/'result.json').write_text(json.dumps(dict(kind=a.kind,terminal=True,record_stable=True,callback_rejected=True,resources_retained=True),indent=2)+'\n')
  print('Terminal exception ownership passed; reboot required.',flush=True)
 except BaseException:
  (b.out/'error.txt').write_text(traceback.format_exc());raise
 finally:
  if b.fd is not None:os.close(b.fd);b.fd=None;capture(b.out/'retained-close',b.debugfs)
  if b.records:b.records.close()
  if b.lock:b.lock.close()
if __name__=='__main__':main()

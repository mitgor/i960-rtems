#!/usr/bin/env python3
import argparse,errno,fcntl,json,os,secrets,struct,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture

def decode(raw,expected_entries,expected_denials,expected_expired):
 w=list(struct.unpack('<64I',raw))
 assert w[0]==0x31415452 and not w[1] and w[7:9]==[0x10c7,0x80000] and w[9]==w[10] and w[11:14]==[0,0,0] and not w[14]&0x2000 and not w[15]
 assert w[16:21]==[0x31464f48,4,expected_entries,expected_denials,expected_expired]
 assert w[22]==0 and w[24] in (1,2) and w[25:27]==[0,127] and w[28:34]==w[34:40]
 assert w[40] and w[43]==0xf2 and w[44:46]==[0x30c7,0x30c7]
 assert w[46]==w[48]==0 and w[47]>=expected_entries and w[49]+192<=w[50]<=w[51]<w[49]+w[52]-64 and w[53]==0xc0001000 and not any(w[54:])
 return w

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--sessions',type=int,default=1);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 for run in range(a.sessions):
  b=Board(a.payload,a.module,a.output/f'run-{run}',autonomous=True);epoch=secrets.randbelow(65535)+1;events=[]
  def action(op,hold=0,e=epoch):
   words=bytearray(struct.pack('<8I',op,e,hold,0,0,0,0,0));start=time.monotonic_ns()
   try:fcntl.ioctl(b.fd,0xc0204d04,words,True)
   except OSError as error:
    events.append(dict(op=op,epoch=e,errno=error.errno));(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n');raise
   w=list(struct.unpack('<8I',words));assert w[3]==1 and w[6:]==[0,0] and not w[4]&1
   events.append(dict(op=op,epoch=e,hold=hold,elapsed_ns=time.monotonic_ns()-start,words=w));(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n')
   return w
  try:
   raw=b.step(struct.pack('<4I',0x31415452,1,epoch,0));assert len(raw)==256 and struct.unpack_from('<I',raw,60)[0]==1
   try:action(0,e=epoch^0x8000 or 1);raise AssertionError('stale epoch accepted')
   except OSError as error:assert error.errno==errno.ESTALE
   assert action(1)[5]==0x85000000|epoch
   for hold in (0,5,20):assert action(0,hold)[5]==0x87000000|epoch
   assert action(2)[5]==0x86000000|epoch
   assert action(1)[5]==0x85000000|epoch
   assert action(3)[5]==0x89000000|epoch
   (b.out/'monitor-log.txt').write_text((b.debugfs/'result.txt').read_text());assert b.sequence==1
   raw=b.step(struct.pack('<4I',0x31415452,0,epoch,0));(b.out/'report.bin').write_bytes(raw);w=decode(raw,4,2,1);(b.out/'report.json').write_text(json.dumps(w,indent=2)+'\n')
   print(json.dumps(dict(run=run,entries=w[18],denials=w[19],expired=w[20],dma_before=w[28:34],dma_after=w[34:40],irq_fault=w[48],ticks=w[2],proof=w[25],missing=w[26])),flush=True)
   print(json.dumps(b.close()),flush=True)
  except BaseException:
   if b.fd is not None:os.close(b.fd);b.fd=None;capture(b.out/'failed-close',b.debugfs)
   if b.records:b.records.close()
   if b.lock:b.lock.close()
   raise
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Actual asynchronous ownership reports and concurrent host control."""
import argparse,concurrent.futures,errno,json,secrets,struct,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'switch'))
from live_concurrent import ioctl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def decode(data):
 assert len(data)==1024
 w=list(struct.unpack('<256I',data));mode=w[3];clean=mode<=2
 assert w[:3]==[0x3149524f,1,0] and 1<=mode<=5 and w[4]>0
 assert w[17:20]==[0,0x10c7,0x80000] and w[20]==w[21] and not any(w[22:25]+w[26:28]) and not w[25]&0x2000
 assert w[32]==w[34]==2 and w[33]==(2 if clean else 0x402)
 assert w[247]==w[248] and w[249:253]==([0,1,1,0] if clean else [1,1,0,0]) and w[254:]==[0x4d554f4b,0x514f4b31]
 assert w[14]>w[15]>0 and w[16]==10000 and w[51]==w[53]==1 and w[54]==23
 if clean:
  assert w[28:32]==[0]*4 and w[35:39]==[1,1,0x10203040,1] and w[39]>0
  assert w[41:45]==[3,0x55667788,0x55667788,0] and w[11]>w[10] and w[12]>=w[11]
 else:
  assert w[28]==w[244] and w[29:32]==[1,1,0] and w[35:39]==[1,0,0,0]
  assert w[41:45]==[4,0x10203040,0xdeadbeef,int(mode==5)]
  assert w[13]==w[9]+4 and w[56]==w[57] and w[58]==w[59] and w[78]==w[79]
 for i in range(2):
  s=w[80+i*82:92+i*82];live=int(i==1 or not clean)
  assert s[7]==live and s[8]==s[9]+live and s[6]==0xf2
 if mode in (1,2,4):
  c=w[60:80];assert c[2]-c[1]==c[3]-c[2]==12 and w[9]==c[3] and c[5:9]==[2,1,1,0] and c[9]==c[10] and c[13:16]==[12,12,0]
 return dict(mode=mode,epoch=w[4],stop_tick=w[8],controller_tick=w[9],lease_complete_tick=w[11],retired_tick=w[12],quarantine_tick=w[13],end_tick=w[5],deferred_checkpoints=w[39],waiter_done=w[36],phase=w[41],references=w[44],other_budget_before=w[14],other_budget_after=w[15],owner_entries=w[88],owner_returns=w[89],other_entries=w[170],other_returns=w[171],faults=w[2])

def exchange(b,mode):
 epoch=secrets.randbelow(65535)+1
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  work=pool.submit(b.step,struct.pack('<3I',0x31505453,epoch,mode));deadline=time.monotonic()+2
  while True:
   assert not work.done(),'callback returned before control'
   try:
    status=ioctl(b.fd,0,epoch)
    if status[4]==0x71000000|epoch:break
   except OSError as e:assert e.errno==errno.EAGAIN
   assert time.monotonic()<deadline;time.sleep(.001)
  reply=ioctl(b.fd,1,epoch)
  control=dict(status=status,reply=reply,pending=True,epoch=epoch,mode=mode)
  (b.out/'control.json').write_text(json.dumps(control,indent=2)+'\n')
  assert reply[6]==0x75000000|epoch and reply[7]==1 and not(reply[3]&1) and not(reply[5]&1)
  data=work.result(timeout=3)
 return data

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output','reader'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--modes',default='1,2,3,4,1,2,3,4');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for index,mode in enumerate(map(int,a.modes.split(','))):
  assert 1<=mode<=4
  before=json.loads(subprocess.check_output([str(a.reader)],text=True));b=Board(a.payload,a.module,a.output/f'run-{index}')
  (b.out/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
  try:
   data=exchange(b,mode);(b.out/'ownirq.bin').write_bytes(data);row=decode(data)
   log=(b.debugfs/'result.txt').read_text();(b.out/'control-log.txt').write_text(log)
   assert 'OWNIRQ verified resource ownership' in log and 'CONCURRENT QUIESCED ioctl' in log
   (b.out/'acceptance.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row);print(json.dumps(row),flush=True)
  finally:print(json.dumps(b.close()),flush=True)
  after=json.loads(subprocess.check_output([str(a.reader)],text=True));(b.out/'mu-after.json').write_text(json.dumps(after,indent=2)+'\n')
  for sample in after['samples']:
   for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
   for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
 (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()

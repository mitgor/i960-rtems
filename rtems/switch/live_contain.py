#!/usr/bin/env python3
"""Bounded STOP-ignoring workers: quarantine, return, then full restoration."""
import argparse,concurrent.futures,errno,json,secrets,struct,subprocess,sys,time
from pathlib import Path
from live_concurrent import ioctl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def decode(data):
 assert len(data)==944
 w=struct.unpack('<236I',data);d=w[184:204];q=w[204:]
 assert w[0]==0x31575349 and w[1]==0 and 32<=w[2]<=128 and min(w[3:5])>5
 assert w[5:11]==(0,0,1,1,0,0)
 assert w[11:13]==(0x10c7,0x80000) and w[13]==w[14] and w[15:18]==(0,0,0) and not(w[18]&0x2000) and w[19]==0
 assert d[0]==0x31505453 and 0<d[1]<=65535 and d[2]==8 and 32<=d[3]<=124
 assert d[4] in (w[20],w[102]) and d[5:9]==(1,1,1,1) and d[9]==w[2]
 assert d[12]>0 and d[13]==0x4d554f4b and not any(d[14:])
 assert q[0]==0x314e5443 and q[1] and q[1] not in (w[20],w[102])
 assert q[2]==d[3] and q[3]==w[2] and q[3]-q[2]==q[4]==4
 assert q[15]==q[16]==q[1] and q[17]==10000 and q[26:]==(0x514f4b31,1,0,0,0,0)
 slots=[]
 for i in range(2):
  s=w[20+i*82:32+i*82];r=w[32+i*82:102+i*82]
  assert s[0] and s[2]-s[1]==8192 and s[1]+16<=s[3]<=s[2]-64 and s[3]%16==0
  assert s[6:8]==(0xf2,1) and s[8]==s[9]+1 and s[8]>5 and d[10+i]==s[9]
  assert s[10]+192<=s[11]<s[10]+8128
  assert r[:15]==tuple(0x19600000+i*0x10000000+j for j in range(15)) and r[68]==0
  assert 0<q[7+i]<q[5+i]<=1000000 and r[69]==q[9+i]==q[7+i]
  assert q[11+i]==q[13+i]==2 and q[18+i]==q[20+i] and q[22+i]==q[24+i]
  slots.append(dict(owner=hex(s[0]),entries=s[8],returns=s[9],live=s[7],
    remaining_at_stop=q[5+i],remaining_at_suspend=q[7+i],remaining_after=q[9+i],
    suspended_state=q[13+i],stack_hash=hex(q[20+i]),irq_hash=hex(q[24+i])))
 assert w[20]!=w[102] and w[30]!=w[112] and (w[22]<=w[103] or w[104]<=w[21])
 return dict(epoch=d[1],stop_tick=d[3],quiesced_tick=w[2],ignored_stop_ticks=q[4],
  stable_observations=q[17],faults=w[1],slots=slots)

def main(decoder=decode,delays=(120,150,200),filename='contain.bin'):
 p=argparse.ArgumentParser()
 for n in ('payload','module','output','reader'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for index,delay in enumerate(delays):
  before=json.loads(subprocess.check_output([str(a.reader)],text=True))
  b=Board(a.payload,a.module,a.output/f'run-{index}');epoch=secrets.randbelow(65535)+1
  (b.out/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
  try:
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    work=pool.submit(b.step,struct.pack('<3I',0x31505453,epoch,delay));deadline=time.monotonic()+2
    while True:
     assert not work.done(),'callback returned before control'
     try:
      status=ioctl(b.fd,0,epoch)
      if status[4]==0x71000000|epoch:break
     except OSError as e:assert e.errno==errno.EAGAIN
     assert time.monotonic()<deadline;time.sleep(.001)
    pending=not work.done();reply=ioctl(b.fd,1,epoch);data=work.result(timeout=3)
   (b.out/filename).write_bytes(data);row=decoder(data);assert row['epoch']==epoch
   assert pending and not(reply[3]&1) and not(reply[5]&1) and reply[6]==0x75000000|epoch and reply[7]==1
   (b.out/'control.json').write_text(json.dumps(dict(status=status,reply=reply,pending=pending),indent=2)+'\n')
   log=(b.debugfs/'result.txt').read_text();(b.out/'control-log.txt').write_text(log)
   assert 'CONCURRENT QUIESCED ioctl' in log and 'CONTAIN verified suspended workers' in log
   (b.out/'acceptance.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row);print(json.dumps(row),flush=True)
  finally:print(json.dumps(b.close()),flush=True)
  after=json.loads(subprocess.check_output([str(a.reader)],text=True));(b.out/'mu-after.json').write_text(json.dumps(after,indent=2)+'\n')
  for sample in after['samples']:
   for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
   for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
 (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()

#!/usr/bin/env python3
import argparse,concurrent.futures,errno,fcntl,json,os,secrets,struct,subprocess,sys,time
from pathlib import Path
from live_stop import decode_stop
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def ioctl(fd,op,epoch):
 b=bytearray(struct.pack('<8I',op,epoch,0,0,0,0,0,0));fcntl.ioctl(fd,0xc0204d03,b,True);return list(struct.unpack('<8I',b))
def refused(fd,op,epoch,allowed):
 try:ioctl(fd,op,epoch)
 except OSError as e:assert e.errno in allowed;return e.errno
 raise AssertionError('unexpected accepted ioctl')
def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output','reader'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for index,delay in enumerate((120,150,200)):
  before=json.loads(subprocess.check_output([str(a.reader)],text=True))
  b=Board(a.payload,a.module,a.output/f'run-{index}');fd=os.dup(b.fd);epoch=secrets.randbelow(65535)+1
  (b.out/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
  evidence={'before':refused(fd,0,epoch,{errno.EAGAIN})}
  try:
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    work=pool.submit(b.step,struct.pack('<3I',0x31505453,epoch,delay))
    deadline=time.monotonic()+2
    while True:
     assert not work.done(),'callback returned before concurrent STOP'
     try:
      status=ioctl(fd,0,epoch)
      if status[4]==0x71000000|epoch:break
     except OSError as e:assert e.errno==errno.EAGAIN
     assert time.monotonic()<deadline;time.sleep(.001)
    evidence['status']=status;evidence['writer_pending_at_ready']=not work.done()
    evidence['wrong_epoch']=refused(fd,1,epoch^0x10000,{errno.ESTALE})
    # Two simultaneous STOP syscalls share one file and are serialized by the
    # control mutex. Only one is allowed to write STOP/RELEASE.
    stop=pool.submit(ioctl,fd,1,epoch)
    time.sleep(.01)
    duplicate=os.dup(fd);os.close(duplicate) # close an alias while syscalls hold file references
    evidence['closed_alias_while_running']=not work.done()
    evidence['duplicate']=refused(fd,1,epoch,{errno.EALREADY,errno.EAGAIN})
    evidence['stop']=stop.result(timeout=3)
    data=work.result(timeout=3)
   (b.out/'stop.bin').write_bytes(data);row=decode_stop(data)
   assert row['stop']['epoch']==epoch
   assert evidence['stop'][2]==1 and not(evidence['stop'][3]&1) and not(evidence['stop'][5]&1)
   assert evidence['stop'][6]==0x73000000|epoch and evidence['stop'][7]==1
   assert evidence['writer_pending_at_ready'] and evidence['closed_alias_while_running']
   evidence['after']=refused(fd,1,epoch,{errno.EAGAIN})
   log=(b.debugfs/'result.txt').read_text();(b.out/'control-log.txt').write_text(log)
   assert log.count('CONCURRENT STOP ioctl')==1 and log.count('CONCURRENT DRAINED ioctl')==1
   assert 'CONCURRENT window closed/joined rc=0 done=1' in log
   (b.out/'concurrency.json').write_text(json.dumps(evidence,indent=2)+'\n')
   (b.out/'acceptance.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row);print(json.dumps(row),flush=True)
  finally:
   os.close(fd);print(json.dumps(b.close()),flush=True)
  after=json.loads(subprocess.check_output([str(a.reader)],text=True));(b.out/'mu-after.json').write_text(json.dumps(after,indent=2)+'\n')
  for sample in after['samples']:
   for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
   for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
 (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()

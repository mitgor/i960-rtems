#!/usr/bin/env python3
"""Fault-inject final user-fd close or sysfs driver unbind during STOP ioctl."""
import argparse,concurrent.futures,errno,json,os,secrets,struct,subprocess,sys,time
from pathlib import Path
from live_concurrent import ioctl,refused
from live_stop import decode_stop
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture,verify_close
import wire
PARAM=Path('/sys/module/dac960rtems/parameters/lifecycle')
DEVICE='0000:37:09.1'
def events():return [int(x) for x in PARAM.read_text().strip().split(',')]
def wait_for(fn,seconds=4):
 end=time.monotonic()+seconds
 while not fn():
  assert time.monotonic()<end,'deadline waiting for lifecycle event'
  time.sleep(.001)
def check_order(mode,e):
 assert len(e)==16
 assert 0<e[0]<e[1]<e[13]<e[4]<e[5],e
 if mode=='close':
  assert e[5]<e[3]<=e[11]<e[7]<e[8],e
  assert not any(e[i] for i in (2,6,9,10,12)),e
 else:
  assert e[1]<e[2]<e[13] and e[5]<e[6]<e[7]<e[8]<e[9]<e[10],e
  assert not any(e[i] for i in (3,11,12)),e

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output','reader'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--repeats',type=int,default=3);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for rep in range(a.repeats):
  for mode in ('close','unbind'):
   before=json.loads(subprocess.check_output([str(a.reader)],text=True))
   b=Board(a.payload,a.module,a.output/f'run-{rep}-{mode}');fd=b.fd;epoch=secrets.randbelow(65535)+1
   (b.out/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
   req=wire.block(struct.pack('<3I',0x31505453,epoch,200),1)
   (b.out/'input.bin').write_bytes(req)
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    write=pool.submit(os.write,fd,req)
    def ready():
     assert not write.done(),'callback completed too soon'
     try:return ioctl(fd,0,epoch)[4]==0x71000000|epoch
     except OSError as e:assert e.errno==errno.EAGAIN;return False
    wait_for(ready)
    stop=pool.submit(ioctl,fd,1,epoch)
    wait_for(lambda:events()[1]>0)
    evidence={'mode':mode,'repetition':rep,'epoch':epoch,'injection_events':events()}
    assert not write.done() and not stop.done()
    if mode=='close':
     # The sole user descriptor disappears while both syscalls hold file refs.
     os.close(fd);b.fd=None
     evidence['fd_closed']=not Path(f'/proc/self/fd/{fd}').exists()
     assert evidence['fd_closed']
     evidence['after_injection']=events();assert evidence['after_injection'][3]==0
    else:
     remove=pool.submit(Path('/sys/bus/pci/drivers/dac960rtems/unbind').write_text,DEVICE)
     wait_for(lambda:events()[2]>0)
     evidence['after_injection']=events()
     assert not remove.done() and not write.done() and evidence['after_injection'][6]==0
    evidence['stop']=stop.result(timeout=4)
    evidence['write_count']=write.result(timeout=4);assert evidence['write_count']==len(req)
    if mode=='close':wait_for(lambda:events()[8]>0)
    else:assert remove.result(timeout=4)==len(DEVICE)
   evidence['events']=events();check_order(mode,evidence['events'])
   (b.out/'lifecycle-progress.json').write_text(json.dumps(evidence,indent=2)+'\n')
   capture(b.out/'close',b.debugfs);verify_close(b.out/'close')
   after=(b.out/'close/payload-after-a5.bin').read_bytes();assert after==(b.out/'close/payload-after-5a.bin').read_bytes()
   status,data=wire.response(b.image[:wire.bio.OFFSET]+req+b.original[wire.bio.IMAGE_SIZE:],after+b.original[len(after):])
   assert status==0;row=decode_stop(data);assert row['stop']['epoch']==epoch
   (b.out/'stop.bin').write_bytes(data)
   if mode=='unbind':
    assert not Path('/sys/bus/pci/devices',DEVICE,'driver').exists()
    evidence['late_ioctl']=refused(fd,1,epoch,{errno.EAGAIN})
    try:os.read(fd,wire.bio.SIZE)
    except OSError as e:assert e.errno==errno.EIO;evidence['late_read']=e.errno
    else:raise AssertionError('read after remove accepted')
    os.close(fd);b.fd=None;wait_for(lambda:events()[12]>0)
    evidence['final_events']=events();f=evidence['final_events']
    assert f[10]<f[3]<=f[11]<f[12] and f[7:9]==evidence['events'][7:9]
    assert not b.debugfs.exists()
   subprocess.run(['rmmod','dac960rtems'],check=True)
   assert not Path('/sys/module/dac960rtems').exists()
   after_mu=json.loads(subprocess.check_output([str(a.reader)],text=True));(b.out/'mu-after.json').write_text(json.dumps(after_mu,indent=2)+'\n')
   for sample in after_mu['samples']:
    for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
    for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
   evidence['restored']=evidence['unloaded']=True
   (b.out/'lifecycle.json').write_text(json.dumps(evidence,indent=2)+'\n')
   (b.out/'acceptance.json').write_text(json.dumps(row,indent=2)+'\n')
   b.records.close();b.lock.close();rows.append(dict(mode=mode,repetition=rep,report=row,events=evidence['events']))
   print(json.dumps(rows[-1]),flush=True)
 (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()

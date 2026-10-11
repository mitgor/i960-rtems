#!/usr/bin/env python3
"""One retained-resource fault per boot. Never force-unload or restore on failure."""
import argparse,concurrent.futures,errno,json,os,secrets,struct,subprocess,sys,time
from pathlib import Path
from live_concurrent import ioctl
from live_lifecycle import wait_for,events,DEVICE
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture
import wire
PARAM=Path('/sys/module/dac960rtems/parameters')
def snapshot():
 return dict(events=events(),retention=[int(x) for x in (PARAM/'retention').read_text().strip().split(',')],
  refcount=int(Path('/sys/module/dac960rtems/refcnt').read_text()),
  bound=Path('/sys/bus/pci/devices',DEVICE,'driver').exists(),
  debugfs=Path('/sys/kernel/debug/dac960rtems').exists())
def check(mode,s):
 if mode==3:
  r=s["retention"];e=s["events"]
  assert r==[0,1,1,0,1,0,1,0,0,0,1,0,1,1,1,3],r
  assert 0<e[0]<e[1]<e[13]<e[4]<e[7]<e[5]<e[3]<=e[11],e
  assert not any(e[i] for i in (2,6,8,9,10,12,14,15)),e
  assert s["refcount"]>0 and s["bound"] and s["debugfs"]
  return
 r=s['retention'];e=s['events'];assert r==[1,1,1,1,1,0,1,mode==2,0,0,0,110,1,1,0,mode],r
 assert 0<e[0]<e[1]<e[13]<e[4]<e[7]<e[5],e
 assert not any(e[i] for i in (8,10,12,14,15)),e
 if mode==1:assert e[5]<e[3]<=e[11] and e[2]==e[6]==e[9]==0 and s['bound']
 else:assert e[1]<e[2]<e[13] and e[5]<e[6]<e[9]<e[3]<=e[11] and not s['bound']
 assert s['refcount']>0 and s['debugfs']
def error_future(f,expected=errno.ETIMEDOUT):
 try:f.result(timeout=5)
 except OSError as e:assert e.errno==expected;return e.errno
 raise AssertionError('failure syscall succeeded')
def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--mode',type=int,choices=(1,2,3),required=True);a=p.parse_args()
 b=Board(a.payload,a.module,a.output,module_options=(f'fail_control={a.mode}',));fd=b.fd;epoch=secrets.randbelow(65535)+1
 req=wire.block(struct.pack('<3I',0x31505453,epoch,200),1);(b.out/'input.bin').write_bytes(req)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  write=pool.submit(os.write,fd,req)
  def ready():
   assert not write.done()
   try:return ioctl(fd,0,epoch)[4]==0x71000000|epoch
   except OSError as e:assert e.errno==errno.EAGAIN;return False
  wait_for(ready);control=pool.submit(ioctl,fd,1,epoch);wait_for(lambda:events()[1]>0)
  evidence=dict(mode=a.mode,epoch=epoch,injection=snapshot());assert not write.done() and not control.done()
  if a.mode in (1,3):
   os.close(fd);b.fd=None;evidence['last_fd_closed']=not Path(f'/proc/self/fd/{fd}').exists();assert evidence['last_fd_closed']
  else:
   remove=pool.submit(Path('/sys/bus/pci/drivers/dac960rtems/unbind').write_text,DEVICE)
   wait_for(lambda:events()[2]>0);assert not remove.done() and events()[6]==0
  if a.mode==3:
   evidence['control_reply']=control.result(timeout=5);evidence['control_errno']=0
  else:evidence['control_errno']=error_future(control)
  evidence['write_errno']=error_future(write,errno.ENODATA if a.mode==3 else errno.ETIMEDOUT)
  if a.mode==2:
   assert remove.result(timeout=5)==len(DEVICE);os.close(fd);b.fd=None
 wait_for(lambda:events()[11]>0)
 evidence['before_unload']=snapshot();check(a.mode,evidence['before_unload'])
 capture(b.out/'retained',b.debugfs)
 log=(b.out/'retained/result.txt').read_text()
 assert 'SESSION FAILED: retained DMA/module; reboot required' in log
 assert 'SESSION CLOSE rc=0' not in log
 assert ('CONCURRENT window closed/joined rc=0 done=1' if a.mode==3 else 'CONCURRENT window closed/joined rc=-110 done=0') in log
 tail=log[log.index('INJECT '):];assert 'submit op=' not in tail,'firmware transaction after uncertainty'
 result=subprocess.run(['rmmod','dac960rtems'],capture_output=True,text=True)
 evidence['unload']=dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr);assert result.returncode!=0
 time.sleep(1);evidence['after_unload']=snapshot();check(a.mode,evidence['after_unload'])
 assert evidence['after_unload']==evidence['before_unload'],'retained resources changed'
 (b.out/'acceptance.json').write_text(json.dumps(evidence,indent=2)+'\n')
 b.records.close();b.lock.close()
 print(json.dumps(evidence),flush=True)
 print('Evidence saved. Resources intentionally retained; recovery requires reboot. No forced unload or restoration attempted.',flush=True)
if __name__=='__main__':main()

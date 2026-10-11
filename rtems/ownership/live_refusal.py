#!/usr/bin/env python3
"""Close with a resident mutex owner: retain the entire session until reboot."""
import argparse,json,os,struct,subprocess,time
from pathlib import Path
from live import Board,decode
from run import capture

def snapshot():
 p=Path('/sys/module/dac960rtems')
 return dict(retained=[int(v) for v in (p/'parameters/ownership_retained').read_text().strip().split(',')],refcount=int((p/'refcnt').read_text()),bound=Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists(),debugfs=Path('/sys/kernel/debug/dac960rtems').exists())

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();b=Board(a.payload,a.module,a.output);rows=[]
 for op,value in ((0,0),(1,0xdeadbeef),(2,0xfeedbeef)):
  req=struct.pack('<4I',0x314e574f,op,1,value);raw=b.step(req);w=decode(raw)
  assert w[4]==0;rows.append(dict(request=req.hex(),report=raw.hex()))
 assert w[7]==1 and w[21]==w[18] and w[27]==1 and w[24]&0x400
 (b.out/'ownership.json').write_text(json.dumps(rows,indent=2)+'\n')
 os.close(b.fd);b.fd=None;b.records.close()
 capture(b.out/'retained',b.debugfs)
 log=(b.out/'retained/result.txt').read_text()
 assert 'OWNERSHIP refuses restore before finalization' in log
 assert 'SESSION FAILED: retained DMA/module; reboot required' in log
 assert 'SESSION CLOSE rc=0' not in log
 assert 'submit op=' not in log.split('OWNERSHIP refuses restore before finalization',1)[1]
 before=snapshot();assert before['retained']==[1,0,1,1,1,1],before
 assert before['refcount']>0 and before['bound'] and before['debugfs']
 r=subprocess.run(['rmmod','dac960rtems'],capture_output=True,text=True);assert r.returncode!=0
 time.sleep(1);after=snapshot();assert after==before
 evidence=dict(before_unload=before,after_unload=after,unload=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 (b.out/'acceptance.json').write_text(json.dumps(evidence,indent=2)+'\n');b.lock.close()
 print(json.dumps(evidence),flush=True)
 print('Premature close refused. Resources retained. Reboot required.',flush=True)
if __name__=='__main__':main()

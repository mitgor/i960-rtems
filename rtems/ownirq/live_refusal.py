#!/usr/bin/env python3
"""Quiesced target with an uncompleted software lease: refuse host reclamation."""
import argparse,errno,json,os,struct,subprocess,time
from pathlib import Path
from live import Board,exchange,decode
from run import capture

def snapshot():
 p=Path('/sys/module/dac960rtems')
 return dict(retained=[int(v) for v in (p/'parameters/ownership_retained').read_text().strip().split(',')],refcount=int((p/'refcnt').read_text()),bound=Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists(),debugfs=Path('/sys/kernel/debug/dac960rtems').exists())

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();b=Board(a.payload,a.module,a.output)
 try:exchange(b,5)
 except OSError as e:assert e.errno==errno.ENODATA;error=e.errno
 else:raise AssertionError('outstanding lease authorized cleanup')
 raw=(b.debugfs/'payload-after-a5.bin').read_bytes()[0x70000+4176:0x70000+4176+1024]
 row=decode(raw);assert row['mode']==5 and row['references']==1
 (b.out/'ownirq.bin').write_bytes(raw)
 log=(b.debugfs/'result.txt').read_text();(b.out/'control-log.txt').write_text(log)
 assert 'OWNIRQ resource proof rejected after callback completion' in log and 'CONCURRENT QUIESCED ioctl' in log
 assert 'submit op=' not in log.split('OWNIRQ resource proof rejected after callback completion',1)[1]
 os.close(b.fd);b.fd=None;b.records.close();capture(b.out/'retained',b.debugfs)
 before=snapshot();assert before['retained']==[1,0,0,0,1,1,1,1] and before['refcount']>0 and before['bound'] and before['debugfs']
 r=subprocess.run(['rmmod','dac960rtems'],capture_output=True,text=True);assert r.returncode!=0
 time.sleep(1);after=snapshot();assert after==before
 evidence=dict(report=row,write_errno=error,before_unload=before,after_unload=after,unload=dict(returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
 (b.out/'acceptance.json').write_text(json.dumps(evidence,indent=2)+'\n');b.lock.close();print(json.dumps(evidence),flush=True)
 print('Quiescence was real, lease remains outstanding, resources retained until reboot.',flush=True)
if __name__=='__main__':main()

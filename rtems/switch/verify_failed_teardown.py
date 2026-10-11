#!/usr/bin/env python3
"""Verify retention evidence, not restoration: reboot is a separate recovery step."""
import argparse,hashlib,json,sys,tarfile
from pathlib import Path
from live_failed_teardown import check
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
import wire
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--case',choices=('close','unbind'),required=True);a=p.parse_args()
mode=1 if a.case=='close' else 2;prefix='failed-'+a.case+'/'
with tarfile.open(a.archive) as t:
 def read(n):return t.extractfile(n).read()
 e=json.loads(read(prefix+'acceptance.json'));assert e['mode']==mode
 check(mode,e['before_unload']);check(mode,e['after_unload']);assert e['before_unload']==e['after_unload']
 assert e['control_errno']==e['write_errno']==110 and e['unload']['returncode']!=0
 assert 'in use' in e['unload']['stderr']
 assert e['injection']['events'][1]>0 and e['injection']['events'][4]==0
 if mode==1:assert e['last_fd_closed']
 identity=json.loads(read(prefix+'request.json'));assert identity['module_options']==[f'fail_control={mode}']
 code=read('mustop/kernel.bin');module=read('failed-teardown-module/dac960rtems.ko')
 for k,v in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:assert hashlib.sha256(v).hexdigest()==identity[k]
 log=read(prefix+'retained/result.txt').decode();tail=log[log.index('INJECT omitted'):]
 assert 'submit op=' not in tail and 'SESSION CLOSE rc=0' not in log
 assert 'SESSION FAILED: retained DMA/module; reboot required' in log
 assert 'CONCURRENT window closed/joined rc=-110 done=0' in log
 assert ('INJECT omitted STOP after READY' if mode==1 else 'INJECT omitted RELEASE after DRAINED') in log
 assert 'uncertain completion: timeout ODB=00000001' in log
print(f'{a.case}: exact images verified; both syscalls ETIMEDOUT; no post-failure firmware submissions or restore; pending/dirty state, DMA/BAR/module retained; ordinary unload refused; completion bit observed but not consumed')

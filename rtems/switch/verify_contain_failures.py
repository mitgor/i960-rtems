#!/usr/bin/env python3
import argparse,hashlib,json,struct,sys,tarfile
from pathlib import Path
from live_contain_failures import check
from live_contain import decode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
import wire
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--mode',type=int,choices=(1,2,3),required=True);a=p.parse_args();mode=a.mode
with tarfile.open(a.archive) as t:
 def read(n):return t.extractfile(n).read()
 prefix=f'containfail-{mode}/';e=json.loads(read(prefix+'acceptance.json'));assert e['mode']==mode
 assert e['injection']['events'][1]>0 and e['injection']['events'][4]==0
 check(mode,e['before_unload']);check(mode,e['after_unload']);assert e['before_unload']==e['after_unload']
 assert e['unload']['returncode']!=0 and 'in use' in e['unload']['stderr']
 assert e['write_errno']==(61 if mode==3 else 110) and e['control_errno']==(0 if mode==3 else 110)
 if mode!=2:assert e['last_fd_closed']
 identity=json.loads(read(prefix+'request.json'));assert identity['module_options']==[f'fail_control={mode}']
 code=read('contain/kernel.bin');module=read('containfail-module/dac960rtems.ko')
 for k,v in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:assert hashlib.sha256(v).hexdigest()==identity[k]
 log=read(prefix+'retained/result.txt').decode();tail=log[log.index('INJECT '):]
 assert 'submit op=' not in tail and 'SESSION CLOSE rc=0' not in log
 assert 'SESSION FAILED: retained DMA/module; reboot required' in log
 if mode==3:
  assert 'CONCURRENT window closed/joined rc=0 done=1' in log and 'INJECT invalid local containment marker' in log
  assert e['control_reply'][6]==0x75000000|e['epoch'] and e['control_reply'][7]==1
  first=read(prefix+'retained/payload-after-a5.bin');assert first==read(prefix+'retained/payload-after-5a.bin')
  original=read(prefix+'open/stage-before-a5.bin');block=read(prefix+'input.bin')
  before=wire.prepare(code)[:wire.bio.OFFSET]+block+original[wire.bio.IMAGE_SIZE:]
  # Failed session_step never narrows debugfs blob.size: only IMAGE_SIZE was read.
  assert 'len=41056 offset=00069000' in log
  status,data=wire.response(before,first[:wire.bio.IMAGE_SIZE]+original[wire.bio.IMAGE_SIZE:]);assert status==0 and decode(data)['epoch']==e['epoch']
 else:
  assert 'CONCURRENT window closed/joined rc=-110 done=0' in log
  assert ('omitted STOP after READY' if mode==1 else 'omitted RELEASE after QUIESCED') in log
print(f'Mode {mode}: exact images and original evidence verified; no post-injection submissions or restoration; DMA/BAR/module retained and unload refused.'+(' Original paired report is valid; local validation copy was rejected with ENODATA after callback completion.' if mode==3 else ' Firmware completion remains unconsumed after failed control.'))

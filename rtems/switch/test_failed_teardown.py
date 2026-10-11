#!/usr/bin/env python3
import tempfile
from pathlib import Path
from build_failed_teardown import build
from live_failed_teardown import check
for mode,e in [(1,[1,2,0,7,4,6,0,5,0,0,0,8,0,3,0,0]),(2,[1,2,3,10,5,7,8,6,0,9,0,11,0,4,0,0])]:
 s=dict(events=e,retention=[1,1,1,1,1,0,1,mode==2,0,0,0,110,1,1,0,mode],refcount=1,bound=mode==1,debugfs=True);check(mode,s)
 for index in (0,1,2,3,4,6,12,13):
  bad={**s,'retention':s['retention'].copy()};bad['retention'][index]=0
  try:check(mode,bad)
  except AssertionError:pass
  else:raise AssertionError(index)
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'payload';p.write_bytes(bytes(4));out=Path(tmp)/'module';build(out,p)
 s=(out/'dac960rtems.c').read_text();t=(out/'stage_rehearsal.h').read_text()
 assert 'fail_control==1' in s and 'fail_control==2' in s
 assert 'if(d->stop_started&&!d->stop_clean)return -EBUSY;' in t
 remove=s[s.index('static void remove('):]
 assert remove.index('if(d->pending || d->exec_dirty || d->stage_dirty)')<remove.index('life_event(14)')
 assert '__module_get(THIS_MODULE)' in s and 'pci_dev_get(d->pdev)' in s
 print('Failed teardown: expected retained states accepted, 16 unsafe snapshots rejected, injection and no-free-before-retention guards verified')

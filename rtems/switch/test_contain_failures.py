#!/usr/bin/env python3
import tempfile
from pathlib import Path
from build_contain_failures import build
from live_contain_failures import check
states=[
 (1,[1,2,0,7,4,6,0,5,0,0,0,8,0,3,0,0],[1,1,1,1,1,0,1,0,0,0,0,110,1,1,0,1]),
 (2,[1,2,3,10,5,7,8,6,0,9,0,11,0,4,0,0],[1,1,1,1,1,0,1,1,0,0,0,110,1,1,0,2]),
 (3,[1,2,0,7,4,6,0,5,0,0,0,8,0,3,0,0],[0,1,1,0,1,0,1,0,0,0,1,0,1,1,1,3])]
count=0
for mode,e,r in states:
 s=dict(events=e,retention=r,refcount=1,bound=mode!=2,debugfs=True);check(mode,s)
 for index in (1,2,4,6,12,13):
  bad={**s,'retention':r.copy()};bad['retention'][index]=0
  try:check(mode,bad)
  except AssertionError:count+=1
  else:raise AssertionError(index)
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'payload';p.write_bytes(bytes(4));out=Path(tmp)/'module';build(out,p)
 s=(out/'stage_rehearsal.h').read_text();c=(out/'dac960rtems.c').read_text()
 assert s.index('words[230]=0;')<s.index('if(!contain_report_valid')<s.index('d->stop_clean=true')
 assert 'fail_control>3' in c and 'omitted RELEASE after QUIESCED' in c
 assert 'if(d->stop_started&&!d->stop_clean)return -EBUSY;' in s
print(f'Containment failure modes: 3 retained states accepted; {count} unsafe snapshots rejected; corrupted local report precedes clean authorization')

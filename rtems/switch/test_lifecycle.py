#!/usr/bin/env python3
"""Check lifecycle ordering acceptance and generated capture lifetime hooks."""
import tempfile
from pathlib import Path
from live_lifecycle import check_order
from build_lifecycle_transport import build
close=[1,2,0,6,4,5,0,8,9,0,0,7,0,3,0,0]
unbind=[1,2,3,0,5,6,7,8,9,10,11,0,0,4,0,0]
for mode,trace in [('close',close),('unbind',unbind)]:
 check_order(mode,trace)
 for index,value in [(4,1),(5,2),(7,1),(8,1),(13,1)]+([(3,1)] if mode=='close' else [(6,2),(10,1)]):
  bad=trace.copy();bad[index]=value
  try:check_order(mode,bad)
  except AssertionError:pass
  else:raise AssertionError((mode,index))
with tempfile.TemporaryDirectory() as tmp:
 payload=Path(tmp)/'payload';payload.write_bytes(bytes(4));out=Path(tmp)/'module';build(out,payload)
 s=(out/'dac960rtems.c').read_text();t=(out/'stage_rehearsal.h').read_text()
 remove=s[s.index('static void remove('):s.index('static struct pci_driver')]
 free=s[s.index('static void session_free('):s.index('static void session_pin(')]
 assert remove.index('mutex_lock(&d->session_lock)')<remove.index('life_event(6)')<remove.index('session_close(d)')<remove.index('pci_iounmap')
 assert remove.index('session_log_end(d)')<remove.index('d->removed=true')
 assert 'debugfs_remove_recursive' not in remove
 assert free.index('debugfs_remove_recursive')<free.index('free_captures')
 assert 'if(d->stop_started&&!d->stop_clean)return -EBUSY;' in t
 print('Lifecycle ordering: normal traces accepted, 13 early-cleanup/join violations rejected; generated capture lifetime and retention gates passed')

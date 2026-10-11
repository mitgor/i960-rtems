#!/usr/bin/env python3
"""Instrument concurrent-control lifetime without changing its locking contract."""
import argparse
from pathlib import Path
from build_concurrent_transport import build as base
from build import replace

def build(out,payload,base_builder=base):
 base_builder(out,payload)
 p=out/'dac960rtems.c';s=p.read_text()
 pos=s.index('static unsigned int changed(')
 helper='''/* Test-only ordered event stamps, readable after debugfs teardown. Each
 * slot has one writer. The atomic counter orders competing lifecycle entries. */
static atomic_t lifecycle_clock=ATOMIC_INIT(0);
static unsigned int lifecycle[16];
module_param_array(lifecycle,uint,NULL,0444);
static void life_event(unsigned int slot){WRITE_ONCE(lifecycle[slot],atomic_inc_return(&lifecycle_clock));}
'''
 s=s[:pos]+helper+s[pos:]
 s=replace(s,' d->control_taken=true;',' d->control_taken=true;life_event(1);')
 s=replace(s,' mutex_unlock(&d->control_lock);return rc;',' if(d->control_taken&&d->control_window)life_event(13);\n mutex_unlock(&d->control_lock);return rc;')
 s=replace(s,'        record(d,"CONCURRENT window closed/joined', '        life_event(4);\n        record(d,"CONCURRENT window closed/joined')
 s=replace(s,'    session_log_start(d);rc=session_step(d,request);','    life_event(0);session_log_start(d);rc=session_step(d,request);')
 s=replace(s,'    mutex_unlock(&d->session_lock);kfree(request);return rc?rc:count;','    life_event(5);mutex_unlock(&d->session_lock);kfree(request);return rc?rc:count;')
 s=replace(s,'int rc=0;\n    mutex_lock(&d->session_lock);','int rc=0;\n    life_event(3);mutex_lock(&d->session_lock);life_event(11);')
 s=replace(s,'    free_captures(d);release_firmware(d->payload);kfree(d);','    life_event(12);debugfs_remove_recursive(d->directory);\n    free_captures(d);release_firmware(d->payload);kfree(d);')
 s=replace(s,'    if(d->misc_registered) misc_deregister(&d->misc);','    life_event(2);\n    if(d->misc_registered) misc_deregister(&d->misc);')
 s=replace(s,'    if(d->owned && !d->pinned) {session_close(d);session_pin(d);}','    life_event(6);\n    if(d->owned && !d->pinned) {session_close(d);session_pin(d);}')
 s=replace(s,'    d->removed=true;\n    debugfs_remove_recursive(d->directory);','    session_log_end(d);d->removed=true;life_event(9);\n    /* Keep immutable capture blobs until final object release for this test. */')
 s=replace(s,'    pci_iounmap(pdev,d->bar);pci_release_regions(pdev);pci_disable_device(pdev);','    pci_iounmap(pdev,d->bar);life_event(10);pci_release_regions(pdev);pci_disable_device(pdev);')
 p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text()
 # stage_rehearsal.h is included before the instrumentation's definition.
 s='static void life_event(unsigned int slot);\n'+s
 s=replace(s,'    int rc=0, step, audit_rc=0;','    int rc=0, step, audit_rc=0;\n    life_event(7);')
 s=replace(s,'           step,d->pending,d->exec_dirty,d->stage_dirty);','           step,d->pending,d->exec_dirty,d->stage_dirty);\n    if(!step&&!d->pending&&!d->exec_dirty&&!d->stage_dirty)life_event(8);')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

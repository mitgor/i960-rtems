#!/usr/bin/env python3
"""Pinned STOP1 transport with a same-file concurrent control ioctl."""
import argparse
from pathlib import Path
from build_stop_transport import build as base
from build import replace
HERE=Path(__file__).resolve().parent

def build(out,payload):
 base(out,payload)
 p=out/'dac960rtems.c';s=p.read_text()
 s=replace(s,'    bool output_valid, stop_started, stop_clean;', '''    struct mutex control_lock;
    bool control_window,control_taken,control_done;
    int control_error;
    u32 control_epoch,control_sequence;
    bool output_valid, stop_started, stop_clean;''')
 s=replace(s,'    mutex_init(&d->session_lock);','    mutex_init(&d->session_lock);mutex_init(&d->control_lock);')
 start=s.index('/* Serialized under');end=s.index('static int issue(',start)
 s=s[:start]+(HERE/'concurrent_host.h').read_text()+'\n'+s[end:]
 start=s.index('    if(opcode==0x6f && slot==41 && d->stop_epoch){')
 end=s.index('    rc = readl_poll_timeout(d->bar + ODB',start)
 s=s[:start]+'''    if(opcode==0x6f && slot==41 && d->stop_epoch){
        d->stop_started=true;
        mutex_lock(&d->control_lock);
        d->control_epoch=d->stop_epoch;d->control_sequence=d->sequence;
        d->control_taken=d->control_done=false;d->control_error=0;
        d->control_window=true;mutex_unlock(&d->control_lock);
    }
'''+s[end:]
 s=replace(s,'    rc = readl_poll_timeout(d->bar + ODB, output, output & 1, 50, WAIT_US);', '''    rc = readl_poll_timeout(d->bar + ODB, output, output & 1, 50, WAIT_US);
    if(opcode==0x6f && slot==41 && d->stop_epoch){
        /* Join any ioctl before consuming completion or touching the shared log.
         * On uncertainty leave pending set, retaining the original resources. */
        mutex_lock(&d->control_lock);d->control_window=false;
        if(d->control_error)rc=d->control_error;
        else if(!d->control_done)rc=-ENODATA;
        record(d,"CONCURRENT window closed/joined rc=%d done=%u\\n",rc,d->control_done);
        mutex_unlock(&d->control_lock);
    }''')
 s=replace(s,'.owner=THIS_MODULE,.open=session_file_open,','.owner=THIS_MODULE,.unlocked_ioctl=concurrent_ioctl,.open=session_file_open,')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

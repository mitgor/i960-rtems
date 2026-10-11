#!/usr/bin/env python3
"""Pinned parked-firmware execution lease; no new DMA or interrupt ownership."""
import argparse,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('persist_builder',HERE.parent/'persistirq/build_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from build import replace

def build(out,payload):
 m.build(out,payload)
 p=out/'dac960rtems.c';s=p.read_text();s=replace(s,'bool control_window,control_taken,control_done;','bool control_window,control_taken,control_done,lease_granted;u32 lease_seq;')
 a=s.index('/* Lock order:');b=s.index('static int issue(',a);s=s[:a]+(HERE/'control_host.h').read_text()+'\nstatic unsigned int resident_retained[8];\nmodule_param_array(resident_retained,uint,NULL,0444);\n'+s[b:]
 s=replace(s,'d->control_taken=d->control_done=false;d->control_error=0;','d->control_taken=d->control_done=d->lease_granted=false;d->lease_seq=0;d->control_error=0;')
 # Only the explicitly leased callback gets a larger, still bounded host wait.
 s=replace(s,'output & 1, 50, WAIT_US);','output & 1, 50, (opcode==0x6f && slot==41 && d->stop_epoch)?125000000u:WAIT_US);');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text()
 # Keep the old gate in an explicit header; the new gate adds hardware evidence.
 original=(HERE.parent/'persistirq/report.h').read_text();assert s.startswith(original)
 s='#include "lease_report.h"\n'+s[len(original):]
 s=s.replace('!=1280','!=1408').replace('kmalloc(1280','kmalloc(1408').replace('i<320','i<352').replace('pirq_valid(w,','lease_valid(w,')
 s=replace(s,'    d->stop_delay_ms=bio_word(request+BIO_INPUT+8);','    if(bio_word(request+BIO_INPUT+8)>=1&&bio_word(request+BIO_INPUT+8)<=3&&bio_word(request+BIO_INPUT+12))return -EINVAL;\n    d->stop_delay_ms=bio_word(request+BIO_INPUT+8);')
 p.write_text(s);(out/'persist_report.h').write_text(original);(out/'lease_report.h').write_text((HERE/'report.h').read_text())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

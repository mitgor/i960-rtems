#!/usr/bin/env python3
"""Pinned concurrent containment test; never labels abandoned ISR frames drained."""
import argparse
from pathlib import Path
from build_concurrent_transport import build as base
from build import replace
HERE=Path(__file__).resolve().parent

def build(out,payload):
 base(out,payload)
 p=out/'dac960rtems.c';s=p.read_text()
 s=replace(s,'0x73000000u|d->control_epoch','0x75000000u|d->control_epoch')
 s=replace(s,'CONCURRENT DRAINED ioctl','CONCURRENT QUIESCED ioctl');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text()
 s=replace(s,'BIO_OFFSET+24)!=816','BIO_OFFSET+24)!=944')
 s=(HERE/'contain_report.h').read_text()+'\n'+s
 s=replace(s,'    rc=mu_cleanup(d,1,1);if(rc)return rc;', '''    {unsigned int words[236],i;
     for(i=0;i<236;i++)words[i]=bio_word(d->stage[6].data+BIO_OFFSET+BIO_OUTPUT+i*4);
     if(!contain_report_valid(words,d->stop_epoch))return -ENODATA;
    }
    record(d,"CONTAIN verified suspended workers, retained frames, restored timer; callback returned\\n");
    rc=mu_cleanup(d,1,1);if(rc)return rc;''')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

#!/usr/bin/env python3
"""Pin a separate STOP1 driver for critical-section and intentional omission tests."""
import argparse
from pathlib import Path
from build_stop_transport import build as base
from build import replace
HERE=Path(__file__).resolve().parent

def build(out,payload):
 base(out,payload)
 p=out/'dac960rtems.c';s=p.read_text().replace('stop_epoch,stop_delay_ms','stop_epoch,stop_delay_ms,stop_case')
 start=s.index('/* Serialized under');end=s.index('static int issue(',start)
 s=s[:start]+(HERE/'stop_cases_host.h').read_text()+'\n'+s[end:];p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text()
 s=replace(s,'d->stop_delay_ms=bio_word(request+BIO_INPUT+8);','d->stop_case=bio_word(request+BIO_INPUT+8);')
 s=replace(s,'d->stop_delay_ms<120||d->stop_delay_ms>200','d->stop_case<1||d->stop_case>4')
 s=replace(s,'BIO_OFFSET+24)!=816','BIO_OFFSET+24)!=896')
 # Only the expected missing-RELEASE bit is permissible in that case. Validate
 # the complete drain/timer/status evidence before marking cleanup complete.
 s=replace(s,'    rc=mu_cleanup(d,1,1);if(rc)return rc;', '''    {const u8 *r=d->stage[6].data+BIO_OFFSET+BIO_OUTPUT;
     if(bio_word(r+4)!=(d->stop_case==4?16384u:0u) ||
        bio_word(r+20)!=1 || bio_word(r+24)!=1 || bio_word(r+28) || bio_word(r+32) ||
        bio_word(r+36) || bio_word(r+40) || bio_word(r+44)!=0x10c7 ||
        bio_word(r+48)!=0x80000 || bio_word(r+52)!=bio_word(r+56) ||
        bio_word(r+60)||bio_word(r+64)||bio_word(r+68)||(bio_word(r+72)&0x2000)||bio_word(r+76) ||
        bio_word(r+736+14*4)!=(d->stop_case==3?6u:0u) ||
        bio_word(r+816)!=d->stop_case)return -ENODATA;
    }
    rc=mu_cleanup(d,1,1);if(rc)return rc;''')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

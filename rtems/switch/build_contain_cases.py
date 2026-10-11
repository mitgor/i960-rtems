#!/usr/bin/env python3
"""Critical-section containment, strict separate report/nonce contract."""
import argparse
from pathlib import Path
from build_contain_transport import build as base
from build import replace
HERE=Path(__file__).resolve().parent

def report_header():
 s=(HERE/'contain_report.h').read_text()
 s=replace(s,'contain_report_valid(const unsigned int*w,unsigned int epoch)', 'contain_case_base(const unsigned int*w,unsigned int epoch)')
 s=replace(s,'d[2]!=8','(d[2]!=17&&d[2]!=29)')
 s=replace(s,'d[3]<32','d[3]<18')
 s=replace(s,'d[7]!=1','(d[7]!=2&&d[7]!=3)')
 s=replace(s,'q[2]!=d[3]','q[2]!=40')
 return s+(HERE/'contain_cases_report.h').read_text()

def build(out,payload):
 base(out,payload)
 p=out/'dac960rtems.c';s=p.read_text().replace('stop_epoch,stop_delay_ms','stop_epoch,stop_delay_ms,contain_case');s=replace(s,' msleep(d->stop_delay_ms);',' /* READY identifies the requested depth; send STOP immediately. */');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text();s=replace(s,(HERE/'contain_report.h').read_text(),report_header())
 s=replace(s,'d->stop_delay_ms=bio_word(request+BIO_INPUT+8);','d->contain_case=bio_word(request+BIO_INPUT+8);')
 s=replace(s,'d->stop_delay_ms<120||d->stop_delay_ms>200','d->contain_case<1||d->contain_case>2')
 s=replace(s,'BIO_OFFSET+24)!=944','BIO_OFFSET+24)!=1024')
 s=replace(s,'words[236]','words[256]').replace('i<236','i<256')
 s=replace(s,'contain_report_valid(words,d->stop_epoch)','contain_cases_valid(words,d->stop_epoch,d->contain_case)')
 s=replace(s,'{unsigned int words[256],i;', '{unsigned int *words,i;int valid;\n     words=kmalloc(256*sizeof(*words),GFP_KERNEL);if(!words)return -ENOMEM;')
 s=replace(s,'if(!contain_cases_valid(words,d->stop_epoch,d->contain_case))return -ENODATA;', 'valid=contain_cases_valid(words,d->stop_epoch,d->contain_case);kfree(words);\n     if(!valid)return -ENODATA;')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

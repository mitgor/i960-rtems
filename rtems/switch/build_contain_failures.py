#!/usr/bin/env python3
"""Compose known lifetime retention with containment control/report failures."""
import argparse
from pathlib import Path
from build_contain_transport import build as containment
from build_lifecycle_transport import build as lifecycle
from build_failed_teardown import build as failures
from build import replace

def build(out,payload):
 failures(out,payload,base_builder=lambda o,p:lifecycle(o,p,base_builder=containment))
 p=out/'dac960rtems.c';s=p.read_text().replace('fail_control>2','fail_control>3').replace('omitted RELEASE after DRAINED','omitted RELEASE after QUIESCED')
 # stage_rehearsal is included before the instrumentation definition.
 s=replace(s,'#include "stage_rehearsal.h"','static unsigned int fail_control;\n#include "stage_rehearsal.h"');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text()
 s=replace(s,'     if(!contain_report_valid(words,d->stop_epoch))return -ENODATA;', '''     if(fail_control==3){
      record(d,"INJECT invalid local containment marker after paired response; original captures preserved\\n");
      words[230]=0;
     }
     if(!contain_report_valid(words,d->stop_epoch))return -ENODATA;''');p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

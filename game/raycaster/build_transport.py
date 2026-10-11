#!/usr/bin/env python3
"""Baseline RIO transport with host-only phase timestamps, unchanged checks."""
import argparse,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('rio_builder',ROOT/'rtems/transport/build.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from build import replace
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
m.build(a.out)
f=a.out/'stage_rehearsal.h';s=f.read_text()
s=replace(s,'int rc;u64 start=ktime_get_ns();','int rc;u64 start=ktime_get_ns(),p1,p2,p3,p4,p5;')
s=replace(s,'d->upload_data=NULL;if(rc) return rc;','d->upload_data=NULL;if(rc) return rc;\n    p1=ktime_get_ns();')
s=replace(s,'rc=issue(d,0x6f,0,0,0x5a,41);if(rc) return rc;', 'p2=ktime_get_ns();\n    rc=issue(d,0x6f,0,0,0x5a,41);if(rc) return rc;\n    p3=ktime_get_ns();')
s=replace(s,'d->steps++;','p4=ktime_get_ns();\n    d->steps++;')
s=replace(s,'d->output_valid=true;', '''p5=ktime_get_ns();
    record(d,"RAYPROFILE seq=%u upload=%llu arm=%llu execute=%llu verify=%llu audit=%llu total=%llu bytes=%u\\n",
       d->sequence,(unsigned long long)(p1-start),(unsigned long long)(p2-p1),
       (unsigned long long)(p3-p2),(unsigned long long)(p4-p3),
       (unsigned long long)(p5-p4),(unsigned long long)(p5-start),d->output_length);
    d->output_valid=true;''')
f.write_text(s)

#!/usr/bin/env python3
import argparse,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('callback_builder',HERE.parent/'callback/build_transport.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
replace=base.base.replace
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--queue',action='store_true');a=p.parse_args()
base.build(a.out,False,True)
p=a.out/'stage_rehearsal.h';s=p.read_text()
s=replace(s,'d->output_length=(d->steps%32)?BIO_IMAGE_SIZE:IMAGE_WINDOW;', 'd->output_length=IMAGE_WINDOW; /* prototype: paired full allocation EVERY step */')
if a.queue:
 (a.out/'queue.h').write_text((HERE/'queue.h').read_text())
 s=replace(s,'/* Persistent BIO1',(HERE/'transport.h').read_text()+'\n/* Persistent BIO1')
 s=replace(s,'int rc;u64 start=ktime_get_ns(),p1,p2,p3,p4,p5;', 'int rc,qrc;u64 start=ktime_get_ns(),p1,p2,p3,p4,p5,qt;')
 s=replace(s,'    rc=session_output(d,d->output_length);if(rc) return rc;', '''    qrc=fq_targeted(d);qt=ktime_get_ns();
    if(d->pending)return qrc; /* never issue more DMA after uncertain completion */
    rc=session_output(d,d->output_length);if(rc)return rc;
    if(qrc)return qrc;
    rc=fq_match_audit(d);if(rc)return rc;
    record(d,"FQPROFILE seq=%u mask=%u targeted_ns=%llu full_audit_ns=%llu\\n",d->sequence,
           fq_word(d->capture[54].data+16),(unsigned long long)(qt-p4),
           (unsigned long long)(ktime_get_ns()-qt));''')
p.write_text(s)
if a.queue:
 p=a.out/'dac960rtems.c';s=p.read_text()
 s=replace(s,'#include "quiet_policy.h"','#include "quiet_policy.h"\n#include "queue.h"')
 s=replace(s,'struct capture capture[54];','struct capture capture[60];')
 # Allocation, publication, and cleanup must all follow the expanded array.
 assert s.count('i < 54')==3
 s=s.replace('i < 54','i < ARRAY_SIZE(d->capture)')
 s=replace(s,'    d->audit_address = address;', '''    if(slot>=ARRAY_SIZE(d->capture)-1 || !count ||
       !d->capture[slot].data || !d->capture[slot+1].data ||
       count>d->capture[slot].blob.size || count>d->capture[slot+1].blob.size)
        return -EINVAL;
    d->audit_address = address;''')
 s=replace(s,'"exec-flash-followup.bin", "exec-stock-followup.bin"','''"exec-flash-followup.bin", "exec-stock-followup.bin",
        "frame-descriptor-a5.bin", "frame-descriptor-5a.bin",
        "frame-slot0-a5.bin", "frame-slot0-5a.bin", "frame-slot1-a5.bin", "frame-slot1-5a.bin"''')
 s=replace(s,'        d->capture[i].data = kzalloc', '        if(i>=54)d->capture[i].blob.size=i<56?64:FQ_SLOT_SIZE;\n        d->capture[i].data = kzalloc')
 p.write_text(s)
(a.out/'queue-build.json').write_text(json.dumps(dict(queue=a.queue,paired_full_every_step=True,poll_us=50),indent=2)+'\n')

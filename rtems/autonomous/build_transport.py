#!/usr/bin/env python3
"""Generate a pinned autonomous transport with stop-before-restore on release."""
import argparse,hashlib,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'rtems/transport'))
import wire
spec=importlib.util.spec_from_file_location('rtems_builder',ROOT/'rtems/transport/build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from build import replace

def build(out,payload,network=False):
 m.build(out)
 sha=hashlib.sha256(wire.prepare(payload.read_bytes())).digest()
 p=out/'dac960rtems.c';s=p.read_text();s=replace(s,'    bool output_valid;','    bool output_valid, irq_may_run;')
 s=s.replace('dac960rtems','dac960auto').replace('i960-rtems','i960-auto');(out/'dac960auto.c').write_text(s);p.unlink()
 p=out/'Makefile';p.write_text(p.read_text().replace('dac960rtems','dac960auto'))
 p=out/'stage_rehearsal.h';s=p.read_text()
 s=replace(s,'    if(memcmp(d->stage[6].data,d->stage[7].data,length) ||', '''    /* Autonomous private state can advance between reads. Both immutable
     * regions and both independently validated BIO responses must agree. */
    if(memcmp(d->stage[6].data,d->stage[7].data,0x20010u) ||
       memcmp(d->stage[6].data+0x6fff0u,d->stage[7].data+0x6fff0u,length-0x6fff0u) ||
       !bio_response_valid(d->stage[2].data,d->stage[7].data,length) ||''')
 pos=s.index('static int session_close(')
 helper='''static int session_step(struct experiment *d,const u8 *request);
static int autonomous_stop(struct experiment *d)
{
    u8 *request;u32 n;int rc;bool saved_ready;
    if(!d->irq_may_run){if(d->steps)record(d,"AUTONOMOUS STOP verified before any RAM restoration (previous close)\\n");return 0;}
    if(d->pending||d->runner_uncertain||!d->exec_dirty||!d->stage_dirty||d->sequence==0xffffffffu)return -EBUSY;
    request=kzalloc(BIO_SIZE,GFP_KERNEL);if(!request)return -ENOMEM;
    bio_put(request,BIO_MAGIC);bio_put(request+4,BIO_VERSION);
    bio_put(request+8,d->sequence+1);bio_put(request+12,16);bio_put(request+16,64);bio_put(request+20,BIO_PENDING);
    bio_put(request+BIO_INPUT,0x31415452u);bio_put(request+BIO_INPUT+4,2);
    memset(request+BIO_GUARD1,0xa5,16);memset(request+BIO_OUTPUT,0xcc,BIO_OUTPUT_MAX);memset(request+BIO_GUARD2,0x5a,16);
    record(d,"AUTONOMOUS before-stop user result=%08x\\n",sp_word(d->capture[20].data));
    /* A controlled user-code failure sets ready=false in fileops. STOP is a
     * distinct masked entry and does not resume that failed task context. */
    saved_ready=d->ready;d->ready=true;rc=session_step(d,request);d->ready=saved_ready;
    kfree(request);if(rc)return rc;
    n=BIO_OFFSET+BIO_OUTPUT;
    if(bio_word(d->stage[6].data+BIO_OFFSET+24)!=64 ||
       bio_word(d->stage[6].data+n)!=0x31415452u ||
       bio_word(d->stage[6].data+n+4) || bio_word(d->stage[6].data+n+60) ||
       bio_word(d->stage[6].data+n+28)!=0x10c7u ||
       bio_word(d->stage[6].data+n+32)!=0x80000u ||
       bio_word(d->stage[6].data+n+36)!=bio_word(d->stage[6].data+n+40) ||
       bio_word(d->stage[6].data+n+44) || bio_word(d->stage[6].data+n+48) ||
       bio_word(d->stage[6].data+n+52) || (bio_word(d->stage[6].data+n+56)&0x2000u))return -ENODATA;
    d->irq_may_run=false;
    record(d,"AUTONOMOUS STOP verified before any RAM restoration\\n");return 0;
}
'''
 if network:helper=helper.replace('bio_put(request+BIO_INPUT+4,2);','bio_put(request+BIO_INPUT+4,6);')
 s=s[:pos]+helper+s[pos:]
 s=replace(s,'    int rc=0, step, audit_rc=0;','    int rc=0, step, audit_rc=0;\n    rc=autonomous_stop(d);if(rc)return rc;')
 s=replace(s,'    if(!d->runtime_verified) return -EPERM;', '    if(!d->runtime_verified) return -EPERM;\n    { static const u8 allowed[32]={'+','.join(str(x) for x in sha)+'};\n      rc=load_digest(d->payload->data,d->payload->size,expected);\n      if(rc||memcmp(expected,allowed,32))return -EPERM; }')
 s=replace(s,'    d->runner_uncertain=true; /* before the first possible arm write */','    d->irq_may_run=true; /* retained until explicit stop acknowledgement */\n    d->runner_uncertain=true; /* before the first possible arm write */')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);p.add_argument('--network',action='store_true');a=p.parse_args();build(a.out,a.payload,a.network)

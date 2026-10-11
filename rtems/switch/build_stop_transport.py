#!/usr/bin/env python3
"""Exact-image-pinned one-shot STOP1 host test during a pending callback."""
import argparse,hashlib,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'transport'))
import wire
spec=importlib.util.spec_from_file_location('base',HERE.parent/'transport/build.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from build import replace

def build(out,payload):
 m.build(out)
 sha=hashlib.sha256(wire.prepare(payload.read_bytes())).digest()
 p=out/'dac960rtems.c';s=p.read_text()
 s=replace(s,'    bool output_valid;','    bool output_valid, stop_started, stop_clean; u32 stop_epoch,stop_delay_ms;')
 s=replace(s,'static int issue(', (HERE/'stop_host.h').read_text()+'\nstatic int issue(')
 s=replace(s,'    writel(1, d->bar + IDB);','''    writel(1, d->bar + IDB);
    if(opcode==0x6f && slot==41 && d->stop_epoch){
        d->stop_started=true;rc=stop_exchange(d);
        if(rc){record(d,"STOP1 uncertain rc=%d; retain pending command/resources\\n",rc);return rc;}
    }''')
 p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text()
 s=replace(s,'    if(!d->runtime_verified) return -EPERM;', '    if(!d->runtime_verified) return -EPERM;\n    { static const u8 allowed[32]={'+','.join(str(x) for x in sha)+'};\n      rc=load_digest(d->payload->data,d->payload->size,expected);\n      if(rc||memcmp(expected,allowed,32))return -EPERM; }')
 s=replace(s,'    /* Consume sequence before submission:', '''    if(d->steps || bio_word(request+12)!=12 || bio_word(request+BIO_INPUT)!=0x31505453u)return -EINVAL;
    d->stop_epoch=bio_word(request+BIO_INPUT+4);d->stop_delay_ms=bio_word(request+BIO_INPUT+8);
    if(!d->stop_epoch||d->stop_epoch>65535||d->stop_delay_ms<120||d->stop_delay_ms>200)return -EINVAL;
    /* Consume sequence before submission:''')
 cleanup=(HERE.parent/'control/mu_cleanup.h').read_text().replace('mu_cleanup(unsigned int owned,unsigned int used)','mu_cleanup(struct experiment*d,unsigned int owned,unsigned int used)')
 cleanup='#define MU_READ(off) readl(d->bar+(off))\n#define MU_WRITE(off,v) writel((v),d->bar+(off))\n'+cleanup+'\n#undef MU_READ\n#undef MU_WRITE\n'
 s=replace(s,'static int session_close(',cleanup+'\nstatic int session_close(')
 s=replace(s,'    int rc=0, step, audit_rc=0;', '    int rc=0, step, audit_rc=0;\n    if(d->stop_started&&!d->stop_clean)return -EBUSY;')
 s=replace(s,'    d->output_valid=true;', '''    if(bio_word(d->stage[6].data+BIO_OFFSET+24)!=816 ||
       bio_word(d->stage[6].data+BIO_OFFSET+BIO_OUTPUT+736+13*4)!=0x4d554f4bu)return -ENODATA;
    rc=mu_cleanup(d,1,1);if(rc)return rc;
    record(d,"STOP1 callback returned; MU words/masks restored, host OISR acknowledged\\n");
    d->stop_clean=true;d->output_valid=true;''')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

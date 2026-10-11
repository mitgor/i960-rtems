#!/usr/bin/env python3
"""Persistent ownership session: exact image pin and explicit finalization gate."""
import argparse,hashlib,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'transport'))
import wire
spec=importlib.util.spec_from_file_location('transport_builder',HERE.parent/'transport/build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from build import replace

def build(out,payload):
 m.build(out);digest=hashlib.sha256(wire.prepare(payload.read_bytes())).digest()
 p=out/'dac960rtems.c';s=p.read_text()
 s=replace(s,'    bool output_valid;', '    bool output_valid,ownership_open,ownership_final;')
 s=replace(s,'static int issue(', 'static unsigned int ownership_retained[6];\nmodule_param_array(ownership_retained,uint,NULL,0444);\nstatic int issue(')
 s=replace(s,'d->pinned=true;', '''d->pinned=true;
        ownership_retained[0]=d->ownership_open;ownership_retained[1]=d->pending;
        ownership_retained[2]=d->exec_dirty;ownership_retained[3]=d->stage_dirty;
        ownership_retained[4]=d->dma_buf!=NULL;ownership_retained[5]=d->bar!=NULL;''');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text();s=(HERE/'report.h').read_text()+'\n'+s
 s=replace(s,'    if(!d->runtime_verified) return -EPERM;', '    if(!d->runtime_verified) return -EPERM;\n    {static const u8 allowed[32]={'+','.join(str(x) for x in digest)+'};\n     rc=load_digest(d->payload->data,d->payload->size,expected);if(rc||memcmp(expected,allowed,32))return -EPERM;}')
 s=replace(s,'    int rc=0, step, audit_rc=0;', '    int rc=0, step, audit_rc=0;\n    if(d->ownership_open){record(d,"OWNERSHIP refuses restore before finalization\\n");return -EBUSY;}')
 s=replace(s,'    /* Consume sequence before submission:', '''    if(d->ownership_final||bio_word(request+12)!=16||bio_word(request+BIO_INPUT)!=0x314e574fu||bio_word(request+BIO_INPUT+4)>12)return -EINVAL;
    /* Consume sequence before submission:''')
 s=replace(s,'    d->runner_uncertain=true;', '    d->ownership_open=true;\n    d->runner_uncertain=true;')
 s=replace(s,'    d->output_valid=true;', '''    {unsigned int w[64],i;
     if(bio_word(d->stage[6].data+BIO_OFFSET+24)!=256)return -ENODATA;
     for(i=0;i<64;i++)w[i]=bio_word(d->stage[6].data+BIO_OFFSET+BIO_OUTPUT+i*4);
     if(!ownership_report_valid(w,d->sequence,bio_word(request+BIO_INPUT+4)))return -ENODATA;
     if(w[5]){d->ownership_open=false;d->ownership_final=true;
      record(d,"OWNERSHIP FINALIZED: all workers suspended, no external leases, callback returned\\n");}
    }
    d->output_valid=true;''');p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

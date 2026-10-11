#!/usr/bin/env python3
"""Persistent exact-image-pinned asynchronous session and terminal cleanup gate."""
import argparse,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'switch'))
from build_concurrent_transport import build as base
from build import replace

def build(out,payload):
 base(out,payload)
 p=out/'dac960rtems.c';s=p.read_text();s=replace(s,'bool output_valid, stop_started, stop_clean;','bool output_valid, stop_started, stop_clean, resident_open, resident_final;')
 s=replace(s,'0x73000000u|d->control_epoch','0x75000000u|d->control_epoch');s=replace(s,'CONCURRENT DRAINED ioctl','CONCURRENT QUIESCED ioctl');s=replace(s,' msleep(d->stop_delay_ms);',' /* STOP immediately after epoch READY. */')
 s=replace(s,'static int issue(', 'static unsigned int resident_retained[8];\nmodule_param_array(resident_retained,uint,NULL,0444);\nstatic int issue(')
 s=replace(s,'d->pinned=true;', '''d->pinned=true;
        resident_retained[0]=d->resident_open;resident_retained[1]=d->pending;
        resident_retained[2]=d->runner_uncertain;resident_retained[3]=d->exec_dirty;
        resident_retained[4]=d->stage_dirty;resident_retained[5]=d->dma_buf!=NULL;
        resident_retained[6]=d->bar!=NULL;resident_retained[7]=d->stop_clean;''');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text();s=(HERE/'report.h').read_text()+'\n'+s
 s=replace(s,'    if(d->stop_started&&!d->stop_clean)return -EBUSY;', '    if(d->resident_open){record(d,"PIRQ refuses restore before FINALIZE\\n");return -EBUSY;}\n    if(d->stop_started&&!d->stop_clean)return -EBUSY;')
 a=s.index('    if(d->steps || bio_word(request+12)!=12');b=s.index('    /* Consume sequence',a)
 s=s[:a]+'''    if(d->resident_final||bio_word(request+12)!=16||bio_word(request+BIO_INPUT)!=0x31515250u||bio_word(request+BIO_INPUT+8)>6||bio_word(request+8)>65535)return -EINVAL;
    d->stop_delay_ms=bio_word(request+BIO_INPUT+8);
    if(!d->steps&&(d->stop_delay_ms<1||d->stop_delay_ms>2))return -EINVAL;
    d->stop_epoch=(d->stop_delay_ms>=1&&d->stop_delay_ms<=3)?bio_word(request+8):0;
    d->stop_started=d->stop_clean=false;
'''+s[b:]
 s=replace(s,'    d->runner_uncertain=true;', '    d->resident_open=true;\n    d->runner_uncertain=true;')
 a=s.index('    if(bio_word(d->stage[6].data+BIO_OFFSET+24)!=816');b=s.index('    d->stop_clean=true;d->output_valid=true;',a)+len('    d->stop_clean=true;d->output_valid=true;')
 s=s[:a]+'''    {unsigned int *w,i;int valid,final;
     if(bio_word(d->stage[6].data+BIO_OFFSET+24)!=1280)return -ENODATA;
     w=kmalloc(1280,GFP_KERNEL);if(!w)return -ENOMEM;
     for(i=0;i<320;i++)w[i]=bio_word(d->stage[6].data+BIO_OFFSET+BIO_OUTPUT+i*4);
     valid=pirq_valid(w,d->sequence,d->stop_delay_ms);final=w[7];kfree(w);
     if(!valid){record(d,"PIRQ report rejected; retain resident resources\\n");return -ENODATA;}
     if(d->stop_epoch){rc=mu_cleanup(d,1,1);if(rc)return rc;d->stop_clean=true;}
     if(final){d->resident_open=false;d->resident_final=true;record(d,"PIRQ FINALIZED: terminal resource proof and callback return\\n");}
    }
    d->output_valid=true;'''+s[b:];p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

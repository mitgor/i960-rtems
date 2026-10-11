#!/usr/bin/env python3
"""Exact image, concurrent STOP, and resource-aware post-completion cleanup gate."""
import argparse,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'switch'))
from build_concurrent_transport import build as base
from build import replace

def build(out,payload):
 base(out,payload)
 p=out/'dac960rtems.c';s=p.read_text();s=replace(s,'0x73000000u|d->control_epoch','0x75000000u|d->control_epoch');s=replace(s,'CONCURRENT DRAINED ioctl','CONCURRENT QUIESCED ioctl');s=replace(s,' msleep(d->stop_delay_ms);',' /* READY selects the critical interval; STOP immediately. */')
 s=replace(s,'static int issue(', 'static unsigned int ownership_retained[8];\nmodule_param_array(ownership_retained,uint,NULL,0444);\nstatic int issue(')
 s=replace(s,'d->pinned=true;', '''d->pinned=true;
        ownership_retained[0]=d->stop_started;ownership_retained[1]=d->stop_clean;
        ownership_retained[2]=d->pending;ownership_retained[3]=d->runner_uncertain;
        ownership_retained[4]=d->exec_dirty;ownership_retained[5]=d->stage_dirty;
        ownership_retained[6]=d->dma_buf!=NULL;ownership_retained[7]=d->bar!=NULL;''');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text();s=replace(s,'d->stop_delay_ms<120||d->stop_delay_ms>200','d->stop_delay_ms<1||d->stop_delay_ms>5')
 s=replace(s,'BIO_OFFSET+24)!=816','BIO_OFFSET+24)!=1024');s=replace(s,'BIO_OUTPUT+736+13*4','BIO_OUTPUT+254*4')
 s=(HERE/'report.h').read_text()+'\n'+s
 s=replace(s,'    rc=mu_cleanup(d,1,1);if(rc)return rc;', '''    {unsigned int *w,i;int valid;
     w=kmalloc(1024,GFP_KERNEL);if(!w)return -ENOMEM;
     for(i=0;i<256;i++)w[i]=bio_word(d->stage[6].data+BIO_OFFSET+BIO_OUTPUT+i*4);
     valid=ownirq_report_valid(w,d->stop_epoch,d->stop_delay_ms);kfree(w);
     if(!valid){record(d,"OWNIRQ resource proof rejected after callback completion; retain resources\\n");return -ENODATA;}
    }
    record(d,"OWNIRQ verified resource ownership, suspended workers, timer restored and no external leases\\n");
    rc=mu_cleanup(d,1,1);if(rc)return rc;''');p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

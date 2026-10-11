#!/usr/bin/env python3
import argparse,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('auto_builder',HERE.parent/'autonomous/build_transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from build import replace

def build(out,payload):
 m.build(out,payload)
 p=out/'dac960auto.c';s=p.read_text();s=replace(s,'bool output_valid, irq_may_run;','bool output_valid, irq_may_run,mu_used,mu_failed,mu_halted,mu_resident;unsigned int monitor_epoch;')
 s=replace(s,'static const struct file_operations session_fops=',(HERE/'host.h').read_text()+'\nstatic const struct file_operations session_fops=');s=replace(s,'.owner=THIS_MODULE,.open=session_file_open,','.owner=THIS_MODULE,.unlocked_ioctl=monitor_ioctl,.open=session_file_open,');p.write_text(s)
 p=out/'stage_rehearsal.h';s=p.read_text();cleanup=(HERE.parent/'control/mu_cleanup.h').read_text().replace('mu_cleanup(unsigned int owned,unsigned int used)','mu_cleanup(struct experiment*d,unsigned int owned,unsigned int used)')
 cleanup='#define MU_READ(off) readl(d->bar+(off))\n#define MU_WRITE(off,v) writel((v),d->bar+(off))\n'+cleanup+'\n#undef MU_READ\n#undef MU_WRITE\n'
 s=replace(s,'static int autonomous_stop(',cleanup+'\nstatic int autonomous_stop(')
 s=replace(s,'    if(!d->irq_may_run)', '    if(d->mu_failed||d->mu_resident)return -EBUSY;\n    if(!d->irq_may_run)')
 s=replace(s,'    /* Consume sequence before submission:', '''    if(!d->steps){
      if(bio_word(request+12)!=16||bio_word(request+BIO_INPUT)!=0x31415452||bio_word(request+BIO_INPUT+4)!=1)return -EINVAL;
      d->monitor_epoch=bio_word(request+BIO_INPUT+8);if(!d->monitor_epoch||d->monitor_epoch>65535)return -EINVAL;
    }
    /* Consume sequence before submission:''')
 s=replace(s,'    d->irq_may_run=false;', '''    rc=mu_cleanup(d,bio_word(d->stage[6].data+n+8)==0x4d554f4bu,d->mu_used);if(rc)return rc;
    record(d,"MONITOR timer/MU restored before RAM cleanup\\n");d->irq_may_run=false;''');p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

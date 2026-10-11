#!/usr/bin/env python3
"""Test-only lost-control injection with read-only retained-resource snapshots."""
import argparse
from pathlib import Path
from build_lifecycle_transport import build as base
from build import replace

def build(out,payload,base_builder=base):
 base_builder(out,payload)
 p=out/'dac960rtems.c';s=p.read_text()
 anchor='static atomic_t lifecycle_clock=ATOMIC_INIT(0);'
 s=replace(s,anchor,'''static unsigned int fail_control;
module_param(fail_control,uint,0444);
/* Never dereference BAR/DMA for this snapshot. All calls hold session_lock. */
static unsigned int retention[16];
module_param_array(retention,uint,NULL,0444);
static void retention_snapshot(struct experiment*d){
 retention[0]=d->pending;retention[1]=d->exec_dirty;retention[2]=d->stage_dirty;
 retention[3]=d->runner_uncertain;retention[4]=d->stop_started;retention[5]=d->stop_clean;
 retention[6]=d->pinned;retention[7]=d->removed;retention[8]=d->owned;
 retention[9]=d->control_window;retention[10]=d->control_done;
 retention[11]=(unsigned int)(-d->control_error);
 retention[12]=d->dma_buf!=NULL;retention[13]=d->bar!=NULL;
 retention[14]=d->steps;retention[15]=fail_control;
}
'''+anchor)
 s=replace(s,' record(d,"CONCURRENT STOP ioctl', ''' if(fail_control==1){record(d,"INJECT omitted STOP after READY; control result uncertain\\n");rc=-ETIMEDOUT;goto failed;}
 record(d,"CONCURRENT STOP ioctl''')
 s=replace(s,' writel(0x74000000u|d->control_epoch,d->bar+0x14);', ''' if(fail_control==2){record(d,"INJECT omitted RELEASE after DRAINED; control result uncertain\\n");rc=-ETIMEDOUT;goto failed;}
 writel(0x74000000u|d->control_epoch,d->bar+0x14);''')
 s=replace(s,'    life_event(5);mutex_unlock', '    retention_snapshot(d);life_event(5);mutex_unlock')
 s=replace(s,'    d->owned=false;', '    d->owned=false;retention_snapshot(d);')
 s=replace(s,'    session_log_end(d);d->removed=true;life_event(9);','    session_log_end(d);d->removed=true;life_event(9);retention_snapshot(d);')
 s=replace(s,'    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);','    life_event(14);dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);')
 s=replace(s,'life_event(10);pci_release_regions(pdev);','life_event(10);life_event(15);pci_release_regions(pdev);')
 # Invalid injection modes are refused before touching the device at probe.
 s=replace(s,'    if (!buffer_io || !firmware_name || !stage_check','    if (fail_control<1 || fail_control>2)return -EINVAL;\n    if (!buffer_io || !firmware_name || !stage_check')
 p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--payload',type=Path,required=True);a=p.parse_args();build(a.out,a.payload)

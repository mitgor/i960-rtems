/* Failure-only frozen fault report. Never clears poison, ACKs a frame, changes
 * DMA registers or permits reuse. At most 2 seconds and 2000 polls per word. */
static void frame_dma_terminal(struct experiment*d,unsigned epoch){
 unsigned i,j,v=0,rc=0;unsigned long end=jiffies+msecs_to_jiffies(2000);
 d->frame_dma_fault[0]=0x31464446;d->frame_dma_fault[1]=epoch;
 for(i=0;i<96;i++){
  writel(0x91000000u|(i<<16)|epoch,d->bar+0x14);readl(d->bar+0x14);
  for(j=0;j<2000;j++){
   if(time_after_eq(jiffies,end)){rc=1;break;}
   if((readl(d->bar+ODB)&1)||readl(d->bar+0x28)!=0x1fb||readl(d->bar+0x34)!=0xff){rc=2;break;}
   if(readl(d->bar+0x1c)==(0x92000000u|(i<<16)|epoch)&&!readl(d->bar+0x14)){v=readl(d->bar+0x18);break;}
   usleep_range(50,100);
  }
  if(rc||j==2000){if(!rc)rc=3;break;}
  d->frame_dma_fault[4+i]=v;d->frame_dma_fault[2]=i+1;
  if((i==0&&v!=0x31464d4e)||(i==1&&v!=epoch)){rc=4;break;}
 }
 d->frame_dma_fault[3]=rc;d->frame_dma_fault_blob.data=d->frame_dma_fault;d->frame_dma_fault_blob.size=sizeof(d->frame_dma_fault);
 debugfs_create_blob("frame-dma-fault.bin",0400,d->directory,&d->frame_dma_fault_blob);
 record(d,"FRAME DMA diagnostic words=%u rc=%u; session remains poisoned\n",d->frame_dma_fault[2],rc);
}
#define FRAME_DMA_DIAG(d,e) frame_dma_terminal(d,e)

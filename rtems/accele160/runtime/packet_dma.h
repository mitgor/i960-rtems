/* Runtime replies borrow DMA0 only after Doom has retired. Reuse the existing
 * pinned slot 0; no new host address, allocation, IRQ or release path. Marker
 * follows the complete 4 KiB reply page. Init cannot process another request
 * until the finite chain is drained. Frame counters remain frame counters. */
static unsigned int packet_dma_completed;
static void packet_dma_reply(unsigned int seq,unsigned int epoch,const void *source){
 unsigned int i,csr,desc=dma_desc_addr();volatile unsigned int *d=(volatile unsigned int*)desc;
 if(!game_idle||engine_running||!dma_initialized||dma_phase||!seq||!epoch)
  bounded_fatal(0x78101u);
 dma_peer_check();
 if(REG(0x1400u)||REG(0x1404u)||REG(0x1410u)||REG(0x1420u)||
    REG(0x140cu)!=desc+32u||REG(0x1424u)!=7u)bounded_fatal(0x78102u);
 for(i=0;i<16u;i++)d[i]=0;
 d[0]=desc+32u;d[1]=dma_bus[0];d[3]=(unsigned int)source;d[4]=4096u;d[5]=7u;
 d[9]=dma_bus[0]+FRAME_BYTES;d[11]=(unsigned int)dma_marker;d[12]=32u;d[13]=7u;
 dma_marker[0]=0x31525044u;dma_marker[1]=epoch;dma_marker[2]=seq;dma_marker[3]=0;
 dma_marker[4]=4096u;dma_marker[5]=(unsigned int)source;dma_marker[6]=~epoch;dma_marker[7]=~seq;
 dma_log[18]=1;dma_log[19]=seq;DMA_SYNC();REG(0x1410u)=desc;REG(0x1400u)=1;
 for(i=0;i<1000000u;i++){
  csr=REG(0x1404u);
  if(csr&0x2du)bounded_fatal(0x78103u);
  if(!(csr&0x400u)&&REG(0x140cu)==desc+32u&&!REG(0x1410u)&&!REG(0x1420u))break;
 }
 if(i==1000000u)bounded_fatal(0x78104u); /* Retain everything on uncertainty. */
 REG(0x1400u)=0;DMA_SYNC();
 if(REG(0x1400u)||REG(0x1404u)||REG(0x140cu)!=desc+32u||REG(0x1410u)||REG(0x1420u)||REG(0x1424u)!=7u)
  bounded_fatal(0x78105u);
 dma_peer_check();packet_dma_completed++;dma_log[17]=packet_dma_completed;dma_log[18]=0;dma_log[20]=i;
}

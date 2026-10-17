/* Channel 0 only. Source/image ownership and host-target lifetimes differ.
 * Descriptor 2 publishes the marker after all frame bytes reach host RAM.
 * Host ACK permits destination reuse; CSR drain permits source reuse. */
#ifndef DMA_CFG_PTR
#define DMA_CFG_PTR ((volatile unsigned int*)0xc000fd40u)
#define DMA_LOG_PTR ((volatile unsigned int*)0xc000fd80u)
#define DMA_SYNC() __asm__ volatile("syncf":::"memory")
#endif
static volatile unsigned int *const dma_cfg=DMA_CFG_PTR;
static volatile unsigned int *const dma_log=DMA_LOG_PTR;
static unsigned int dma_store[24] __attribute__((aligned(16)));
static unsigned int dma_marker[8] __attribute__((aligned(16)));
static unsigned int dma_bus[2],dma_peers[2][8],dma_phase,dma_gen,dma_slot,dma_polls;
static unsigned int dma_initialized,dma_start_tick,dma_completed;
static const unsigned int dma_offsets[8]={0,12,16,20,24,28,32,36};
static unsigned int dma_desc_addr(void){return ((unsigned int)dma_store+31u)&~31u;}
static void dma_peer_check(void){unsigned ch,i;
 for(ch=1;ch<3u;ch++)for(i=0;i<8u;i++)
  if(REG(0x1400u+ch*64u+dma_offsets[i])!=dma_peers[ch-1u][i])bounded_fatal(0x78001u);
}
static void dma_init(void){unsigned i,ch;
 if(dma_initialized)return;
 if(dma_cfg[0]!=0x31464d44u||dma_cfg[1]!=BRIDGE_EPOCH||
    dma_cfg[4]!=FRAME_BYTES||dma_cfg[5]!=0x314d5241u||
    (dma_cfg[6]!=4u&&dma_cfg[6]!=32u)||(dma_cfg[7]&~1u))bounded_fatal(0x78002u);
 for(i=0;i<2u;i++){
  unsigned v=dma_cfg[2u+i];
  if((v&4095u)||v<0x10000u||v>0xfffe0000u)bounded_fatal(0x78003u);
  dma_bus[i]=v;
 }
 if(!(dma_bus[0]+73728u<=dma_bus[1]-4096u||
      dma_bus[1]+73728u<=dma_bus[0]-4096u))bounded_fatal(0x78004u);
 for(i=8u;i<16u;i++)if(dma_cfg[i])bounded_fatal(0x78005u);
 if(dma_busy_mask()||REG(0x1404u))bounded_fatal(0x78006u);
 for(ch=1u;ch<3u;ch++)for(i=0;i<8u;i++)dma_peers[ch-1u][i]=REG(0x1400u+ch*64u+dma_offsets[i]);
 for(i=0;i<32u;i++)dma_log[i]=0u;
 dma_log[0]=0x31464d44u;dma_log[1]=BRIDGE_EPOCH;
 dma_initialized=1u;
}
static void dma_step(void){unsigned csr,desc=dma_desc_addr();
 if(dma_phase!=1u)return;
 csr=REG(0x1404u);dma_polls++;dma_log[9]=csr;
 if(csr&0x2du)bounded_fatal(0x78007u);
 if(REG(0x140cu)==desc+32u&&!REG(0x1420u)&&!REG(0x1410u)&&!(csr&0x400u)){
  REG(0x1400u)=0u;
  if(REG(0x1400u)||REG(0x140cu)!=desc+32u||REG(0x1410u)||REG(0x1420u))bounded_fatal(0x78008u);
  dma_peer_check();
  dma_phase=0u;dma_completed++;
  dma_log[2]=0u;dma_log[10]=ticks;dma_log[11]=dma_completed;
  dma_log[12]=dma_polls;dma_log[13]=REG(0x140cu);
  dma_log[14]=REG(0x1410u);dma_log[15]=REG(0x1420u);
 }
 if(dma_phase&&ticks-dma_start_tick>=50u)bounded_fatal(0x78009u);
}
static void dma_drain(void){unsigned polls=0;
 while(dma_phase){
  dma_step();
  if(dma_phase&&!(++polls&1023u)){
   if(rtems_task_wake_after(1)!=RTEMS_SUCCESSFUL)bounded_fatal(0x7800au);
   priority0();
  }
 }
}
static void dma_kick(unsigned gen,unsigned slot,const void *source,unsigned hash,unsigned published_tick){
 unsigned i,desc=dma_desc_addr();volatile unsigned int*d=(volatile unsigned int*)desc;
 dma_drain();dma_peer_check();
 if(REG(0x1400u)||REG(0x1410u)||REG(0x1420u)||REG(0x1404u))bounded_fatal(0x7800bu);
 if(dma_completed&&(REG(0x140cu)!=desc+32u||REG(0x1424u)!=7u))bounded_fatal(0x7800cu);
 for(i=0;i<16u;i++)d[i]=0u;
 d[0]=desc+32u;d[1]=dma_bus[slot];d[3]=(unsigned int)source;d[4]=FRAME_BYTES;d[5]=7u;
 d[9]=dma_bus[slot]+FRAME_BYTES;d[11]=(unsigned int)dma_marker;d[12]=32u;d[13]=7u;
 dma_marker[0]=0x31505044u;dma_marker[1]=BRIDGE_EPOCH;dma_marker[2]=gen;dma_marker[3]=slot;
 dma_marker[4]=FRAME_BYTES;dma_marker[5]=(unsigned int)source;dma_marker[6]=published_tick;dma_marker[7]=~gen;
 dma_gen=gen;dma_slot=slot;dma_polls=0;dma_start_tick=ticks;dma_phase=1u;
 dma_log[2]=1u;dma_log[3]=gen;dma_log[4]=slot;dma_log[5]=(unsigned int)source;
 dma_log[6]=dma_bus[slot];dma_log[7]=desc;dma_log[8]=ticks;dma_log[16]=hash;
 DMA_SYNC();
 REG(0x1410u)=desc;REG(0x1400u)=1u;
}

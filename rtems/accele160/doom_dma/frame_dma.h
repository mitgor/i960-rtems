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

#if ACCELE_TERMINAL_TEST >= 6
#if ACCELE_TERMINAL_TEST >= 10 && ACCELE_TERMINAL_TEST <= 13
/* One-shot diagnostic CE resume, never generic fault recovery. Preserve the
 * timeout record, recheck its exact suspended state, then observe a new bound.
 * No descriptor reload, chain-resume bit, completion publication or release. */
static void at_dma_resume(void){unsigned i,ch,csr;
 if(at[208])return;
 at[208]=1u; /* Attempt latched even when the gate refuses. */
 #if ACCELE_TERMINAL_TEST == 11 || ACCELE_TERMINAL_TEST == 13
 /* The sole injected doorbell must have been observed, masked and cleared
  * by the owned NMI handler before any DMA restart. IISR is read-only here. */
 at[221]=REG(0x1324u);at[222]=REG(0x1320u);at[223]=REG(0x1328u);
 if(at[160]!=2u||at[20]!=0x7d004u||at[163]!=248u||at[155]!=1u||
    at[151]!=0x100u||!(at[152]&8u)||!(at[153]&0x80000000u)||
    (at[154]&8u)||at[221]!=(at[152]&~8u)||
    at[222]!=(at[153]&~0x80000000u)||at[223]!=(at[154]|8u))return;
#else
 if(at[160]!=1u||at[20]!=0x7d003u)return;
#endif
 if(!claimed||switch_fault||
    !at_guard()||!at_owned_valid()||at[175]!=10000000u||at[195]!=1u||
    at[203]!=4096u||at[186]!=0x400u||at[187]||at[191]!=7u||
    at[183]!=1024u||at[184]!=0x400u||!at[194]||
    at[192]!=at[204]||at[193]!=at[205])return;
 for(i=0;i<6u;i++)if(at[186+i]!=at[196+i])return;
 if(at[188]<at[180]||at[188]>=at[180]+32768u||
    (at[188]&31u)||at[189]!=at[188]+32u||!at[190]||at[190]>65536u)return;
 csr=REG(0x1404u);at[209]=csr;
 if(csr!=0x400u||REG(0x1400u)||REG(0x140cu)!=at[188]||
    REG(0x1410u)!=at[189]||REG(0x1420u)!=at[190]||REG(0x1424u)!=7u)return;
 at[208]=2u;DMA_SYNC();REG(0x1400u)=1u;DMA_SYNC();
 for(i=0;i<10000000u;i++){
  csr=REG(0x1404u);if(!(csr&0x400u)||(csr&0x2du))break;
 }
 at[210]=i;at[211]=csr;at[212]=REG(0x1400u);at[213]=REG(0x140cu);
 at[214]=REG(0x1410u);at[215]=REG(0x1420u);at[216]=REG(0x1424u);
 at[217]=byte_fnv((const void*)at[181],65536u);
 at[218]=byte_fnv((const void*)at[180],32800u);at[219]=1u;
 for(ch=1;ch<3u;ch++)for(i=0;i<8u;i++)
  if(REG(0x1400u+ch*64u+dma_offsets[i])!=dma_peers[ch-1u][i])at[219]=0u;
 at[220]=at_guard()&&at_owned_valid();
 if(at[210]<10000000u&&!at[211]&&at[212]==1u&&
    at[213]==at[180]+32768u&&!at[214]&&!at[215]&&at[216]==7u&&
    at[217]==at[204]&&at[218]==at[205]&&at[219]&&at[220])at[208]=3u;
}
#endif
/* Diagnostic only, after CPU containment. Observe a bounded number of polls;
 * Never publish firmware completion/release. Profiles 10/11 may CE-resume
 * its deliberately suspended chain after the recorded timeout. On timeout
 * the same terminal park retains source, descriptors and host destinations. */
static void at_dma_finish(void){unsigned i,ch,csr=0;
 for(i=0;i<10000000u;i++){
  csr=REG(0x1404u);
  if(!(csr&0x400u)||(csr&0x2du))break;
 }
 at[175]=i;at[186]=csr;at[187]=REG(0x1400u);at[188]=REG(0x140cu);
 at[189]=REG(0x1410u);at[190]=REG(0x1420u);at[191]=REG(0x1424u);
 if(at[183]==1024u && (at[184]&0x400u)){
  at[192]=byte_fnv((const void*)at[181],65536u);
  at[193]=byte_fnv((const void*)at[180],32800u);
  at[194]=1u;
  for(ch=1;ch<3u;ch++)for(i=0;i<8u;i++)
   if(REG(0x1400u+ch*64u+dma_offsets[i])!=dma_peers[ch-1u][i])at[194]=0u;
 }
#if ACCELE_TERMINAL_TEST == 12 || ACCELE_TERMINAL_TEST == 13
 /* Change only recorded evidence: expected fingerprint (12), NISR (13).
  * The actual NMI has already been acknowledged; never change live sources.
  * Restore the evidence, retry with the latch intact, then observe timeout. */
 {const unsigned field=ACCELE_TERMINAL_TEST==13?151u:204u;
  const unsigned mask=ACCELE_TERMINAL_TEST==13?0x100u:1u;
#if ACCELE_TERMINAL_TEST == 13
  at[239]=field;
#endif
  at[224]=at[field];at[field]^=mask;at[225]=at[field];DMA_SYNC();
  at_dma_resume();at[226]=at[208];
  at[field]=at[224];DMA_SYNC();at_dma_resume();at[227]=at[208];
 }
 for(i=0;i<10000000u;i++){
  csr=REG(0x1404u);if(!(csr&0x400u)||(csr&0x2du))break;
 }
 at[228]=i;at[229]=csr;at[230]=REG(0x1400u);at[231]=REG(0x140cu);
 at[232]=REG(0x1410u);at[233]=REG(0x1420u);at[234]=REG(0x1424u);
 at[235]=byte_fnv((const void*)at[181],65536u);
 at[236]=byte_fnv((const void*)at[180],32800u);at[237]=1u;
 for(ch=1;ch<3u;ch++)for(i=0;i<8u;i++)
  if(REG(0x1400u+ch*64u+dma_offsets[i])!=dma_peers[ch-1u][i])at[237]=0u;
 at[238]=at_guard()&&at_owned_valid();
#elif ACCELE_TERMINAL_TEST == 10 || ACCELE_TERMINAL_TEST == 11
 at_dma_resume();
#endif
}
/* Isolated diagnostic before engine admission. Finite 1024 x 64 KiB chain
 * repeats an immutable source into ONE existing guarded/pinned destination.
 * Descriptors occupy 32800 bytes of the existing 900000-byte image loan.
 * No circular descriptors, new PCI targets, source reuse, or host ACK. */
static void at_dma_test(void){
 unsigned i,j,csr=0;
 unsigned char *source=(unsigned char*)(((unsigned int)image_base+4095u)&~4095u);
 unsigned desc=(unsigned int)source+65536u;
 volatile unsigned int*d=(volatile unsigned int*)desc;
 if(!claimed||!image_base||!at_owned_valid())
  accele_terminal_enter(0x7d020u);
 dma_init();dma_peer_check();
 for(i=0;i<65536u;i++)source[i]=(unsigned char)(i^(i>>8)^0x69u);
 for(i=0;i<1025u;i++){
  for(j=0;j<8u;j++)d[i*8u+j]=0;
  d[i*8u]=(i==1024u)?0u:desc+(i+1u)*32u;
  d[i*8u+1u]=dma_bus[0]+(i==1024u?65536u:0u);
  d[i*8u+3u]=i==1024u?(unsigned int)dma_marker:(unsigned int)source;
  d[i*8u+4u]=i==1024u?32u:65536u;d[i*8u+5u]=7u;
 }
 for(i=0;i<8u;i++)dma_marker[i]=0x444d4100u+i;
 at[180]=desc;at[181]=(unsigned int)source;at[182]=dma_bus[0];
 at[183]=1024u;at[185]=(unsigned int)dma_marker;
#if ACCELE_TERMINAL_TEST >= 10 && ACCELE_TERMINAL_TEST <= 13
 at[204]=byte_fnv(source,65536u);at[205]=byte_fnv((const void*)desc,32800u);
#endif
#if ACCELE_TERMINAL_TEST == 7 || ACCELE_TERMINAL_TEST == 9 || ACCELE_TERMINAL_TEST == 11 || ACCELE_TERMINAL_TEST == 13
 if(REG(0x1700u)||(REG(0x1324u)&8u)||(REG(0x1320u)&0x80000000u))
  accele_terminal_enter(0x7d016u);
 REG(0x1328u)=at[154]&~8u;DMA_SYNC();
 if(REG(0x1328u)!=(at[154]&~8u))accele_terminal_enter(0x7d017u);
#endif
 DMA_SYNC();REG(0x1410u)=desc;REG(0x1400u)=1u;
 for(i=0;i<100000u;i++){csr=REG(0x1404u);if(csr&0x42du)break;}
 at[184]=csr;DMA_SYNC();
 if(!(csr&0x400u)||(csr&0x2du))accele_terminal_enter(0x7d021u);
#if ACCELE_TERMINAL_TEST >= 8
 /* 273353-001 19.14.1: CE=0 suspends, it does NOT abort or drain queues.
  * Only our DMA0 is changed. Keep all buffers/descriptors until reset. */
 REG(0x1400u)=0u;DMA_SYNC();
 {unsigned stable=0,old_d=~0u,old_n=~0u,old_b=~0u,d,n,b;
  for(i=0;i<100000u&&stable<4096u;i++){
   csr=REG(0x1404u);d=REG(0x140cu);n=REG(0x1410u);b=REG(0x1420u);
   if(d==old_d&&n==old_n&&b==old_b)stable++;else stable=0;
   old_d=d;old_n=n;old_b=b;
   if(!(csr&0x400u)||(csr&0x2du)||REG(0x1400u))break;
  }
  at[196]=csr;at[197]=REG(0x1400u);at[198]=old_d;at[199]=old_n;
  at[200]=old_b;at[201]=REG(0x1424u);at[202]=i;at[203]=stable;
  if(stable!=4096u||!old_b||!old_n||at[197]||!(csr&0x400u)||(csr&0x2du))
   accele_terminal_enter(0x7d022u);
  at[195]=1u;DMA_SYNC();
 }
#endif
#if ACCELE_TERMINAL_TEST == 6 || ACCELE_TERMINAL_TEST == 8 || ACCELE_TERMINAL_TEST == 10 || ACCELE_TERMINAL_TEST == 12
 accele_raise_fault();
#else
 at[155]=1u;DMA_SYNC(); /* Host may now issue the actual doorbell NMI. */
#endif
}
#endif

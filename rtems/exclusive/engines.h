/* Intel 272736-002 tables 20-3/4, 16-4, 16-28, 18-2/9.
 * Phase 0 observes. Phase 1 disables only already-inactive i960 DMA.
 * Phase 2 additionally denies bus mastering and external secondary grants.
 * No active-DMA abort, SCSI reset, cache-engine ownership or arbitrary MMIO. */
#define EREG(a) (*(volatile unsigned int*)(a))
#define ESHORT(a) (*(volatile unsigned short*)(a))
#define ENGINE_WORDS 16
static const unsigned int engine_dma[6]={0x1400,0x1404,0x1440,0x1444,0x1480,0x1484};
static unsigned int engine_before[ENGINE_WORDS],engine_during[ENGINE_WORDS],engine_after[ENGINE_WORDS];
static unsigned int engine_phase,engine_error,engine_written;
static void engine_snapshot(unsigned int*w){unsigned int i;
 for(i=0;i<6;i++)w[i]=EREG(engine_dma[i]);
 w[6]=ESHORT(0x1204);w[7]=ESHORT(0x1298);w[8]=ESHORT(0x103e);
 w[9]=EREG(0x104c);w[10]=EREG(0x1600);w[11]=EREG(0x1700);
 w[12]=EREG(0x1240);w[13]=EREG(0x1244);w[14]=EREG(0x1040);w[15]=EREG(0x1048);
}
static unsigned int engine_admit(const unsigned int*w,unsigned int phase){
 unsigned int i;
 if(phase>2)return 1;
 for(i=0;i<6;i++)if(w[i])return 2; /* include error/pending and resume flags */
 if(w[8]&0x40)return 3;
 if(phase==2&&!(w[9]&0x10000))return 4; /* no control of an external arbiter */
 return 0;
}
static unsigned int engine_acquire(unsigned int phase){unsigned int i;
 engine_phase=phase;engine_snapshot(engine_before);engine_error=engine_admit(engine_before,phase);
 if(engine_error)return engine_error;
 if(phase){for(i=0;i<6;i+=2){EREG(engine_dma[i])=0;(void)EREG(engine_dma[i]);}engine_written=1;}
 if(phase==2){
  EREG(0x104c)=engine_before[9]|0x3ffc;(void)EREG(0x104c);
  ESHORT(0x1298)=engine_before[7]&~4u;(void)ESHORT(0x1298);
  ESHORT(0x1204)=engine_before[6]&~4u;(void)ESHORT(0x1204);
 }
 engine_snapshot(engine_during);
 for(i=0;i<6;i++)if(engine_during[i])engine_error|=8;
 if(phase==2&&(engine_during[6]!=(engine_before[6]&~4u)||engine_during[7]!=(engine_before[7]&~4u)||engine_during[9]!=(engine_before[9]|0x3ffc)))engine_error|=16;
 return engine_error;
}
static void engine_release(void){
 if(engine_written&&engine_phase==2){
  ESHORT(0x1204)=engine_before[6];(void)ESHORT(0x1204);
  ESHORT(0x1298)=engine_before[7];(void)ESHORT(0x1298);
  EREG(0x104c)=engine_before[9];(void)EREG(0x104c);
 }
 engine_snapshot(engine_after);
 /* All controls admitted zero; no outstanding descriptor is resumed. */
}

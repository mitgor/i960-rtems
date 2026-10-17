/* AcceleRAID 160: callback-free, finite timer monitor using owned grant RAM.
 * This is bare ISR work; neither RTEMS nor DMA/SCSI transfer is admitted. */
extern unsigned char _bss_start[],_bss_end[],irq_owned_area[];
extern void timer_isr(void),timer_invalidate_dcache(void);
extern unsigned int escape_context[];
#define REG(a) (*(volatile unsigned int *)(a))
#define ENTER 0x52544e45u
#define HALT  0x544c4148u
#define ACTIVE 0x49544341u
#define HALTED 0x544c4148u
#define EXPIRED 0x45505845u
#define MAX_TICKS 300u
volatile unsigned int irq_active,irq_fault;
static volatile unsigned int ticks,entries,entered_ticks,irq_sp,frame,frame_pc,frame_ac,frame_vector;
static unsigned int saved_mask,saved_map,saved_vector,saved_reload,saved_count,saved_pc;
static volatile unsigned int armed,restoration,state;
static volatile unsigned int * const side=(volatile unsigned int *)0xc000fa40u;
static volatile unsigned int * const diag=(volatile unsigned int *)0xc000fa60u;
static void mask31(void){unsigned int level=31u<<16;
 __asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(level)::"g0","memory");
}
static void clear_tip1(void){unsigned int old=0;
 __asm__ volatile("lda 0xff008500,g0; lda 0x2000,g1; atmod g0,g1,%0"
                  :"+r"(old)::"g0","g1","memory");
}
static unsigned int preflight(void){
 if(REG(0xff008510u)!=0x6000u||REG(0xff008520u)!=0x4444u||
    REG(0xff008524u)!=0x6754u||REG(0xff008528u)!=0x80000u||
    REG(0xff008504u)!=0x10c7u||(REG(0xff008500u)&0x2000u))return 1u;
 if(REG(0xff000310u)||REG(0xff000314u)||REG(0x4u)!=0xaaaaaaaau||
    REG(0x20u)!=0xc0000418u||REG(0x3cu)!=0xe0000ff0u)return 2u;
 if(REG(0xff000318u))return 3u;
 if(REG(0xff000310u)||REG(0xff000314u)||
    (REG(0xff008500u)&0x2000u)||REG(0xff008504u)!=0x10c7u||
    REG(0xff008528u)!=0x80000u||REG(0x4u)!=0xaaaaaaaau)return 4u;
 return 0u;
}
static void stop_timer(void){
 if(!armed)return;
 mask31();REG(0xff008504u)=0;REG(0xff000318u)=0;clear_tip1();
 REG(0xff008528u)=saved_map;REG(0x4u)=saved_vector;
 REG(0xff000310u)=saved_reload;REG(0xff000314u)=saved_count;
 REG(0xff008504u)=saved_mask;armed=0;
 restoration=(REG(0xff008504u)==saved_mask&&
              REG(0xff008528u)==saved_map&&REG(0x4u)==saved_vector&&
              REG(0xff000310u)==saved_reload&&
              REG(0xff000314u)==saved_count&&
              !(REG(0xff008500u)&0x2000u)&&REG(0xff000318u)==0);
}
void timer_interrupt(unsigned int fp){unsigned int sp,cmd,pc,ac,vector;
 __asm__ volatile("mov sp,%0":"=r"(sp));irq_sp=sp;
 if(sp<(unsigned int)irq_owned_area+192u||
    sp>=(unsigned int)irq_owned_area+4096u)irq_fault|=1u;
 if((fp&15u)||fp<0xc0000100u||fp>=0xc0713000u){
  irq_fault|=2u;stop_timer();state=EXPIRED;side[4]=EXPIRED;return;
 }
 pc=REG(fp-16u);ac=REG(fp-12u);vector=REG(fp-8u);
 if(vector!=0x12u)irq_fault|=4u;
 ticks++;diag[4]=ticks;diag[5]=sp;
 timer_invalidate_dcache();
 cmd=side[3];
 if(!entries&&cmd==ENTER&&side[0]==0x3145534cu&&
    side[1]==0x161610d1u&&side[2]==1u){
  /* ENTER is sent only after op13 has returned. Its frame must belong to
   * stock firmware, rather than our previous owned entry stack. */
  if(fp<0xc0000100u||fp>=0xc0710000u){irq_fault|=8u;}
  else{
   side[3]=0u;entries=1u;entered_ticks=ticks;
   frame=fp;frame_pc=pc;frame_ac=ac;
   frame_vector=vector;state=ACTIVE;side[4]=ACTIVE;
  }
 }
 if(entries&&cmd==HALT&&side[0]==0x3145534cu&&
    side[1]==0x161610d1u&&side[2]==1u){
  stop_timer();state=HALTED;
 }else if(ticks>=MAX_TICKS||irq_fault){
  stop_timer();state=EXPIRED;
 }
 if(REG(fp-16u)!=pc||REG(fp-12u)!=ac||REG(fp-8u)!=vector)irq_fault|=16u;
 if(!armed){volatile unsigned int *trace=(volatile unsigned int*)(irq_owned_area+3072);
  trace[0]=0x31464f48u;trace[1]=ticks;trace[2]=entries;
  trace[3]=entered_ticks;trace[4]=frame;trace[5]=frame_pc;
  trace[6]=frame_ac;trace[7]=frame_vector;trace[8]=irq_sp;
  trace[9]=irq_fault;trace[10]=restoration;trace[11]=state;
  /* The interrupt record restores the interrupted firmware PC on ret.
   * Return it to its exact original priority after timer-1 is disabled. */
  REG(fp-16u)=(pc&~0x1f0000u)|(saved_pc&0x1f0000u);
  trace[12]=REG(fp-16u);trace[13]=saved_pc;trace[14]=pc;
  side[5]=frame;side[6]=irq_fault;side[7]=restoration;
  side[4]=state;
 }
 diag[6]=entries;diag[7]=restoration;
}
unsigned int bounded_main(unsigned int report_addr,unsigned int nonce){
 volatile unsigned int *report=(volatile unsigned int*)report_addr;
 unsigned char *p;unsigned int error;
 if(report_addr!=0xc000fa20u||nonce!=0x161610d1u)return 0xbad00001u;
 for(p=_bss_start;p<_bss_end;p++)*p=0;
 if(side[0]!=0x3145534cu||side[1]!=nonce||side[2]!=1u||
    side[3]!=0u)return 0xbad00002u;
 error=preflight();diag[1]=error;if(error)return 0xbad10000u|error;
 saved_pc=escape_context[2];
 diag[6]=saved_pc;
 saved_mask=REG(0xff008504u);saved_map=REG(0xff008528u);
 saved_vector=REG(0x4u);saved_reload=REG(0xff000310u);
 saved_count=REG(0xff000314u);
 mask31();REG(0xff008504u)=0u;REG(0x4u)=(unsigned int)timer_isr;
 REG(0xff008528u)=0x00180000u;
 /* 100 MHz / 8 / 125000 -> 10 ms period, maximum 1.28 s. */
 REG(0xff000310u)=125000u;REG(0xff000314u)=125000u;
 REG(0xff008504u)=0x2000u;armed=1u;REG(0xff000318u)=0x36u;
 side[4]=0x59444152u; /* READY: arm finished; op13 still returning. */
 report[0]=0x314e5552u;report[1]=nonce;report[2]=0x31454e4fu;
 report[6]=0x4d524141u; /* AARM: accepted asynchronous arm. */
 return 0;
}

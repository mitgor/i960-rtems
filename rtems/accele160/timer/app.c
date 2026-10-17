/* Strictly bounded timer-1/vector-18 experiment on the 80303 new card.
 * All hardware writes are preceded by exact stock-state guards. */
extern unsigned char _bss_start[],_bss_end[],irq_owned_area[];
extern void timer_isr(void),timer_invalidate_dcache(void);
#define REG(a) (*(volatile unsigned int *)(a))
volatile unsigned int irq_active,irq_fault;
static volatile unsigned int ticks,irq_sp;
static unsigned int saved_mask,saved_map,saved_vector,saved_reload,saved_count;
static volatile unsigned int * const side=(volatile unsigned int *)0xc000fa40u;
static volatile unsigned int * const diag=(volatile unsigned int *)0xc000fa60u;

static void mask31(void){unsigned int old;
 __asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"=r"(old)::"g0","memory");
}
static void priority0(void){unsigned int old;
 __asm__ volatile("mov 0,g0; modpc 0,g0,%0":"=r"(old)::"g0","memory");
}
static void clear_tip1(void){unsigned int old=0;
 __asm__ volatile("lda 0xff008500,g0; lda 0x2000,g1; atmod g0,g1,%0"
                  :"+r"(old)::"g0","g1","memory");
}
void timer_interrupt(void){unsigned int sp;
 __asm__ volatile("mov sp,%0":"=r"(sp));
 irq_sp=sp;
 if(sp<(unsigned int)irq_owned_area+192u ||
    sp>=(unsigned int)irq_owned_area+4096u)irq_fault=2u;
 ++ticks;
 REG(0xc000fa70u)=ticks;
 REG(0xc000fa74u)=sp;
}

static unsigned int preflight(void){
 if(REG(0xff008510u)!=0x6000u ||
    REG(0xff008520u)!=0x4444u || REG(0xff008524u)!=0x6754u ||
    REG(0xff008528u)!=0x00080000u ||
    REG(0xff008504u)!=0x000010c7u || REG(0xff008500u)!=0u)
  return 1u;
 if(REG(0xff000310u)!=0u || REG(0xff000314u)!=0u ||
    REG(0x00000004u)!=0xaaaaaaaau ||
    REG(0x00000020u)!=0xc0000418u ||
    REG(0x0000003cu)!=0xe0000ff0u)return 2u;
 /* Mode read clears terminal-count status; every idle guard precedes it. */
 if(REG(0xff000318u)!=0u)return 3u;
 if(REG(0xff000310u)!=0u || REG(0xff000314u)!=0u ||
    REG(0xff008500u)!=0u || REG(0xff008504u)!=0x10c7u ||
    REG(0xff008528u)!=0x80000u || REG(0x4u)!=0xaaaaaaaau)
  return 4u;
 return 0u;
}
static void stop_timer(void){
 mask31();
 REG(0xff008504u)=0u;
 REG(0xff000318u)=0u;
 clear_tip1();
 REG(0xff008528u)=saved_map;
 REG(0x00000004u)=saved_vector;
 REG(0xff000310u)=saved_reload;
 REG(0xff000314u)=saved_count;
 REG(0xff008504u)=saved_mask;
}
static unsigned int restored(void){
 return REG(0xff008504u)==saved_mask &&
        REG(0xff008528u)==saved_map &&
        REG(0x00000004u)==saved_vector &&
        REG(0xff000310u)==saved_reload &&
        REG(0xff000314u)==saved_count &&
        !(REG(0xff008500u)&0x2000u) &&
        REG(0xff000318u)==0u && irq_active==0u && irq_fault==0u;
}

unsigned int bounded_main(unsigned int report_addr,unsigned int nonce){
 volatile unsigned int *report=(volatile unsigned int *)report_addr;
 unsigned char *p;
 unsigned int epoch,goal,budget,stopped=0,reason,success;
 if(report_addr!=0xc000fa20u||nonce!=0x161610d1u)return 0xbad00001u;
 for(p=_bss_start;p<_bss_end;p++)*p=0;
 if(side[0]!=0x3145534cu || side[1]!=nonce || side[3]!=0u ||
    (side[2]!=1u&&side[2]!=2u))return 0xbad00002u;
 epoch=side[2];
 reason=preflight();
 diag[1]=reason;
 if(reason)return 0xbad10000u|reason;
 saved_mask=REG(0xff008504u);
 saved_map=REG(0xff008528u);
 saved_vector=REG(0x00000004u);
 saved_reload=REG(0xff000310u);
 saved_count=REG(0xff000314u);
 goal=epoch==1u?1000u:8u;
 mask31();
 REG(0xff008504u)=0u;
 REG(0x00000004u)=(unsigned int)timer_isr;
 REG(0xff008528u)=0x00180000u;
 REG(0xff000310u)=10000u;
 REG(0xff000314u)=10000u;
 REG(0xff008504u)=0x2000u;
 REG(0xff000318u)=0x36u;
 side[4]=0x59444152u; /* READY after arm */
 priority0();
 for(budget=0;budget<2000000u && ticks<goal;budget++){
  timer_invalidate_dcache();
  if(side[3]==0x504f5453u){
   if(side[0]!=0x3145534cu||side[1]!=nonce||side[2]!=epoch){
    reason=5u;break;
   }
   stopped=1u;break;
  }
  if(irq_fault){reason=6u;break;}
 }
 stop_timer();
 success=restored();
 diag[4]=ticks;
 diag[5]=irq_sp;
 diag[6]=success;
 diag[7]=reason;
 if(!success)return 0xbad20000u|irq_fault;
 if(reason)return 0xbad30000u|reason;
 if(stopped){
  side[5]=0x214b4341u;side[6]=nonce;side[7]=epoch;
 }else if(ticks>=goal){side[4]=0x4b434954u; /* TICK */
 }else return 0xbad40000u;
 report[0]=0x314e5552u;
 report[1]=nonce;
 report[2]=0x31454e4fu;
 report[6]=stopped?0x504f5453u:0x4b434954u;
 return 0u;
}

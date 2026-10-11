#ifdef I960_EXTRA_RAM
#include <string.h>
#define R(a) (*(volatile unsigned int*)(a))
extern unsigned int exclusive_fault_valid(void),scsi_target_verified(void);
extern void exclusive_engine_report(unsigned int*);
#ifdef I960_QUEUE_RECLAIM
extern unsigned int resident_fallback_prepare(void),resident_fallback_valid(void);
#endif
extern unsigned int resident_queue_extend(unsigned int),resident_queue_external_valid(void);
static unsigned int boundary_low[16],boundary_high[16],firmware_hash,code_hash,extra_ready;
static unsigned int hash(unsigned int lo,unsigned int bytes){unsigned int h=2166136261u,i;for(i=0;i<bytes;i+=4)h=(h^R(lo+i))*16777619u;return h;}
static unsigned int boundary(void){unsigned int i;
 for(i=0;i<16;i++)if(R(0xc01fffc0u+i*4)!=boundary_low[i]||R(0xc0240000u+i*4)!=boundary_high[i])return 0;
 return hash(0xc0000000u,0x140000)==firmware_hash&&hash(0xc0f2c000u,0x20000)==code_hash;
}
#define RP_WRITE(a,v) (R(a)=(v))
#define RP_READ(a) R(a)
#define RP_SYNC() do{unsigned int x;__asm__ volatile("dcctl 2,0,%0":"=r"(x)::"memory");}while(0)
#define RP_BOUNDARY() boundary()
#include "ram_probe.h"
struct ram_probe_report extra_report;
static unsigned int saved_cache;
unsigned int exclusive_extra_guard_mask(void){unsigned int i,bad=0;
 for(i=0;i<16;i++){
  if(R(RAM_PROBE_LO+4*i)!=0xa55a1234u)bad|=1;
  if(R(RAM_PROBE_LO+4*(RAM_PROBE_WORDS-16+i))!=0x5aa54321u)bad|=2;
  if(R(RAM_PROBE_LO+64+192000+4*i)!=0xc3c39696u)bad|=4;
 }return bad;
}
static unsigned int guards(void){return !exclusive_extra_guard_mask();}
#ifdef I960_GENERAL_HEAP
extern unsigned int resident_heap_init(void);
#endif
unsigned int exclusive_extra_valid(void){return extra_ready&&resident_queue_external_valid()
#ifdef I960_QUEUE_RECLAIM
 &&resident_fallback_valid()
#endif
&&extra_report.passes==4&&!extra_report.error&&guards()&&exclusive_fault_valid()&&scsi_target_verified();}
unsigned int exclusive_extra_prepare(void){unsigned int i,scratch,s[17],rc;
 if(extra_ready||!exclusive_fault_valid()||!scsi_target_verified()){extra_report.error=0x10001;return 1;}
 exclusive_engine_report(s);for(i=0;i<6;i++)if(s[i]){extra_report.error=0x10002;return 2;}
 /* Pinned ROM interrupt table has no pending software interrupts. No code
  * in the resident profile posts software interrupts or system calls. */
 if(R(0xfeffd4e0u)!=0xfeffd0c0u){extra_report.error=0x10003;return 3;}
 for(i=0;i<9;i++)if(R(0xfeffd0c0u+i*4)){extra_report.error=0x10004;return 4;}
 __asm__ volatile("flushreg":::"memory");
 __asm__ volatile("dcctl 4,0,%0":"=r"(saved_cache)::"memory");
 __asm__ volatile("dcctl 0,0,%0":"=r"(scratch)::"memory");
 for(i=0;i<16;i++){boundary_low[i]=R(0xc01fffc0u+i*4);boundary_high[i]=R(0xc0240000u+i*4);}
 firmware_hash=hash(0xc0000000u,0x140000);code_hash=hash(0xc0f2c000u,0x20000);
 rc=ram_probe_run(&extra_report,1);
 if(!rc){
  for(i=0;i<16;i++){R(RAM_PROBE_LO+64+192000+4*i)=0xc3c39696u;R(RAM_PROBE_LO+4*i)=0xa55a1234u;R(RAM_PROBE_LO+4*(RAM_PROBE_WORDS-16+i))=0x5aa54321u;}
  if(!boundary()||!guards()||!exclusive_fault_valid()||!scsi_target_verified())rc=5;
 }
 RP_SYNC();if(saved_cache&1)__asm__ volatile("dcctl 1,0,%0":"=r"(scratch)::"memory");
 if(rc){extra_report.error|=rc<<16;return rc;}
 /* The queue is always fixed; the separately opted-in heap uses its guarded tail. */
 if(resident_queue_extend(RAM_PROBE_LO+64)){extra_report.error=6;return 6;}
#ifdef I960_QUEUE_RECLAIM
 if(resident_fallback_prepare()){extra_report.error=9;return 9;}
#endif
 extra_ready=1;if(!exclusive_extra_valid())return 7;
#ifdef I960_GENERAL_HEAP
 if(resident_heap_init())return 8;
#endif
 return 0;
}
void exclusive_extra_report(unsigned int*w){unsigned int i,*p=(unsigned int*)&extra_report;
 for(i=0;i<6;i++)w[i]=p[i];w[6]=extra_ready;w[7]=saved_cache;
}
#endif

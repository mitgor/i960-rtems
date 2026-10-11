#ifdef I960_FAULT_OWNER
#include <string.h>
#define V(a) (*(volatile unsigned int*)(a))
#define FO_READ(a) V(a)
#define FO_WRITE(a,v) (V(a)=(v))
#include "fault_owner.h"
extern void exclusive_fault_entry(void),exclusive_nmi_entry(void);
extern void exclusive_raise_fault(void),exclusive_synthetic_nmi(void);
extern unsigned int scsi_target_verified(void);
extern void exclusive_engine_report(unsigned int*);
unsigned char exclusive_exception_area[4096] __attribute__((aligned(16)));
volatile unsigned int exclusive_trap_active,exclusive_trap_words[64];
static unsigned int owner_epoch,owner_ready,old_nmi,old_stack,old_hash;
static unsigned int vector_read(void){unsigned int v;__asm__ volatile("ld 0,%0":"=r"(v)::"memory");return v;}
static void vector_write(unsigned int v){__asm__ volatile("st %0,0"::"r"(v):"memory");}
static unsigned int guard_valid(void){unsigned int i;for(i=0;i<64;i++)if(exclusive_exception_area[i]!=0xa5||exclusive_exception_area[4032+i]!=0xa5)return 0;return 1;}
unsigned int exclusive_fault_valid(void){
 return owner_ready&&vector_read()==(unsigned int)exclusive_nmi_entry&&V(0xff008704)==(unsigned int)exclusive_exception_area+64&&fault_table_valid((unsigned int)exclusive_fault_entry)&&guard_valid();
}
unsigned int exclusive_fault_install(unsigned int epoch){unsigned int i,s[17];
 exclusive_engine_report(s);for(i=0;i<6;i++)if(s[i])return 1;
 if(s[6]!=2||(s[7]&4)||s[8]&0x40||s[11])return 1;
 if(owner_ready||V(0xff008700)!=0xfeffd4d0u||V(0xfeffd4d0)!=FAULT_TABLE)return 1;
 old_nmi=vector_read();old_stack=V(0xff008704);if(old_nmi!=0xc004e190u)return 2;
 for(i=0;i<64;i++)old_hash=(old_hash<<1)^V(FAULT_TABLE+i*4);
 memset(exclusive_exception_area,0xa5,sizeof(exclusive_exception_area));owner_epoch=epoch;
 vector_write((unsigned int)exclusive_nmi_entry);
 V(0xff008704)=(unsigned int)exclusive_exception_area+64;
 if(fault_table_install((unsigned int)exclusive_fault_entry))return 3;
 owner_ready=1;return exclusive_fault_valid()?0:4;
}
/* Called only after irrevocable takeover. A real fault never resumes RTEMS. */
void exclusive_fault_inject(void){
#if I960_FAULT_TEST == 1
 exclusive_raise_fault();
#elif I960_FAULT_TEST == 2
 exclusive_synthetic_nmi();
#elif I960_FAULT_TEST == 3
 if(exclusive_fault_valid()&&scsi_target_verified())V(0x1328)=0x1f3;
#endif
}
#ifdef I960_EXTRA_RAM
extern void exclusive_extra_report(unsigned int*);
#endif
#ifdef I960_GENERAL_HEAP
extern void resident_heap_report(unsigned int*);
#endif
#ifdef I960_OWNED_MIB
#include "large_ram.h"
static unsigned int terminal_ram[64],terminal_ram_selected;
#endif
void exclusive_trap_park(void){unsigned int token,index,i,s[17];
 exclusive_trap_words[37]=V(0x1320);exclusive_trap_words[38]=V(0x1328);exclusive_trap_words[39]=V(0x1324);
 V(0x1328)=0x1fb; /* mask the test source before clearing its latch */
 if(exclusive_trap_words[2]==2)V(0x1320)=0x80000000u;
 exclusive_trap_words[0]=0x31464d4e; /* NMF1, terminal snapshot, not EXR1 */
 exclusive_trap_words[1]=owner_epoch;
 exclusive_trap_words[8]=V(0x1700);exclusive_trap_words[9]=vector_read();
 exclusive_trap_words[10]=V(0xff008704);exclusive_trap_words[11]=(unsigned int)exclusive_fault_entry;
 exclusive_trap_words[12]=(unsigned int)exclusive_nmi_entry;exclusive_trap_words[13]=old_nmi;
 exclusive_trap_words[14]=old_stack;exclusive_trap_words[15]=old_hash;
 exclusive_trap_words[16]=exclusive_fault_valid();exclusive_trap_words[17]=scsi_target_verified();
 exclusive_engine_report(s);for(i=0;i<17;i++)exclusive_trap_words[20+i]=s[i];
 exclusive_trap_words[18]=guard_valid();exclusive_trap_words[19]=V(0xff008504);
#ifdef I960_EXTRA_RAM
 exclusive_extra_report((unsigned int*)(exclusive_trap_words+40));
#endif
#ifdef I960_GENERAL_HEAP
 resident_heap_report((unsigned int*)(exclusive_trap_words+48));
#endif
 for(;;){token=V(0x1314);if((token&65535)!=owner_epoch)continue;
#ifdef I960_OWNED_MIB
  if(token==(0x98000000u|owner_epoch)){exclusive_large_report(terminal_ram);terminal_ram_selected=1;V(0x1314)=0;V(0x131c)=0x99000000u|owner_epoch;(void)V(0x131c);V(0x1324)=2;continue;}
  if(token==(0x90000000u|owner_epoch))terminal_ram_selected=0;
#endif
  if(token==(0x90000000u|owner_epoch)){V(0x1314)=0;V(0x131c)=0x95000000u|owner_epoch;}
  else if((token&0xff000000u)==0x91000000u){index=(token>>16)&255;if(index>=64)continue;V(0x1318)=
#ifdef I960_OWNED_MIB
 terminal_ram_selected?terminal_ram[index]:
#endif
 exclusive_trap_words[index];V(0x1314)=0;V(0x131c)=0x92000000u|(index<<16)|owner_epoch;}
  else if(token==(0x93000000u|owner_epoch)){V(0x1314)=0;V(0x131c)=0x94000000u|owner_epoch;}
  else continue;
  (void)V(0x131c);V(0x1324)=2;(void)V(0x1324);
 }
}
#endif

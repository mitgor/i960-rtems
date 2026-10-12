/* Exclusive, reboot-only admission. Unused RAM remains pattern-filled and is
 * sampled throughout execution; it is not yet a general application allocator. */
#ifdef I960_OWNED_MIB
#include "large_ram.h"
#include "board.h"
#ifdef I960_RESIDENT_UPLOAD
#include "upload.h"
#define RESERVE_START UPLOAD_RESERVE
#else
#define RESERVE_START LARGE_RESERVE
#endif
#define R(a) (*(volatile unsigned int*)(a))
extern unsigned int exclusive_fault_valid(void),scsi_target_verified(void);
extern void exclusive_engine_report(unsigned int*);
extern unsigned int irq_owned_entry_fp;
static unsigned int ready,passes,checked,error,failed_address,low_hash,high_hash,samples,final_checked;
static unsigned int hash(unsigned int lo,unsigned int hi){unsigned int h=2166136261u;for(;lo<hi;lo+=4)h=(h^R(lo))*16777619u;return h;}
static unsigned int pattern(unsigned int a,unsigned int p){unsigned int v=a*0x9e3779b9u;return p==0?a^0xa5a5a5a5u:p==1?a^0x5a5a5a5au:p==2?v:~v;}
static unsigned int guards(void){unsigned int i;for(i=0;i<16;i++)if(R(LARGE_LO+4*i)!=0x314d4152u||R(LARGE_HI-64+4*i)!=0x324d4152u||R(LARGE_LO+0x40040+4*i)!=0x334d4152u)return 0;return 1;}
unsigned int exclusive_large_valid(void){unsigned int a;
 if(!ready||error||!guards())return 0;
#ifdef I960_RESIDENT_UPLOAD
 if(!upload_guards())return 0;
#endif
 for(a=RESERVE_START;a<LARGE_HI-64;a+=65536)if(R(a)!=pattern(a,3)){error=6;failed_address=a;return 0;}
 samples++;return 1;
}
unsigned int exclusive_large_prepare(void){unsigned int w[17],a,p,v,cache,scratch;
 w[0]=(*(volatile unsigned char*)0xe0400000)&31;w[1]=R(0xc011e22c);
 if(w[1]!=0xc0110780u)return error=1;
 w[2]=R(w[1]+0xc0);w[3]=R(w[1]+0x168);w[4]=R(0xc00a8718);w[5]=R(0xc0112a70);w[6]=R(w[1]+8);
 if(ready||resident_board_admit(w)||!exclusive_fault_valid()||!scsi_target_verified())return error=1;
 exclusive_engine_report(w);for(a=0;a<6;a++)if(w[a])return error=2;
 /* Keep the parked original firmware frame and a generous surrounding reserve. */
 if(irq_owned_entry_fp>=LARGE_LO-65536&&irq_owned_entry_fp<LARGE_HI+65536)return error=3;
 if(R(0xfeffd4e0u)!=0xfeffd0c0u)return error=3;
 for(a=0;a<9;a++)if(R(0xfeffd0c0u+4*a))return error=3;
 __asm__ volatile("flushreg":::"memory");
 __asm__ volatile("dcctl 4,0,%0":"=r"(cache)::"memory");
 __asm__ volatile("dcctl 0,0,%0":"=r"(scratch)::"memory");
 #ifdef I960_RESIDENT_UPLOAD
 upload_protect_init();if(!upload_protect_all()){error=8;goto end;}
#endif
 low_hash=hash(0xc0000000u,LARGE_LO);high_hash=hash(LARGE_HI,0xc0f4c000u);
 for(p=0;p<4;p++){
  for(a=LARGE_LO;a<LARGE_HI;a+=4)R(a)=pattern(a,p);
  __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
  for(a=LARGE_LO;a<LARGE_HI;a+=4){v=R(a);checked++;if(v!=pattern(a,p)){failed_address=a;error=4;goto end;}}
  if(hash(0xc0000000u,LARGE_LO)!=low_hash||hash(LARGE_HI,0xc0f4c000u)!=high_hash){error=5;goto end;}
#ifdef I960_RESIDENT_UPLOAD
  if(!upload_protect_all()){error=8;goto end;}
#endif
  passes++;
 }
 for(a=0;a<16;a++){R(LARGE_LO+4*a)=0x314d4152u;R(LARGE_HI-64+4*a)=0x324d4152u;R(LARGE_LO+0x40040+4*a)=0x334d4152u;}
#ifdef I960_RESIDENT_UPLOAD
 if(!upload_init()){error=9;goto end;}
#endif
 ready=1;
end:
 __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
 if(cache&1)__asm__ volatile("dcctl 1,0,%0":"=r"(scratch)::"memory");
 return error;
}
unsigned int exclusive_large_finish(void){unsigned int a,count=0;
 extern void exclusive_drain_poll(void);
 final_checked=0;
 if(!exclusive_large_valid())return 0;
#ifdef I960_RESIDENT_UPLOAD
 if(!upload_finish()){error=10;return 0;}
#endif
 for(a=RESERVE_START;a<LARGE_HI-64;a+=4){
  if(!(count&1023))exclusive_drain_poll();
  if(R(a)!=pattern(a,3)){error=7;failed_address=a;return 0;}count++;
 }
 /* Publish only the complete scan; pages taken during the scan still show zero. */
 final_checked=count;return 1;
}
void exclusive_large_report(unsigned int*w){unsigned int i;for(i=0;i<64;i++)w[i]=0;
 w[0]=0x314d4152;w[1]=LARGE_LO;w[2]=LARGE_BYTES;w[3]=ready;w[4]=passes;w[5]=checked;w[6]=error;w[7]=failed_address;
 w[8]=LARGE_WORKSPACE;w[9]=262144;w[10]=LARGE_STACKS;w[11]=65536;w[12]=4;w[13]=RESERVE_START;w[14]=LARGE_HI-64-RESERVE_START;w[15]=samples;w[16]=exclusive_large_valid();w[17]=irq_owned_entry_fp;w[18]=final_checked;w[26]=2;
#ifdef I960_RESIDENT_UPLOAD
 w[26]=3;w[31]=UPLOAD_BASE;w[32]=UPLOAD_BYTES;w[33]=upload_guards();upload_protect_report(w+34);
#endif
 {extern void exclusive_stack_report(unsigned int*);exclusive_stack_report(w+19);}
}
#endif

#ifdef I960_RESIDENT_UPLOAD
#include "upload.h"
extern unsigned char upload_code_start[],upload_code_end[];
extern void exclusive_drain_poll(void);
#define R(a) (*(volatile unsigned int*)(a))
#define PAGES 144u
static unsigned int addresses[PAGES],lengths[PAGES],hashes[PAGES],count,next,checks,error,bad;
static unsigned int hash(unsigned int a,unsigned int n){unsigned int h=2166136261u;for(;n;n-=4,a+=4)h=(h^R(a))*16777619u;return h;}
static void range(unsigned int lo,unsigned int hi){unsigned int n;while(lo<hi){n=hi-lo;if(n>4096)n=4096;
 if(count==PAGES){error=1;return;}addresses[count]=lo;lengths[count]=n;hashes[count]=hash(lo,n);count++;lo+=n;}}
void upload_protect_init(void){
 if(count){error=1;return;}
 range(0xc0f2c000u,0xc0f4c000u);
 range((unsigned int)upload_code_start,(unsigned int)upload_code_end);
 /* BIO response, upper guard, saved staging tail, stock cache data/descriptors,
  * top-of-DRAM warm marker: frozen after ARM returns and engines are held. */
 range(0xc0f9bff0u,0xc1000000u);
}
unsigned int upload_protect_step(void){unsigned int i=next;
 if(error||!count)return 0;
 if(hash(addresses[i],lengths[i])!=hashes[i]){error=2;bad=addresses[i];return 0;}
 checks++;if(++next==count)next=0;return 1;
}
unsigned int upload_protect_all(void){unsigned int i;for(i=0;i<count;i++)if(!upload_protect_step())return 0;return count&&!error;}
unsigned int upload_protect_finish(void){unsigned int i;for(i=0;i<count;i++){exclusive_drain_poll();if(!upload_protect_step())return 0;}return count&&!error;}
void upload_protect_report(unsigned int*w){w[0]=count;w[1]=checks;w[2]=error;w[3]=bad;w[4]=(unsigned int)upload_code_start;w[5]=(unsigned int)upload_code_end;}
#endif

/* Native model of the exact host handshake. No hardware is accessed. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <stdbool.h>
typedef uint32_t u32;
#define ODB 0x2c
struct experiment {u32 *bar;unsigned int stop_epoch,stop_delay_ms,pending,sequence;};
static u32 regs[64];static int phase,pauses,fail,maskbad,premature,writes;
static u32 readl(u32*p){unsigned int off=(char*)p-(char*)regs;
 assert(off==ODB||off==0x28||off==0x34||off==0x1c||off==0x14);
 if(off==ODB)return premature;
 if(off==0x28&&maskbad)return 0;
 return regs[off/4];
}
static void writel(u32 v,u32*p){unsigned int off=(char*)p-(char*)regs;
 assert(off==0x14);writes++;regs[off/4]=v;
 if(v==0x72001234){assert(phase==1);phase=2;}
 else {assert(v==0x74001234&&phase==3);phase=4;}
}
static void usleep_range(int a,int b){(void)a;(void)b;pauses++;
 if(fail)return;
 if(!phase){regs[0x1c/4]=0x71001234;phase=1;}
 if(phase==2){regs[0x1c/4]=0x73001234;phase=3;}
}
static void msleep(unsigned int n){assert(n>=120&&n<=200);}
#define record(...) ((void)0)
/* Driver BAR is byte-addressed. Use a matching view for these shared helpers. */
#define experiment byte_experiment
struct byte_experiment {void *bar;unsigned int stop_epoch,stop_delay_ms,pending,sequence;};
#include "stop_host.h"
#undef experiment
static void reset(void){memset(regs,0,sizeof(regs));regs[0x28/4]=0x1fb;regs[0x34/4]=0xff;phase=pauses=fail=maskbad=premature=writes=0;}
int main(void){struct byte_experiment d={regs,0x1234,120,1,1};
 reset();assert(stop_exchange(&d)==0&&phase==4&&writes==2);
 reset();fail=1;assert(stop_exchange(&d)==-ETIMEDOUT&&writes==0&&pauses==800);
 reset();maskbad=1;assert(stop_exchange(&d)==-EIO&&writes==0);
 reset();premature=1;assert(stop_exchange(&d)==-EPROTO&&writes==0);
 reset();phase=1;regs[0x1c/4]=0x71001234;fail=1;
 assert(stop_exchange(&d)==-ETIMEDOUT&&writes==1); /* no release without drained */
 reset();regs[0x1c/4]=0x71001235;fail=1;
 assert(stop_exchange(&d)==-ETIMEDOUT&&writes==0); /* stale nonce */
 puts("STOP1 host: normal handshake, mask drift, stale nonce, premature completion and both timeout paths passed");
}

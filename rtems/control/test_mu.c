#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static unsigned int regs[16],writes,pauses,mode;
static unsigned int rd(unsigned int off){assert(off<64 && !(off&3));return regs[off/4];}
static void wr(unsigned int off,unsigned int value){
 assert(off==0x14||off==0x1c||off==0x24||off==0x30);writes++;
 if(off==0x30){assert(value==2);return;} /* local OISR writes ignored */
 else if(off==0x24){assert(value==2);regs[off/4]&=~value;}
 else{regs[off/4]=value;regs[(off==0x14?0x24:0x30)/4]|=2;}
}
#define MU_READ(off) rd(off)
#define MU_WRITE(off,v) wr(off,v)
#include "mu_echo.h"
static void pause_step(void){pauses++;if(mode==1)mu_poll();if(mode==2)regs[0x28/4]^=4;}
#define MU_PAUSE() pause_step()
#include "mu_host.h"
static void host_wr(unsigned int off,unsigned int v){if(off==0x30){assert(v==2);regs[off/4]&=~v;writes++;}else wr(off,v);}
#undef MU_WRITE
#define MU_WRITE(off,v) host_wr(off,v)
#include "mu_cleanup.h"
static void reset(void){memset(regs,0,sizeof(regs));regs[0x28/4]=0x1fb;regs[0x34/4]=0xff;mu_owned=mu_enabled=mu_age=mu_count=0;writes=pauses=0;mode=1;}
int main(void){unsigned int w[8],i;
 reset();assert(mu_start()==0);memset(w,0,sizeof(w));w[0]=0xc71e1234;
 assert(mu_exchange(w)==0&&w[1]==(w[0]^0x5a5a5a5a));assert(mu_count==1);
 regs[0x24/4]|=0x40;regs[0x30/4]|=1;assert(mu_finish()==0);
 assert(regs[0x30/4]==3);assert(mu_cleanup(1,1)==0); /* exact host PCI cleanup */
 assert(regs[0x24/4]==0x40&&regs[0x30/4]==1&&!regs[0x14/4]&&!regs[0x1c/4]);
 assert(mu_finish()==0); /* idempotent */
 reset();regs[0x14/4]=1;assert(mu_start()!=0&&writes==0);assert(mu_exchange(w)==-EBUSY&&writes==0);
 reset();regs[0x30/4]=2;assert(mu_start()!=0&&writes==0);
 reset();regs[0x24/4]=2;assert(mu_start()!=0&&writes==0);
 reset();regs[0x34/4]&=~2u;assert(mu_start()!=0&&writes==0);
 reset();assert(mu_start()==0);mode=0;assert(mu_exchange(w)==-ETIMEDOUT&&pauses==200);assert(mu_finish()==0);
 reset();assert(mu_start()==0);mode=2;assert(mu_exchange(w)==-EIO);i=writes;assert(mu_finish()!=0&&writes==i&&mu_owned);
 reset();assert(mu_start()==0);for(i=0;i<201;i++)mu_poll();assert(!mu_enabled&&writes==0);wr(0x14,0xc71e9999);mu_poll();assert(regs[0x1c/4]==0);assert(mu_finish()==0);
 reset();w[0]=1;assert(mu_exchange(w)==-EINVAL&&writes==0);
 reset();regs[0x30/4]=2;assert(mu_cleanup(0,0)==0&&writes==0&&regs[0x30/4]==2);assert(mu_cleanup(0,1)==-ENODATA&&writes==0);
 reset();regs[0x14/4]=1;assert(mu_cleanup(1,1)==-ENODATA&&writes==0);
 puts("MU exact host/target loops: echo, refusal, timeout, masks, W1C isolation, watchdog, restoration passed");return 0;
}

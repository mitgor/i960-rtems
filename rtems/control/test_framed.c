#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static unsigned int regs[16],progress,halted,quiesce_after,mode,pauses;
static unsigned int rd(unsigned int o){return regs[o/4];}
static void wr(unsigned int o,unsigned int v){
 if(o==0x24)regs[o/4]&=~v;
 else if(o==0x30){} /* read-only on local side */
 else{assert(o==0x14||o==0x1c);regs[o/4]=v;regs[(o==0x14?0x24:0x30)/4]|=2;}
}
#define MU_READ(o) rd(o)
#define MU_WRITE(o,v) wr(o,v)
#define MU_EPOCH 0x12345678u
#define MU_PROGRESS progress
#define MU_HALT() (halted=1)
#include "mu_framed.h"
static void pause_step(void){pauses++;if(mode==1&&!halted){mu_poll();if(!mu_runtime_stopped)progress++;}if(mode==2)regs[0x28/4]^=4;}
#define MU_PAUSE() pause_step()
#include "mu_framed_host.h"
static unsigned int generation;
static void frame(unsigned int*w,unsigned int seq,unsigned int op){
 memset(w,0,36*sizeof(*w));w[0]=seq;w[1]=CTL_MAGIC;w[2]=1;w[3]=MU_EPOCH;w[4]=op;w[5]=0xdeadbeef;w[6]=ctl_checksum(w,6);w[32]=++generation;
}
static void reset(void){memset(regs,0,sizeof(regs));regs[0x28/4]=0x1fb;regs[0x34/4]=0xff;mu_owned=0;generation=halted=progress=pauses=0;mode=1;assert(!mu_start());}
int main(void){unsigned int w[36],saved[16],i,r;
 reset();frame(w,1,CTL_PING);assert(!mu_exchange(w));assert(w[20]==0&&w[21]==0xdeadbeef&&w[16]==1);assert(w[24]==ctl_checksum(w+16,8));memcpy(saved,w+16,sizeof(saved));
 /* Exact retries return the original snapshot, not another execution. */
 w[32]=++generation;assert(!mu_exchange(w));assert(!memcmp(saved,w+16,sizeof(saved)));
 frame(w,2,CTL_STOP);assert(!mu_exchange(w));assert(w[22]&&mu_runtime_stopped&&!halted);quiesce_after=progress;assert(w[21]==progress);
 frame(w,3,CTL_STATUS);assert(!mu_exchange(w));assert(w[22]&&w[21]==quiesce_after&&progress==quiesce_after);
 frame(w,4,CTL_PING);assert(!mu_exchange(w));assert(w[20]==CTL_STOPPED);
 w[33]=1;assert(!mu_exchange(w)&&halted&&w[16]==0x2f000000);assert(!mu_finish());
 reset();frame(w,1,CTL_STOP);w[3]++;w[6]=ctl_checksum(w,6);assert(!mu_exchange(w)&&w[20]==CTL_BAD_EPOCH&&!mu_runtime_stopped);
 frame(w,2,CTL_STOP);assert(!mu_exchange(w)&&w[20]==CTL_BAD_SEQUENCE&&!mu_runtime_stopped);
 frame(w,1,CTL_STOP);w[6]^=1;assert(!mu_exchange(w)&&w[20]==CTL_BAD_FRAME&&!mu_runtime_stopped);
 frame(w,1,CTL_PING);assert(!mu_exchange(w));w[5]++;w[6]=ctl_checksum(w,6);w[32]=++generation;assert(mu_exchange(w)==-ETIMEDOUT&&!mu_runtime_stopped);
 reset();assert(mu_fragment(0xd0000000u,0x2f000000u,~0u,&r)==-ETIMEDOUT&&!halted);
 reset();frame(w,1,CTL_PING);mode=0;assert(mu_exchange(w)==-ETIMEDOUT&&pauses==100);assert(!mu_state.sequence);
 reset();frame(w,1,CTL_PING);mode=2;assert(mu_exchange(w)==-EIO);
 reset();for(i=0;i<3001;i++)pause_step();assert(halted&&mu_runtime_stopped&&mu_owned);
 reset();assert(!mu_fragment(0xc0000001,0x3f000001,~0u,&r));assert(mu_fragment(0xa0011234,0x5f011234,~0u,&r)==-ETIMEDOUT&&!mu_state.sequence);
 puts("Framed MU: roundtrip, duplicate, STOP/status/halt, epoch/sequence/checksum, altered retry, order, timeout, mask change, watchdog passed");return 0;
}

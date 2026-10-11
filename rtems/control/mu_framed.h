/* CTL1 serialized over message 1, one 16-bit fragment per timer interrupt.
 * All state is in the uploaded private image, never in unreserved BAR RAM. */
#include "control.c"
#ifndef MU_READ
#define MU_READ(off) (*(volatile unsigned int*)(0x1300u+(off)))
#define MU_WRITE(off,v) (*(volatile unsigned int*)(0x1300u+(off))=(v))
#endif
static unsigned int mu_owned,mu_enabled,mu_age,mu_inmask,mu_outmask;
static unsigned int mu_last,mu_generation,mu_index,mu_ready,mu_runtime_stopped;
static unsigned int mu_req[16],mu_reply[16],mu_previous[16];
static struct ctl_state mu_state;
static void mu_barrier(void *arg){(void)arg;__asm__ volatile("":::"memory");}
static int mu_quiesce(void *arg){(void)arg;mu_runtime_stopped=1;return 1;}
static unsigned int mu_start(void){unsigned int i;
 if(mu_owned||!MU_EPOCH)return 1;
 mu_inmask=MU_READ(0x28);mu_outmask=MU_READ(0x34);
 if(mu_inmask!=0x1fb||mu_outmask!=0xff||MU_READ(0x14)||MU_READ(0x1c)||
    (MU_READ(0x24)&2)||(MU_READ(0x30)&2))return 2;
 mu_owned=mu_enabled=1;mu_age=mu_last=mu_generation=mu_index=mu_ready=mu_runtime_stopped=0;
 for(i=0;i<16;i++)mu_req[i]=mu_reply[i]=mu_previous[i]=0;
 ctl_init(&mu_state,MU_EPOCH);return 0;
}
static void mu_publish(unsigned int token){
 MU_WRITE(0x24,2);(void)MU_READ(0x24);
 MU_WRITE(0x1c,token);(void)MU_READ(0x1c);
}
static void mu_poll(void){unsigned int token,kind,index,value,i,same;
 struct ctl_hooks hooks={mu_barrier,mu_quiesce,0};
 if(!mu_enabled)return;
 /* Absolute 30-second experiment budget. Timeout quiesces tasks and timer;
  * ownership remains held for validated firmware cleanup. */
 if(++mu_age>3000||MU_READ(0x28)!=mu_inmask||MU_READ(0x34)!=mu_outmask){
  mu_runtime_stopped=1;mu_enabled=0;MU_HALT();return;
 }
 ctl_tick(&mu_state);token=MU_READ(0x14);
 if(!token||token==mu_last)return;
 kind=token>>24;index=(token>>16)&255;value=token&65535;
 if(kind==0xc0){
  if((token&0xffffff)!=mu_generation+1)return;
  mu_generation++;mu_index=mu_ready=0;mu_last=token;
  for(i=0;i<16;i++)mu_req[i]=0;
  mu_publish(token^0xff000000u);return;
 }
 if(kind==0xa0 && mu_generation && index==mu_index && index<32){
  mu_req[index/2]|=value<<((index%2)*16);mu_index++;
  if(mu_index==32){
   if(mu_req[0]==mu_state.sequence){
    same=1;for(i=0;i<16;i++)if(mu_req[i]!=mu_previous[i])same=0;
    if(!same)return; /* changed duplicate is not an idempotent retry */
    mu_ready=1;
   }else if(ctl_poll(&mu_state,mu_req,mu_reply,&hooks)){
    if(!mu_reply[4]&&(mu_req[4]==CTL_STATUS||mu_req[4]==CTL_STOP)){
     mu_reply[5]=MU_PROGRESS;mu_reply[8]=ctl_checksum(mu_reply,8);
    }
    for(i=0;i<16;i++)mu_previous[i]=mu_req[i];mu_ready=1;
   }else return;
  }
  mu_last=token;mu_publish(token^0xff000000u);return;
 }
 if(kind==0xb0 && mu_ready && index<32 && !value){
  mu_last=token;mu_publish(0x4f000000u|(index<<16)|((mu_reply[index/2]>>((index%2)*16))&65535));return;
 }
 /* Final halt can only follow a completed STOP response. This stops timer
  * dispatch but is not permission to reclaim the currently returning ISR. */
 if(token==0xd0000000u && mu_ready && mu_state.stopped && mu_last==0xb01f0000u){
  mu_runtime_stopped=1;mu_enabled=0;MU_HALT();mu_last=token;mu_publish(0x2f000000u);
 }
}
static unsigned int mu_finish(void){
 mu_enabled=0;if(!mu_owned)return 0;
 if(MU_READ(0x28)!=mu_inmask||MU_READ(0x34)!=mu_outmask)return 1;
 MU_WRITE(0x14,0);(void)MU_READ(0x14);MU_WRITE(0x1c,0);(void)MU_READ(0x1c);
 MU_WRITE(0x24,2);
 if(MU_READ(0x14)||MU_READ(0x1c)||(MU_READ(0x24)&2))return 2;
 mu_owned=0;return 0;
}

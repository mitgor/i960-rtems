#ifdef I960_DOOM_CHECKPOINTS
#include "../../game/doom/runtime/startup/checkpoint_log.h"
static struct doom_checkpoint_log *checkpoints;
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
/* A scalar handshake only. Neither IRQ control nor this wait owns a WAD loan. */
static volatile unsigned checkpoint_pending,checkpoint_generation,checkpoint_ack,checkpoint_ack_index;
static unsigned checkpoint_read_mask;
static int checkpoint_barrier_stage(unsigned s){return s==42||s==43||s==44||s==50||s==51||s==63||s==80||(s>=81&&s<=98);}
#endif
static int checkpoint_init(void){unsigned i,saved;struct doom_checkpoint_log*p=doom_malloc(sizeof(*p));if(!p)return 0;
 for(i=0;i<sizeof(*p);i++)((unsigned char*)p)[i]=0;
 saved=runtime_lock();
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
 checkpoint_pending=checkpoint_generation=checkpoint_ack=checkpoint_ack_index=checkpoint_read_mask=0;
#endif
 checkpoints=p;runtime_unlock(saved);return 1;
}
static void checkpoint_retire(void){unsigned saved=runtime_lock();checkpoints=0;runtime_unlock(saved);/* controller drains the registered heap allocation afterward */}
static unsigned checkpoint_frozen[8];
static int checkpoint_mark(unsigned stage,unsigned x,unsigned y,unsigned z){unsigned saved;int rc;
 if(!owned_owner()||!checkpoints)return 0;
#ifdef I960_DOOM_PLAY
 {extern int engine_play_mark(unsigned,unsigned,unsigned,unsigned);return engine_play_mark(stage,x,y,z);}
#endif
 saved=runtime_lock();rc=doom_checkpoint_put(checkpoints,owned_generation,batch.sequence,stage,x,y,z);
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
 if(rc&&checkpoint_barrier_stage(stage)){checkpoint_generation=owned_generation;checkpoint_ack=checkpoint_ack_index=0;checkpoint_pending=checkpoints->count;}
#endif
 runtime_unlock(saved);
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
 if(rc&&checkpoint_barrier_stage(stage)){
  unsigned start=upload_time(),polls=0;
  extern void doom_shared_service(void);
  while(!checkpoint_ack){
   if(owned_stopping()){rc=-1;break;}
   /* Both elapsed-time and iteration bounds: a stopped clock cannot wait forever. */
   if(upload_time()-start>=3000||++polls>=10000000u){rc=0;break;}
   doom_shared_service();
   if(!(polls&1023u))doom_shared_yield();
  }
  saved=runtime_lock();checkpoint_pending=checkpoint_generation=checkpoint_ack=checkpoint_ack_index=0;runtime_unlock(saved);
 }
#endif
 return rc;
}
unsigned doom_runtime_checkpoint_control(unsigned op,unsigned index,unsigned value,unsigned running){
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
 if(op==0x7f){
  /* Token indexes are eight bits. Carry both full-width identity words in
   * payloads: stage the record number, then commit its generation. */
  unsigned selected=checkpoint_ack_index;
  if(index==1)checkpoint_ack_index=0;
  if(!running||upload_stopping()||!owned_running||!checkpoint_pending||checkpoint_ack||checkpoint_frozen[1]!=checkpoint_pending||checkpoint_frozen[2]!=checkpoint_generation||checkpoint_read_mask!=255u)return ~0u;
  if(index==0){if(checkpoint_ack_index||value!=checkpoint_pending)return ~0u;checkpoint_ack_index=value;return 0;}
  if(index!=1||selected!=checkpoint_pending||value!=checkpoint_generation||value!=owned_generation)return ~0u;
  checkpoint_ack=1;return 0;
 }
#endif
 if(op==0x7d){if(index||!value||value>DOOM_CHECKPOINT_CAPACITY)return ~0u;
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
  checkpoint_read_mask=0;
#endif
  if(checkpoints)return doom_checkpoint_get(checkpoints,value,checkpoint_frozen)?0:~0u;
  {unsigned i;for(i=0;i<8;i++)checkpoint_frozen[i]=0;checkpoint_frozen[0]=DOOM_CHECKPOINT_MAGIC;}return 0;
 }
 if(op==0x7e){if(index>=8||value)return ~0u;
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
  checkpoint_read_mask|=1u<<index;
#endif
  return checkpoint_frozen[index];}
 return ~0u;
}
#endif

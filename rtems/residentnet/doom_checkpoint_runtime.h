#ifdef I960_DOOM_CHECKPOINTS
#include "../../game/doom/runtime/startup/checkpoint_log.h"
static struct doom_checkpoint_log *checkpoints;
static int checkpoint_init(void){unsigned i,saved;struct doom_checkpoint_log*p=doom_malloc(sizeof(*p));if(!p)return 0;
 for(i=0;i<sizeof(*p);i++)((unsigned char*)p)[i]=0;
 saved=runtime_lock();checkpoints=p;runtime_unlock(saved);return 1;
}
static void checkpoint_retire(void){unsigned saved=runtime_lock();checkpoints=0;runtime_unlock(saved);/* controller drains the registered heap allocation afterward */}
static unsigned checkpoint_frozen[8];
static int checkpoint_mark(unsigned stage,unsigned x,unsigned y,unsigned z){unsigned saved;int rc;
 if(!owned_owner()||!checkpoints)return 0;
 saved=runtime_lock();rc=doom_checkpoint_put(checkpoints,owned_generation,batch.sequence,stage,x,y,z);runtime_unlock(saved);return rc;
}
unsigned doom_runtime_checkpoint_control(unsigned op,unsigned index,unsigned value,unsigned running){
 if(op==0x7d){if(index||!value||value>DOOM_CHECKPOINT_CAPACITY)return ~0u;
  if(checkpoints)return doom_checkpoint_get(checkpoints,value,checkpoint_frozen)?0:~0u;
  {unsigned i;for(i=0;i<8;i++)checkpoint_frozen[i]=0;checkpoint_frozen[0]=DOOM_CHECKPOINT_MAGIC;}return 0;
 }
 if(op==0x7e)return index<8&&!value?checkpoint_frozen[index]:~0u;
 return ~0u;
}
#endif

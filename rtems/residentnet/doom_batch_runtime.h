#ifdef I960_WAD_BATCH
#include "../../game/doom/runtime/batch/wire.h"
static struct doom_runtime_v1 batch_api;
static struct doom_batch batch;
#ifdef I960_DOOM_DMA
#include "../dma/wad_target.h"
#endif
#ifdef I960_DOOM_DMA
#define WAD_STAGE_BYTES 12288u
#else
#define WAD_STAGE_BYTES (8u*136u*4u)
#endif
static int batch_read(unsigned f,unsigned o,void*p,unsigned n){
 struct doom_heap*h=doom_arena_context();unsigned token,stage_token=0,start,saved,polls=0;void*stage=0;int result=-1,claimed=0;
 if(!owned_owner()||owned_stopping()||!h||f!=1||o>api.file_bytes||n>4096)return -1;
 if(!n||o==api.file_bytes)return 0;
 token=doom_heap_borrow(h,p,n);if(!token)return -1;leases++;
 stage=owned_allocate(WAD_STAGE_BYTES);if(!stage)goto done;
 stage_token=doom_heap_borrow(h,stage,WAD_STAGE_BYTES);if(!stage_token)goto done;
#ifdef I960_DOOM_DMA
 {unsigned i;for(i=0;i<12288;i++)((unsigned char*)stage)[i]=0xa5;wd_buffer=stage;wd_host=0;wd_phase=0;}
#endif
 saved=runtime_lock();batch.inbox=stage;batch_selected=1;claimed=doom_batch_begin(&batch,o,n,api.file_bytes);runtime_unlock(saved);
 if(!claimed)goto done;claimed=0;start=upload_time();
 while(!claimed){
 #ifdef I960_DOOM_DMA
  wd_step();
  if(wd_phase==3){unsigned i,total=n;if(total>api.file_bytes-o)total=api.file_bytes-o;
   for(i=total;i<4096;i++)if(wd_buffer[4096+i]){exclusive_abort();for(;;){}}
   if(!owned_stopping()){for(i=0;i<total;i++)((unsigned char*)p)[i]=wd_buffer[4096+i];result=total;batch.accepted++;}
   break;
  }
#endif
  if(owned_stopping()||upload_time()-start>=500){
#ifdef I960_DOOM_DMA
   if(wd_phase){exclusive_abort();for(;;){}}
#endif
   result=-4;break;
  }
  saved=runtime_lock();claimed=doom_batch_claim(&batch);runtime_unlock(saved);
  if(!claimed){doom_shared_service();if(!(++polls&1023u))doom_shared_yield();}
 }
 if(claimed&&!owned_stopping())result=doom_batch_copy(&batch,p,n);
 saved=runtime_lock();
#ifdef I960_DOOM_DMA
 wd_release();
#endif
 doom_batch_cancel(&batch);batch.inbox=0;runtime_unlock(saved);
 done:
#ifdef I960_DOOM_DMA
 saved=runtime_lock();wd_release();runtime_unlock(saved);
#endif
 saved=runtime_lock();if(batch.inbox==stage)batch.inbox=0;runtime_unlock(saved);
 if(stage_token&&!doom_heap_return(h,stage,stage_token)){exclusive_abort();return -5;}
 if(stage)owned_release(stage);
 if(!doom_heap_return(h,p,token)){exclusive_abort();return -5;}leases--;return result;
}
const struct doom_runtime_v1*doom_runtime_batch_api(unsigned limit){
 if(!bound||(limit!=512&&limit!=4096))return 0;batch_api=owned_api.io;batch_api.version=DOOM_API_BATCH_VERSION;
 batch_api.features=DOOM_API_BATCH_FEATURES;batch_api.max_read=limit;batch_api.read=batch_read;return &batch_api;
}
static unsigned batch_route(unsigned op,unsigned index,unsigned value,unsigned running){
#ifdef I960_DOOM_DMA
 if(op==0x77&&index)return wd_control(index,value,running&&!runtime_stopping());
 if(wd_phase&&op>=0x77)return ~0u;
#endif
 return doom_batch_control(&batch,op,index,value,running&&!runtime_stopping());}
static unsigned batch_idle(void){return batch.state==WAD_IDLE;}
static void batch_legacy(void){batch_selected=0;}
unsigned doom_runtime_batch_report(unsigned i){unsigned w[8];w[0]=DOOM_BATCH_MAGIC;w[1]=batch.sequence;w[2]=batch.accepted;w[3]=batch.rejected;w[4]=batch.cancelled;w[5]=leases;w[6]=batch.state;w[7]=api.file_bytes;return i<8?w[i]:~0u;}
#endif

#ifdef I960_WAD_BATCH
#include "doom_checkpoint_runtime.h"
#ifdef I960_DOOM_CHECKPOINTS
static struct doom_runtime_checkpoint checkpoint_api;
#define batch_owned_api checkpoint_api.base
#else
static struct doom_runtime_owned batch_owned_api;
#endif
const struct doom_runtime_owned *doom_runtime_owned_batch_api(void){const struct doom_runtime_v1*a=doom_runtime_batch_api(4096);if(!a)return 0;batch_owned_api=owned_api;batch_owned_api.io=*a;
#ifdef I960_DOOM_CHECKPOINTS
 batch_owned_api.version=DOOM_CHECKPOINT_VERSION;batch_owned_api.bytes=sizeof(checkpoint_api);batch_owned_api.features=DOOM_CHECKPOINT_FEATURES;checkpoint_api.mark=checkpoint_mark;
#endif
 return &batch_owned_api;}
#endif

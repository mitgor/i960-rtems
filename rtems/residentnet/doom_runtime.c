#ifdef I960_DOOM_RUNTIME
#include "doom_runtime.h"
#include "../../game/doom/runtime/libc.h"
#include "../../game/doom/runtime/wad.h"
#ifndef UPLOAD_NATIVE
extern unsigned int upload_time(void),upload_stopping(void);
extern void exclusive_abort(void),doom_shared_yield(void);
static unsigned int runtime_lock(void){unsigned int v=31u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");return v;}
static void runtime_unlock(unsigned int v){__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");}
#else
#include "runtime_native.h"
#endif
extern struct doom_heap *doom_arena_context(void);
static struct doom_wad wad;
static unsigned int bound,leases;
static struct doom_runtime_v1 api;
static void *allocate(unsigned int n){return doom_malloc(n);}
static unsigned int milliseconds(void){return upload_time()*10u;}
static int read_wad(unsigned int file,unsigned int offset,void*dst,unsigned int n){
 struct doom_heap*h=doom_arena_context();unsigned int saved,token,start;int result=-1,claimed=0;
 if(!bound||!h||upload_stopping()||file!=1||offset>api.file_bytes||n>512)return -1;
 if(!n||offset==api.file_bytes)return 0;
 token=doom_heap_borrow(h,dst,n);if(!token)return -1;leases++;
 saved=runtime_lock();claimed=doom_wad_begin(&wad,file,offset,n,api.file_bytes);runtime_unlock(saved);
 if(!claimed)goto done;claimed=0;start=upload_time();
 while(!claimed){
  if(upload_stopping()||upload_time()-start>=500){result=-4;break;}
  saved=runtime_lock();claimed=doom_wad_claim(&wad);runtime_unlock(saved);
  if(!claimed)doom_shared_yield(); /* worker 0 remains runnable */
 }
 if(claimed&&!upload_stopping())result=doom_wad_copy(&wad,dst,n);
 saved=runtime_lock();doom_wad_cancel(&wad);runtime_unlock(saved);
done:
 if(!doom_heap_return(h,dst,token)){exclusive_abort();return -5;}leases--;return result;
}
unsigned int doom_runtime_bind(const unsigned int*w,unsigned int n){unsigned int i;
 if(bound||n!=11||w[0]!=WAD_MAGIC||w[1]!=1||w[2]<512||w[2]>268435456u||!doom_arena_context())return 1;
 api.magic=DOOM_API_MAGIC;api.version=DOOM_API_VERSION;api.bytes=sizeof(api);api.features=DOOM_API_FEATURES;api.pointer_bytes=sizeof(void*);api.little_endian=1;api.arena_bytes=8u*1048576u;api.max_read=512;api.file_id=1;api.file_bytes=w[2];
 for(i=0;i<8;i++)api.sha256[i]=w[3+i];api.allocate=allocate;api.release=doom_free;api.ticks_ms=milliseconds;api.read=read_wad;api.reserved[0]=api.reserved[1]=0;bound=1;return 0;
}
const struct doom_runtime_v1*doom_runtime_api(void){return bound?&api:0;}
unsigned int doom_runtime_control(unsigned int op,unsigned int index,unsigned int value,unsigned int running){return doom_wad_control(&wad,op,index,value,running&&!upload_stopping());}
unsigned int doom_runtime_report(unsigned int i){unsigned int w[8];w[0]=WAD_MAGIC;w[1]=wad.sequence;w[2]=wad.accepted;w[3]=wad.rejected;w[4]=wad.cancelled;w[5]=leases;w[6]=wad.state;w[7]=api.file_bytes;return i<8?w[i]:~0u;}
unsigned int doom_runtime_finish(void){return !leases&&wad.state==WAD_IDLE;}
#endif

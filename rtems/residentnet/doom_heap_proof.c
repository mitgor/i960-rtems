#ifdef I960_DOOM_HEAP
#include "../../game/doom/runtime/libc.h"
/* Only upload worker 1 calls the allocator; finish runs after BOTH task/IRQ
 * contexts drain. No other task or ISR may call these private entry points. */
extern unsigned int upload_stopping(void);
extern void exclusive_abort(void);
static struct doom_heap heap;
static unsigned int locked,ready;
static unsigned char *retained;
static int enter(void*p){(void)p;if(locked)return 0;locked=1;return 1;}
static void leave(void*p){(void)p;locked=0;}
static int progress(void*p){(void)p;return !upload_stopping();}
static void fatal(unsigned int code){(void)code;exclusive_abort();}
static int check(unsigned char*p,unsigned int n,unsigned int zero){unsigned int i;
 for(i=0;i<n;i++){if(!(i&1023)&&upload_stopping())return 0;if(p[i]!=(zero?0:(unsigned char)i)){exclusive_abort();return 0;}}return 1;}
unsigned int doom_arena_proof(struct arena*a){
 struct doom_heap_hooks hooks={enter,leave,progress,0};unsigned char*zone=0,*p=0,*q=0,*copy=0;unsigned int i,rc=1;
 if(ready)return 2;
 if(!doom_heap_init(&heap,a,&hooks)||!doom_libc_bind(&heap,fatal))return 3;ready=1;
 zone=doom_calloc(6,1048576);if(!zone||!check(zone,6u*1048576u,1))goto done;
 p=doom_malloc(128000);if(!p)goto done;for(i=0;i<128000;i++)p[i]=(unsigned char)i;
 q=doom_realloc(p,196608);if(!q)goto done;p=q;q=0;if(!check(p,128000,0))goto done;
 if(doom_realloc(p,8u*1048576u)||doom_calloc(~0u,2)||!check(p,128000,0))goto done;
 copy=(unsigned char*)doom_strdup("Doom arena ABI");if(!copy)goto done;
 for(i=0;i<15;i++)if(copy[i]!=(unsigned char)"Doom arena ABI"[i])goto done;
 retained=doom_malloc(65536);if(!retained)goto done;
 for(i=0;i<65536;i++)retained[i]=(unsigned char)i;
 rc=0;
done:doom_free(copy);doom_free(p);doom_free(zone);return rc;
}
unsigned int doom_arena_finish(void){unsigned int i;
 if(!ready)return 1;
 /* STOP is already set; don't use the stop-aware bulk checker here. */
 if(retained)for(i=0;i<65536;i++)if(retained[i]!=(unsigned char)i)return 0;
 if(!doom_heap_stop(&heap)||!doom_heap_drain(&heap))return 0;
 return !heap.blocks&&!heap.live&&!heap.busy&&!heap.fault;
}
#endif

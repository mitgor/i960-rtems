#ifdef I960_GENERAL_HEAP
#include <string.h>
#include <rtems/system.h>
#include <rtems/score/heap.h>
#include <rtems/score/isr.h>
#include "general_heap.h"
#ifndef HEAP_NATIVE
#define HEAP_BASE RESIDENT_HEAP_BASE
#define HEAP_ABORT() exclusive_abort()
extern void exclusive_abort(void);
extern unsigned int exclusive_extra_valid(void),exclusive_extra_guard_mask(void);
static unsigned int heap_raw_lock(void){unsigned int v=31u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");return v;}
static void heap_raw_unlock(unsigned int v){__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(v)::"g0","memory");}
#else
#include "heap_native.h"
#endif
#ifdef I960_HEAP_SHARED
#include "heap_timing.inc"
static unsigned int shared_protected(void*),shared_valid(void);
static void shared_worker(unsigned int,unsigned int),shared_drain(unsigned int);
static unsigned int shared_selftest(void);
#else
#define lock_heap heap_raw_lock
#define unlock_heap heap_raw_unlock
#endif
#define HWORD(a) (*(volatile unsigned int*)(a))
#define HEAP_END (HEAP_BASE+RESIDENT_HEAP_BYTES)
#define HEAP_SLOTS 64
struct live_block {unsigned char*raw;unsigned int size,busy;};
static struct live_block blocks[HEAP_SLOTS];
static Heap_Control app_heap;
#ifdef I960_QUEUE_RECLAIM
static Heap_Control fallback_heap;
#endif
static Heap_Control*arena(unsigned int p,unsigned int n){
 if(p>=HEAP_BASE&&p<HEAP_END&&n<=HEAP_END-p)return &app_heap;
#ifdef I960_QUEUE_RECLAIM
 {unsigned int b=resident_fallback_base();if(p>=b&&p<b+FALLBACK_HEAP_BYTES&&n<=b+FALLBACK_HEAP_BYTES-p)return &fallback_heap;}
#endif
 return 0;
}
static unsigned int heap_ready,heap_error,allocations,frees,rejections,live_bytes,peak_bytes,selftest;
static unsigned int operations[2],last_tick[2],seeds[2]={17,91};
static unsigned char*worker_block[2];
static unsigned int worker_size[2],worker_value[2];
static unsigned int find_block(void*p){unsigned int i;for(i=0;i<HEAP_SLOTS;i++)if(blocks[i].raw&&blocks[i].raw+16==p)return i;return HEAP_SLOTS;}
static unsigned int redzones(void){unsigned int i,j;for(i=0;i<HEAP_SLOTS;i++)if(blocks[i].raw){
 unsigned char*p=blocks[i].raw;unsigned int n=blocks[i].size;
 if(n>HEAP_MAX_BYTES-32||!arena((unsigned int)p,n+32))return 0;
 for(j=0;j<16;j++)if(p[j]!=(unsigned char)(0xa5^j)||p[16+n+j]!=(unsigned char)(0x5a^j))return 0;
 }return 1;}
/* Bounded physical and free-list validation before entering the legacy allocator.
 * No speculative dereference of a corrupt next pointer. At most 64 live blocks. */
static unsigned int metadata_one(Heap_Control*control,unsigned int base,unsigned int end){unsigned int a=base,previous=1,n=0,nfree=0,nused=0,registered=0,freeaddr[65],i,p,prev;
 if((unsigned int)control->start!=base||(unsigned int)control->final!=end-8||control->page_size!=16||control->permanent_null)return 0;
 while(a<end-8){unsigned int f,size;
  if(++n>129||a&3||HWORD(a)!=previous)return 0;
  f=HWORD(a+4);size=f&~1u;if(size<16||(size&3)||size>end-8-a)return 0;
  if(!(f&1)){if(nfree==65)return 0;freeaddr[nfree++]=a;}
  /* RTEMS free trusts the saved alignment offset before its block checks.
   * Bind every used block to the registry and validate that offset first. */
  else {unsigned int offset=16-((a+8)&15),raw=a+8+offset;
   if(raw>a+size||a+size-raw<32||HWORD(raw-4)!=offset)return 0;
   for(i=0;i<HEAP_SLOTS;i++)if((unsigned int)blocks[i].raw==raw)break;
   if(i==HEAP_SLOTS||blocks[i].size>a+size-raw-32)return 0;nused++;
  }
  previous=f;a+=size;
 }
 if(a!=end-8||HWORD(a)!=previous||HWORD(a+4)!=1)return 0;
 for(i=0;i<HEAP_SLOTS;i++)if(blocks[i].raw&&(unsigned int)blocks[i].raw>=base&&(unsigned int)blocks[i].raw<end){if(blocks[i].busy>1)return 0;registered++;}
 if(nused!=registered)return 0;
 p=(unsigned int)control->first;prev=(unsigned int)&control->start;
 for(n=0;n<nfree;n++){
  if(p<base||p>=end-8)return 0;
  for(i=0;i<nfree;i++)if(freeaddr[i]==p)break;
  if(i==nfree||HWORD(p+12)!=prev)return 0;
  freeaddr[i]=0;prev=p;p=HWORD(p+8);
 }
 return p==(unsigned int)&control->final&&(unsigned int)control->last==prev;
}
static unsigned int metadata(void){unsigned int i;
 for(i=0;i<HEAP_SLOTS;i++)if(blocks[i].raw&&!arena((unsigned int)blocks[i].raw,1))return 0;
 return metadata_one(&app_heap,HEAP_BASE,HEAP_END)
#ifdef I960_QUEUE_RECLAIM
 &&metadata_one(&fallback_heap,resident_fallback_base(),resident_fallback_base()+FALLBACK_HEAP_BYTES)
#endif
 ;
}
unsigned int resident_heap_valid(void){return heap_ready&&!heap_error&&metadata()&&redzones()
#ifdef I960_HEAP_SHARED
 &&shared_valid()
#endif
 ;}
static void poison(unsigned int code){heap_error=code;HEAP_ABORT();}
static unsigned int enter_op(unsigned int*saved,unsigned int op){
 *saved=lock_heap();
#ifdef I960_HEAP_SHARED
 timing_op=op;
#endif
 if(!heap_ready||_ISR_Nest_level){rejections++;unlock_heap(*saved);return 0;}
 if(!exclusive_extra_valid()){poison(1);return 0;}
 if(!metadata()){poison(2);return 0;}
 if(!redzones()){poison(3);return 0;}
#ifdef I960_HEAP_SHARED
 if(!shared_valid()){poison(11);return 0;}
#endif
 return 1;
}
static void*allocate(unsigned int n){unsigned int i,j;unsigned char*p;
 if(!n||n>HEAP_MAX_BYTES-64){rejections++;return 0;}
 for(i=0;i<HEAP_SLOTS&&blocks[i].raw;i++);
 if(i==HEAP_SLOTS){rejections++;return 0;}
 p=_Heap_Allocate(&app_heap,n+32);
#ifdef I960_QUEUE_RECLAIM
 if(!p)p=_Heap_Allocate(&fallback_heap,n+32);
#endif
 if(!p){rejections++;return 0;}
 if(!arena((unsigned int)p,n+32)||((unsigned int)p&15)){poison(4);return 0;}
 blocks[i].raw=p;blocks[i].size=n;blocks[i].busy=0;
 for(j=0;j<16;j++){p[j]=0xa5^j;p[16+n+j]=0x5a^j;}
 live_bytes+=n;if(live_bytes>peak_bytes)peak_bytes=live_bytes;allocations++;return p+16;
}
static unsigned int release_raw(void*p){unsigned int i;if(!p)return 0;i=find_block(p);
 if(i==HEAP_SLOTS||blocks[i].busy){rejections++;return 1;}
 if(!_Heap_Free(arena((unsigned int)blocks[i].raw,1),blocks[i].raw)){poison(5);return 2;}
 live_bytes-=blocks[i].size;blocks[i].raw=0;blocks[i].size=0;frees++;return 0;
}
static unsigned int release(void*p){
#ifdef I960_HEAP_SHARED
 if(shared_protected(p)){rejections++;return 1;}
#endif
 return release_raw(p);
}
#define enter(p) enter_op(p,0)
void resident_heap_check(void){unsigned int saved;if(enter(&saved))unlock_heap(saved);}
void*resident_malloc(unsigned int n){unsigned int saved;void*p;if(!enter_op(&saved,1))return 0;p=allocate(n);unlock_heap(saved);return p;}
unsigned int resident_free(void*p){unsigned int saved,rc;if(!p)return 0;if(!enter_op(&saved,4))return 1;rc=release(p);unlock_heap(saved);return rc;}
void*resident_calloc(unsigned int n,unsigned int size){unsigned int saved;void*p;if(!enter_op(&saved,2))return 0;
 if(!n||!size||size>(HEAP_MAX_BYTES-64)/n){rejections++;unlock_heap(saved);return 0;}
 p=allocate(n*size);
#ifdef I960_HEAP_SHARED
 if(p){unsigned int slot=find_block(p),before;
  blocks[slot].busy=1;unlock_heap(saved);before=irq_samples;memset(p,0,n*size);
  if(!enter_op(&saved,2))return 0;if(irq_samples!=before)copy_preemptions[0]++;
  blocks[slot].busy=0;
 }
#else
 if(p)memset(p,0,n*size);
#endif
 unlock_heap(saved);return p;
}
void*resident_realloc(void*p,unsigned int n){unsigned int saved,i,old;void*q;
 if(!p)return resident_malloc(n);if(!n){resident_free(p);return 0;}
 if(!enter_op(&saved,3))return 0;
#ifdef I960_HEAP_SHARED
 if(shared_protected(p)){rejections++;unlock_heap(saved);return 0;}
#endif
 i=find_block(p);if(i==HEAP_SLOTS||blocks[i].busy){rejections++;unlock_heap(saved);return 0;}
 old=blocks[i].size;q=allocate(n);if(q){
#ifdef I960_HEAP_SHARED
  unsigned int slot=find_block(q),before;blocks[i].busy=blocks[slot].busy=1;
  unlock_heap(saved);before=irq_samples;memcpy(q,p,n<old?n:old);
  if(!enter_op(&saved,3))return 0;if(irq_samples!=before)copy_preemptions[1]++;
  blocks[i].busy=blocks[slot].busy=0;
#else
  memcpy(q,p,n<old?n:old);
#endif
  release(p);
 }unlock_heap(saved);return q;
}
#ifdef I960_HEAP_SHARED
#include "shared_heap.inc"
#endif
static unsigned int startup_test(void){void*p[64],*q;unsigned int i,j,n=0;
 if(resident_malloc(0)||resident_malloc(~0u)||resident_calloc(~0u,2))return 1;
 q=resident_calloc(31,7);if(!q)return 2;for(i=0;i<217;i++)if(((unsigned char*)q)[i])return 3;
 memset(q,0x3c,217);p[0]=resident_realloc(q,4096);if(!p[0])return 4;
 for(i=0;i<217;i++)if(((unsigned char*)p[0])[i]!=0x3c)return 5;
 if(resident_realloc(p[0],HEAP_MAX_BYTES))return 6;
 if(!resident_free((char*)p[0]+1)||resident_free(p[0])||!resident_free(p[0]))return 7;
 while(n<64&&(p[n]=resident_malloc(2048))!=0)n++;
 if(n<20)return 8;
 for(i=0;i<n;i+=2)if(resident_free(p[i]))return 9;
 for(i=1;i<n;i+=2)if(resident_free(p[i]))return 10;
 q=resident_malloc(RESIDENT_HEAP_BYTES-256);if(!q)return 11;
 for(j=0;j<RESIDENT_HEAP_BYTES-256;j++)((unsigned char*)q)[j]=(unsigned char)j;
 for(j=0;j<RESIDENT_HEAP_BYTES-256;j++)if(((unsigned char*)q)[j]!=(unsigned char)j)return 12;
 if(resident_free(q)||live_bytes||allocations!=frees||!resident_heap_valid())return 13;
 for(i=0;i<64;i++){p[i]=resident_malloc(1);if(!p[i])return 14;}
 if(resident_malloc(1)||resident_realloc(p[0],2))return 15;
 for(i=0;i<64;i++)if(resident_free(p[i]))return 16;
 if(live_bytes||allocations!=frees||!resident_heap_valid())return 17;
 return 0;
}
unsigned int resident_heap_init(void){unsigned int rc;
 if(heap_ready||!exclusive_extra_valid())return 1;
#ifdef I960_HEAP_SHARED
 timing_init();
#endif
 if(!_Heap_Initialize(&app_heap,(void*)HEAP_BASE,RESIDENT_HEAP_BYTES,16))return 2;
#ifdef I960_QUEUE_RECLAIM
 if(!resident_fallback_valid()||!_Heap_Initialize(&fallback_heap,(void*)resident_fallback_base(),FALLBACK_HEAP_BYTES,16))return 19;
#endif
 heap_ready=1;rc=startup_test();if(rc){heap_error=0x100+rc;return rc;}selftest=1;
#ifdef I960_QUEUE_RECLAIM
 {unsigned char*p=resident_malloc(RESIDENT_HEAP_BYTES-64),*q=resident_malloc(FALLBACK_HEAP_BYTES-64);unsigned int j;
 if(!p||!q||arena((unsigned int)p-16,1)!=&app_heap||arena((unsigned int)q-16,1)!=&fallback_heap)return 20;
 for(j=0;j<FALLBACK_HEAP_BYTES-64;j++)q[j]=(unsigned char)j;
 for(j=0;j<FALLBACK_HEAP_BYTES-64;j++)if(q[j]!=(unsigned char)j)return 21;
 if(resident_malloc(HEAP_MAX_BYTES)||resident_free(p)||resident_free(q)||!resident_heap_valid())return 22;
 }
#endif
#ifdef I960_HEAP_SHARED
 if(shared_selftest())return 18;
#endif
 return 0;
}
void resident_heap_step(unsigned int id,unsigned int tick){unsigned int i,n;unsigned char*p;
 if(id>1||last_tick[id]==tick)return;last_tick[id]=tick;
 p=worker_block[id];if(p){for(i=0;i<worker_size[id];i++)if(p[i]!=worker_value[id])poison(6);if(resident_free(p))poison(7);worker_block[id]=0;}
#ifdef I960_HEAP_SHARED
 shared_worker(id,tick);
#endif
 seeds[id]=seeds[id]*1664525u+1013904223u;n=1+(seeds[id]%3072);
 p=resident_malloc(n);if(!p)poison(8);worker_size[id]=n;worker_value[id]=(tick+id*31)&255;
 memset(p,worker_value[id],n);worker_block[id]=p;operations[id]++;
}
void resident_heap_drain(unsigned int id){unsigned int i;
#ifdef I960_HEAP_SHARED
 shared_drain(id);
#endif
 if(worker_block[id]){
 for(i=0;i<worker_size[id];i++)if(worker_block[id][i]!=worker_value[id])poison(6);
 if(resident_free(worker_block[id]))poison(7);worker_block[id]=0;}
}
void resident_heap_report(unsigned int*w){
 w[0]=0x31504548;w[1]=HEAP_BASE;w[2]=HEAP_TOTAL_BYTES;w[3]=heap_ready;
 w[4]=heap_error;w[5]=allocations;w[6]=frees;w[7]=live_bytes;w[8]=peak_bytes;w[9]=rejections;
 w[10]=selftest;w[11]=resident_heap_valid();w[12]=operations[0];w[13]=operations[1];w[14]=exclusive_extra_guard_mask();w[15]=I960_HEAP_TEST;
}
void resident_heap_inject(void){
#if I960_HEAP_TEST == 1
 HWORD(RESIDENT_HEAP_BASE-64)^=1; /* queue-end / heap-start guard */
#elif I960_HEAP_TEST == 2
 if(worker_block[0])worker_block[0][worker_size[0]]^=1;
#elif I960_HEAP_TEST == 3
 HWORD(HEAP_BASE+4)^=0x80000000u; /* invalid block extent, rejected before allocator */
#elif I960_HEAP_TEST == 5
 HWORD(resident_fallback_base()-64)^=1;
#elif I960_HEAP_TEST == 6
 HWORD(resident_fallback_base()+4)^=0x80000000u;
#elif I960_HEAP_TEST == 4
 if(worker_block[0])HWORD((unsigned int)worker_block[0]-20)^=1; /* saved alignment offset used by free */
#endif
}
#ifndef HEAP_NATIVE
void*malloc(size_t n){return resident_malloc(n);}
void*calloc(size_t n,size_t z){return resident_calloc(n,z);}
void*realloc(void*p,size_t n){return resident_realloc(p,n);}
void free(void*p){(void)resident_free(p);}
#endif
#endif

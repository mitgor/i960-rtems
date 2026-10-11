#!/usr/bin/env python3
"""Linux freestanding 32-bit test of the actual RTEMS allocator and wrapper.
No multilib libc required; only gcc's -m32 backend and Linux IA32 support.
"""
import argparse,json,hashlib,subprocess,shutil,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--rtems',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument("--shared",action="store_true");p.add_argument("--iterations",type=int,default=1000);p.add_argument("--queue-reclaim",action="store_true");a=p.parse_args();assert not a.queue_reclaim or a.shared;assert 1000<=a.iterations<=100000;out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parent
inc=out/'include';(inc/'rtems/score').mkdir(parents=True,exist_ok=True)
(inc/'rtems/system.h').write_text('''#ifndef TEST_SYSTEM_H
#define TEST_SYSTEM_H
typedef unsigned int unsigned32;typedef int boolean;typedef unsigned int size_t;
#define TRUE 1
#define FALSE 0
#define NULL ((void*)0)
#define RTEMS_INLINE_ROUTINE static inline
#define CPU_HEAP_ALIGNMENT 16
#define CPU_ALIGNMENT 16
#endif
''')
(inc/'rtems/score/sysstate.h').write_text('')
(inc/'rtems/score/isr.h').write_text('extern unsigned int _ISR_Nest_level;\n')
(inc/'string.h').write_text('#include <rtems/system.h>\nvoid*memset(void*,int,size_t);void*memcpy(void*,const void*,size_t);\n')
inputs=[]
for rel in ['include/rtems/score/heap.h','include/rtems/score/address.h','inline/rtems/score/heap.inl','inline/rtems/score/address.inl']:
 source=a.rtems/'cpukit/score'/rel;dest=inc/'rtems/score'/source.name;shutil.copyfile(source,dest);inputs.append(source)
(out/'heap_native.h').write_text('''static unsigned char native_arena[RESIDENT_HEAP_BYTES] __attribute__((aligned(16)));
#ifdef I960_QUEUE_RECLAIM
static unsigned char native_fallback[FALLBACK_HEAP_BYTES] __attribute__((aligned(16)));
unsigned int resident_fallback_base(void){return (unsigned int)native_fallback;}
unsigned int resident_fallback_valid(void){return 1;}
#endif
#define HEAP_BASE ((unsigned int)native_arena)
static unsigned int native_admit=1,native_mask,native_actor;
static int native_jump[5];
#define HEAP_ABORT() __builtin_longjmp(native_jump,1)
static unsigned int exclusive_extra_valid(void){return native_admit;}
static unsigned int exclusive_extra_guard_mask(void){return !native_admit;}
static unsigned int heap_raw_lock(void){unsigned int old=native_mask;native_mask=31;return old;}
static void heap_raw_unlock(unsigned int old){native_mask=old;}
''')
(out/'main.c').write_text('#define WORKER_ITERATIONS '+str(a.iterations)+'\n'+('#define I960_HEAP_SHARED 1\n' if a.shared else '')+('#define I960_QUEUE_RECLAIM 1\n' if a.queue_reclaim else '')+'''#define I960_GENERAL_HEAP 1
#define I960_HEAP_TEST 0
#define HEAP_NATIVE 1
#include "general_heap.c"
unsigned int _ISR_Nest_level;
void resident_net_irq_counts(unsigned int*w){w[0]=w[1]=0;}
void*memset(void*p,int c,size_t n){unsigned char*q=p;while(n--)*q++=c;return p;}
void*memcpy(void*p,const void*q,size_t n){unsigned char*d=p;const unsigned char*s=q;while(n--)*d++=*s++;return p;}
static void quit(unsigned int code){__asm__ volatile("int $0x80"::"a"(1),"b"(code):"memory");for(;;){}}
#define CHECK(x) do{if(!(x))quit(__LINE__);}while(0)
void _start(void){unsigned int i,t,old;unsigned char*p;void*saved;void*slots[64];
 if(__builtin_setjmp(native_jump))quit(128+heap_error);
 CHECK(sizeof(void*)==4);CHECK(!resident_malloc(1));CHECK(!resident_heap_init());CHECK(resident_heap_valid()&&selftest);
 p=resident_malloc(RESIDENT_HEAP_BYTES-64);CHECK(p&&resident_heap_valid());
#ifdef I960_QUEUE_RECLAIM
 slots[0]=resident_malloc(FALLBACK_HEAP_BYTES-64);CHECK(slots[0]);
 CHECK(!resident_malloc(1));CHECK(!resident_free(slots[0]));
#else
 CHECK(!resident_malloc(1));
#endif
 CHECK(!resident_free(p)&&resident_heap_valid());
 for(i=0;i<64;i++){slots[i]=resident_malloc(1);CHECK(slots[i]&&!((unsigned int)slots[i]&15));}
 CHECK(!resident_malloc(1));CHECK(!resident_realloc(slots[0],2));
 for(i=0;i<64;i++)CHECK(!resident_free(slots[i]));
#ifdef I960_QUEUE_RECLAIM
 {unsigned int j;void*prior;
  p=resident_malloc(40000);CHECK(p);memset(p,0x39,40000);
  p=resident_realloc(p,80000);CHECK(p&&arena((unsigned int)p-16,1)==&fallback_heap);
  for(j=0;j<40000;j++)CHECK(p[j]==0x39);
  p=resident_realloc(p,20000);CHECK(p&&arena((unsigned int)p-16,1)==&app_heap);
  for(j=0;j<20000;j++)CHECK(p[j]==0x39);CHECK(!resident_free(p));
  slots[0]=resident_malloc(RESIDENT_HEAP_BYTES-64);CHECK(slots[0]);
  p=resident_malloc(100);CHECK(p&&arena((unsigned int)p-16,1)==&fallback_heap);
  prior=fallback_heap.first;old=frees;
  for(j=0;j<32;j++){
   fallback_heap.first=(void*)((unsigned int)prior^(1u<<j));
   if(!__builtin_setjmp(native_jump)){resident_free(p);quit(210);}
   CHECK(heap_error==2&&frees==old);fallback_heap.first=prior;heap_error=0;native_mask=0;
  }
  CHECK(!resident_free(p)&&!resident_free(slots[0])&&resident_heap_valid());
 }
#endif
 p=resident_realloc(0,100);CHECK(p);memset(p,0x71,100);
 p=resident_realloc(p,20);CHECK(p);for(i=0;i<20;i++)CHECK(p[i]==0x71);
 CHECK(!resident_realloc(p,0)&&!resident_free(0));
 for(t=1;t<=WORKER_ITERATIONS;t++){native_actor=0;resident_heap_step(0,t);native_actor=1;resident_heap_step(1,t);}
 native_actor=0;resident_heap_drain(0);native_actor=1;resident_heap_drain(1);CHECK(!live_bytes&&allocations==frees&&resident_heap_valid());
#ifdef I960_HEAP_SHARED
 {unsigned int h,h2,prior=shared_generation;
  native_actor=0;CHECK(!resident_shared_resume(0));native_actor=1;CHECK(!resident_shared_resume(1));
  native_actor=0;h=resident_shared_new(0,100);CHECK(h&&resident_shared_acquire(h,1));
  native_actor=1;CHECK(!resident_shared_acquire(h,1));p=resident_shared_pin(h,1);CHECK(p);memset(p,0x29,100);
  CHECK(!resident_shared_cancel(0)&&resident_shared_ack(h,0));native_actor=0;CHECK(!resident_shared_ack(h,0));
  CHECK(!resident_shared_new(0,1));CHECK(!resident_shared_resume(0));CHECK(resident_shared_acquire(h,0));
  native_actor=1;CHECK(!resident_shared_cancel(1));old=frees;
  for(i=0;i<1000;i++)CHECK(resident_shared_ack(h,1)==2&&frees==old&&p[i%100]==0x29&&resident_heap_valid());
  CHECK(!resident_shared_unpin(h,1)&&!resident_shared_ack(h,1));CHECK(resident_shared_ack(h,1));CHECK(!resident_shared_resume(1));
  native_actor=0;h2=resident_shared_new(0,100);CHECK(h2!=h&&!resident_shared_pin(h,0));
  CHECK(!resident_shared_cancel(0)&&!resident_shared_ack(h2,0)&&!resident_shared_resume(0));
  h=resident_shared_new(0,100);CHECK(h);old=frees;shared[h&7].pins=2;
  if(!__builtin_setjmp(native_jump)){resident_free(shared[h&7].p);quit(205);}
  CHECK(heap_error==11&&frees==old);shared[h&7].pins=0;heap_error=0;native_mask=0;
  CHECK(!resident_shared_cancel(0)&&!resident_shared_ack(h,0)&&!resident_shared_resume(0));
  {unsigned int sum[2]={0xfffffff0u,1};add_time(sum,32);CHECK(sum[0]==16&&sum[1]==2);}
  prior=shared_generation;shared_generation=0x1ffffffe;
  h=resident_shared_new(0,1);CHECK(h>>3==0x1fffffff);CHECK(!resident_shared_cancel(0)&&!resident_shared_ack(h,0)&&!resident_shared_resume(0));
  CHECK(!resident_shared_new(0,1));shared_generation=prior;
  CHECK(!resident_shared_cancel(0)&&!resident_shared_cancel(1));
 }
#endif
#ifdef I960_HEAP_SHARED
 {unsigned int state=17,h,a,action,slot;
  for(t=0;t<5000;t++){
   state=state*1664525u+1013904223u;a=state&1;native_actor=a;action=(state>>5)%7;slot=(state>>12)&7;
   h=shared[slot].p?(shared[slot].generation<<3)|slot:0;
   if(action==0)resident_shared_new(a,1+(state%512));
   else if(action==1)resident_shared_acquire(h,a);
   else if(action==2)resident_shared_pin(h,a);
   else if(action==3)resident_shared_unpin(h,a);
   else if(action==4)resident_shared_cancel(a);
   else if(action==5)resident_shared_ack(h,a);
   else resident_shared_resume(a);
   CHECK(resident_heap_valid());
   for(i=0;i<8;i++)if(shared[i].p)CHECK(shared[i].refs&&!(shared[i].pins&~shared[i].refs));
  }
  resident_shared_cancel(0);resident_shared_cancel(1);
  for(a=0;a<2;a++){native_actor=a;for(i=0;i<8;i++)if(shared[i].p){
   h=(shared[i].generation<<3)|i;if(shared[i].pins&(1u<<a))CHECK(!resident_shared_unpin(h,a));
   if(shared[i].refs&(1u<<a))CHECK(!resident_shared_ack(h,a));
  }}
  CHECK(shared_created==shared_retired&&!live_bytes&&allocations==frees);
 }
#endif
 p=resident_malloc(100);CHECK(p);blocks[find_block(p)].busy=1;old=frees;
 CHECK(resident_free(p)&&!resident_realloc(p,200)&&frees==old);blocks[find_block(p)].busy=0;CHECK(!resident_free(p));
 _ISR_Nest_level=1;CHECK(!resident_malloc(64)&&native_mask==0);_ISR_Nest_level=0;
 p=resident_malloc(100);CHECK(p);old=frees;
 for(i=0;i<32;i++){
  unsigned char*q=i<16?p-16+i:p+100+i-16;*q^=1;
  if(!__builtin_setjmp(native_jump)){resident_malloc(1);quit(200);}
  CHECK(heap_error==3&&frees==old);*q^=1;heap_error=0;native_mask=0;
 }
 for(i=0;i<32;i++){
  unsigned int*q=(unsigned int*)(p-20);*q^=1u<<i;
  if(!__builtin_setjmp(native_jump)){resident_free(p);quit(203);}
  CHECK(heap_error==2&&frees==old);*q^=1u<<i;heap_error=0;native_mask=0;
 }
 saved=app_heap.first;
 for(i=0;i<32;i++){
  app_heap.first=(void*)((unsigned int)saved^(1u<<i));
  if(!__builtin_setjmp(native_jump)){resident_malloc(1);quit(201);}
  CHECK(heap_error==2&&frees==old);app_heap.first=saved;heap_error=0;native_mask=0;
 }
 native_admit=0;
 if(!__builtin_setjmp(native_jump)){resident_malloc(1);quit(202);}
 CHECK(heap_error==1&&frees==old);native_admit=1;heap_error=0;native_mask=0;
 CHECK(!resident_free(p)&&!live_bytes&&allocations==frees&&resident_heap_valid());
 slots[0]=resident_malloc(100);slots[1]=resident_malloc(100);slots[2]=resident_malloc(100);
 CHECK(slots[0]&&slots[1]&&slots[2]);CHECK(!resident_free(slots[0])&&!resident_free(slots[2]));
 saved=app_heap.first->next;app_heap.first->next=0;old=frees;
 if(!__builtin_setjmp(native_jump)){resident_free(slots[1]);quit(204);}
 CHECK(heap_error==2&&frees==old);app_heap.first->next=saved;heap_error=0;native_mask=0;
 CHECK(!resident_free(slots[1])&&!live_bytes&&allocations==frees&&resident_heap_valid());
#ifdef I960_HEAP_SHARED
 CHECK(shared_cycles>50&&shared_checks>50&&shared_created==shared_retired&&shared_deferred>50);
 CHECK(shared_cancelled==3&&shared_tested);
 {unsigned int report[64];resident_heap_diagnostics(report);
  __asm__ volatile("int $0x80"::"a"(4),"b"(1),"c"(report),"d"(sizeof(report)):"memory");}
#endif
 quit(0);
}
''')
sources=[a.rtems/'cpukit/score/src'/n for n in ['heap.c','heapallocate.c','heapfree.c']];inputs+=sources
cmd=['gcc','-m32','-nostdlib','-ffreestanding','-fno-builtin','-fno-pie','-no-pie','-fno-stack-protector','-O1','-I'+str(inc),'-I'+str(root),'-I'+str(out),str(out/'main.c'),*map(str,sources),'-o',str(out/'heap-test')]
subprocess.run(cmd,check=True);run=subprocess.run([str(out/'heap-test')],check=True,stdout=subprocess.PIPE)
if a.shared:
 assert len(run.stdout)==256
 (out/'diagnostics.json').write_text(json.dumps(list(struct.unpack('<64I',run.stdout)),indent=2)+'\n')
(out/'result.json').write_text(json.dumps(dict(actual_rtems_sources={str(p.relative_to(a.rtems)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},queue_reclaim=a.queue_reclaim,cross_arena_realloc=a.queue_reclaim,fallback_free_list_pointer_bit_mutations=32 if a.queue_reclaim else 0,shared_enabled=a.shared,shared_random_operations=5000 if a.shared else 0,busy_buffer_reclaim_refused=True,shared_uncertain_ack_retries=1000 if a.shared else 0,generation_exhaustion_tested=a.shared,shared_registry_corruption_contained=a.shared,pointer_bits=32,live_slot_limit=64,empty_free_list_checked=True,realloc_shrink_and_oom_preserve=True,worker_iterations=a.iterations*2,redzone_mutations=32,free_list_pointer_bit_mutations=32,alignment_offset_bit_mutations=32,null_free_list_link_rejected=True,guard_failure_retains_allocations=True,passed=True),indent=2)+'\n')
print('Actual RTEMS 4.6.6 allocator, 32-bit wrapper: startup/exhaustion/coalescing, worker stress iterations, ISR refusal, 32 redzone, 32 offset and 32 pointer corruptions passed')

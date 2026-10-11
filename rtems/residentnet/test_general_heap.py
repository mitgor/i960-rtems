#!/usr/bin/env python3
"""Linux freestanding 32-bit test of the actual RTEMS allocator and wrapper.
No multilib libc required; only gcc's -m32 backend and Linux IA32 support.
"""
import argparse,json,hashlib,subprocess,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--rtems',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parent
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
#define HEAP_BASE ((unsigned int)native_arena)
static unsigned int native_admit=1,native_mask;
static int native_jump[5];
#define HEAP_ABORT() __builtin_longjmp(native_jump,1)
static unsigned int exclusive_extra_valid(void){return native_admit;}
static unsigned int exclusive_extra_guard_mask(void){return !native_admit;}
static unsigned int lock_heap(void){unsigned int old=native_mask;native_mask=31;return old;}
static void unlock_heap(unsigned int old){native_mask=old;}
''')
(out/'main.c').write_text('''#define I960_GENERAL_HEAP 1
#define I960_HEAP_TEST 0
#define HEAP_NATIVE 1
#include "general_heap.c"
unsigned int _ISR_Nest_level;
void*memset(void*p,int c,size_t n){unsigned char*q=p;while(n--)*q++=c;return p;}
void*memcpy(void*p,const void*q,size_t n){unsigned char*d=p;const unsigned char*s=q;while(n--)*d++=*s++;return p;}
static void quit(unsigned int code){__asm__ volatile("int $0x80"::"a"(1),"b"(code):"memory");for(;;){}}
#define CHECK(x) do{if(!(x))quit(__LINE__);}while(0)
void _start(void){unsigned int i,t,old;unsigned char*p;void*saved;void*slots[64];
 CHECK(sizeof(void*)==4);CHECK(!resident_malloc(1));CHECK(!resident_heap_init());CHECK(resident_heap_valid()&&selftest);
 p=resident_malloc(RESIDENT_HEAP_BYTES-64);CHECK(p&&resident_heap_valid());
 CHECK(!resident_malloc(1));CHECK(!resident_free(p)&&resident_heap_valid());
 for(i=0;i<64;i++){slots[i]=resident_malloc(1);CHECK(slots[i]&&!((unsigned int)slots[i]&15));}
 CHECK(!resident_malloc(1));CHECK(!resident_realloc(slots[0],2));
 for(i=0;i<64;i++)CHECK(!resident_free(slots[i]));
 p=resident_realloc(0,100);CHECK(p);memset(p,0x71,100);
 p=resident_realloc(p,20);CHECK(p);for(i=0;i<20;i++)CHECK(p[i]==0x71);
 CHECK(!resident_realloc(p,0)&&!resident_free(0));
 for(t=1;t<=1000;t++){resident_heap_step(0,t);resident_heap_step(1,t);}
 resident_heap_drain(0);resident_heap_drain(1);CHECK(!live_bytes&&allocations==frees&&resident_heap_valid());
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
 quit(0);
}
''')
sources=[a.rtems/'cpukit/score/src'/n for n in ['heap.c','heapallocate.c','heapfree.c']];inputs+=sources
cmd=['gcc','-m32','-nostdlib','-ffreestanding','-fno-builtin','-fno-pie','-no-pie','-fno-stack-protector','-O1','-I'+str(inc),'-I'+str(root),'-I'+str(out),str(out/'main.c'),*map(str,sources),'-o',str(out/'heap-test')]
subprocess.run(cmd,check=True);subprocess.run([str(out/'heap-test')],check=True)
(out/'result.json').write_text(json.dumps(dict(actual_rtems_sources={str(p.relative_to(a.rtems)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},pointer_bits=32,live_slot_limit=64,empty_free_list_checked=True,realloc_shrink_and_oom_preserve=True,worker_iterations=2000,redzone_mutations=32,free_list_pointer_bit_mutations=32,alignment_offset_bit_mutations=32,null_free_list_link_rejected=True,guard_failure_retains_allocations=True,passed=True),indent=2)+'\n')
print('Actual RTEMS 4.6.6 allocator, 32-bit wrapper: startup/exhaustion/coalescing, 2000 worker iterations, ISR refusal, 32 redzone, 32 offset and 32 pointer corruptions passed')

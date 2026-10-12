#!/usr/bin/env python3
"""Two native threads exercise the actual target ownership/proof code."""
from pathlib import Path
import os,subprocess,tempfile
r=Path(__file__).resolve().parent
source=r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdio.h>
#include <pthread.h>
#include <time.h>
#include <stdatomic.h>
static unsigned char memory[8*1048576+128] __attribute__((aligned(16)));
#define UPLOAD_GUARD_LO ((unsigned long)memory)
#define UPLOAD_NATIVE 1
#define I960_RESIDENT_UPLOAD 1
#define I960_DOOM_HEAP 1
#define I960_DOOM_SHARED 1
static _Thread_local unsigned int identity;
static pthread_mutex_t mutex;
static atomic_uint halted;
static unsigned int current(void){return identity;}
static int obtain(unsigned int wait){unsigned int i;struct timespec d={0,1000000};
 for(i=0;i<(wait?20:1);i++){if(!pthread_mutex_trylock(&mutex))return 1;if(wait)nanosleep(&d,0);}return 0;}
static void release(void){assert(!pthread_mutex_unlock(&mutex));}
void doom_shared_init(void){pthread_mutexattr_t a;assert(!pthread_mutexattr_init(&a));assert(!pthread_mutexattr_settype(&a,PTHREAD_MUTEX_RECURSIVE));assert(!pthread_mutex_init(&mutex,&a));assert(!pthread_mutexattr_destroy(&a));}
void doom_shared_yield(void){struct timespec d={0,10000000};nanosleep(&d,0);}
#include "upload.c"
#include "doom_heap_shared.c"
#include "doom_heap_proof.c"
static void*peer(void*p){(void)p;identity=1;while(!atomic_load(&halted)){doom_shared_peer_step();doom_shared_yield();}return 0;}
int main(void){pthread_t task;unsigned int i;identity=2;doom_shared_init();assert(upload_init());
 /* No ISR/unregistered admission and no recursive lock. */
 identity=0;assert(!doom_shared_enter((void*)1));identity=2;
 assert(doom_shared_enter((void*)1));assert(!doom_shared_enter((void*)1));doom_shared_leave((void*)1);
 assert(!pthread_create(&task,0,peer,0));assert(!doom_arena_proof(&app_arena));
 assert(phase==4);
 /* Allocation namespaces refuse another owner's pointer, preserving both. */
 assert(!doom_heap_free(&heap,peer_buffer));assert(heap.error==DH_INVALID);
 atomic_store(&halted,1);assert(!pthread_join(task,0));
 assert(peer_checks&&wrong_owner_checks&&peer_heap.blocks==1&&heap.blocks==1);
 assert(!doom_shared_finish()); /* no drain authority yet */
 identity=3;doom_shared_quiesce(1);assert(upload_finish());
 for(i=0;i<ARENA_SLOTS;i++)assert(!app_arena.slot[i].span);
 /* Even after quiescence, a stale worker cannot allocate or force release. */
 identity=2;assert(!doom_shared_enter((void*)1));
 puts("PASS shared arena: concurrent owners, ISR/wrong task/recursive refusal, separate namespaces, retained buffers, post-join drain, stale task refusal");
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.c').write_text(source)
 (p/'upload_native.h').write_text('''#define R(a) (*(unsigned int*)(unsigned long)(a))
static unsigned int upload_stopping(void){return atomic_load(&halted);}
static unsigned int upload_time(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (unsigned int)(t.tv_sec*100+t.tv_nsec/10000000);}
static void barrier(void){}
static int sync_code(void*p,unsigned int n){return 1;}
static void exclusive_abort(void){assert(0);}
unsigned int upload_protect_step(void){return 1;}
unsigned int upload_protect_finish(void){return 1;}
''')
 core=r.parents[1]/'loader/segmented';runtime=r.parents[1]/'game/doom/runtime'
 subprocess.run(['cc','-std=c11','-pthread','-fsanitize='+os.environ.get('SANITIZERS','address,undefined'),'-g','-I'+str(p),'-I'+str(r),str(p/'test.c'),str(core/'arena.c'),str(core/'image.c'),str(runtime/'heap.c'),str(runtime/'libc.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)

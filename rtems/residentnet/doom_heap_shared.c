#ifdef I960_DOOM_SHARED
#include "../../game/doom/runtime/heap.h"
#include "doom_heap_shared.h"
#ifndef UPLOAD_NATIVE
#include <rtems/system.h>
#include <rtems/rtems/sem.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/options.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
extern volatile unsigned int switch_threads[2];
extern unsigned int upload_stopping(void),upload_time(void);
extern void exclusive_abort(void);
static rtems_id mutex_id;
static unsigned int controller_task;
static unsigned int current(void){
 if(_ISR_Nest_level||_Thread_Dispatch_disable_level)return 0;
 if((unsigned int)_Thread_Executing==switch_threads[0])return 1;
 if((unsigned int)_Thread_Executing==switch_threads[1])return 2;
 return (unsigned int)_Thread_Executing==controller_task?3:0;
}
static int obtain(unsigned int wait){return rtems_semaphore_obtain(mutex_id,wait?RTEMS_WAIT:RTEMS_NO_WAIT,2)==RTEMS_SUCCESSFUL;}
static void release(void){if(rtems_semaphore_release(mutex_id)!=RTEMS_SUCCESSFUL)exclusive_abort();}
void doom_shared_init(void){controller_task=(unsigned int)_Thread_Executing;if(rtems_semaphore_create(0x44415245,1,RTEMS_BINARY_SEMAPHORE|RTEMS_PRIORITY|RTEMS_INHERIT_PRIORITY,0,&mutex_id)!=RTEMS_SUCCESSFUL)exclusive_abort();}
void doom_shared_yield(void){if(rtems_task_wake_after(1)!=RTEMS_SUCCESSFUL)exclusive_abort();}
#endif
/* No IRQ allocation, recursive entry, implicit task handoff or forced unlock.
 * Only the controller, AFTER the runtime proves both IRQ/task drains, may use
 * the two allocation namespaces for final reclamation. */
#ifdef UPLOAD_NATIVE
#include <stdatomic.h>
static atomic_uint holder;
#else
static volatile unsigned int holder;
#endif
static unsigned int quiescent,enters[2],wait_max,hold_start,hold_max;
#ifdef UPLOAD_NATIVE
#include <stdatomic.h>
static atomic_uint phase;
#else
static volatile unsigned int phase;
#endif
static struct arena *shared_arena;
static struct doom_heap peer_heap;
static unsigned char *peer_buffer;
static unsigned int peer_bytes,peer_checks,peer_turn,wrong_owner_checks,timeout_checks,recursive_checks;
int doom_shared_enter(void *cookie){unsigned int role=(unsigned int)(unsigned long)cookie,c=current(),start=upload_time(),elapsed;
 if(role>1||!c||(!quiescent&&c!=role+1)||(quiescent&&c!=3))return 0;
 if(!obtain(!quiescent))return 0;
 if(holder){release();return 0;}holder=c;hold_start=upload_time();enters[role]++;
 elapsed=upload_time()-start;if(elapsed>wait_max)wait_max=elapsed;return 1;
}
void doom_shared_leave(void *cookie){unsigned int elapsed=upload_time()-hold_start;(void)cookie;
 if(!holder||holder!=current()){exclusive_abort();return;}
 if(elapsed>hold_max)hold_max=elapsed;holder=0;release();
}
void doom_shared_quiesce(unsigned int drained){if(current()!=3||!drained||holder){exclusive_abort();return;}quiescent=1;}
unsigned doom_shared_application_owner(void){if(current()!=2||quiescent||holder==2)return 0;
#ifndef UPLOAD_NATIVE
 unsigned pc=0;__asm__ volatile("modpc 0,0,%0":"+r"(pc)::"memory");
 return ((pc>>16)&31)==20; /* read-only PC query; established runnable priority */
#else
 return 1;
#endif
}
static int peer_progress(void*p){(void)p;return !upload_stopping();}
void doom_shared_wait(unsigned int wanted){unsigned int start=upload_time();
 while(phase!=wanted){if(upload_stopping()||upload_time()-start>200){exclusive_abort();return;}doom_shared_yield();}
}
static struct doom_heap *owner_heap;
void doom_shared_owner(struct doom_heap*h){owner_heap=h;}
void doom_shared_start(struct arena*a){shared_arena=a;phase=1;doom_shared_wait(2);
 if(!doom_shared_enter((void*)1)){exclusive_abort();return;}
 if(doom_shared_enter((void*)1)){exclusive_abort();return;}recursive_checks++;doom_shared_leave((void*)1);
 phase=5;doom_shared_wait(6);
 if(doom_shared_enter((void*)1)){exclusive_abort();return;}timeout_checks++;
 doom_shared_wait(7);
}
void doom_shared_resize(void){phase=3;doom_shared_wait(4);}
void doom_shared_peer_step(void){unsigned int i,off;unsigned char*p;
 struct doom_heap_hooks hooks={doom_shared_enter,doom_shared_leave,peer_progress,0};
 if(!phase||upload_stopping())return;
 if(phase==1){
  if(!doom_heap_init(&peer_heap,shared_arena,&hooks)){exclusive_abort();return;}
  peer_buffer=doom_heap_calloc(&peer_heap,1,65536);if(!peer_buffer){exclusive_abort();return;}
  peer_bytes=65536;for(i=0;i<peer_bytes;i++)if(peer_buffer[i]){exclusive_abort();return;}
  for(i=0;i<peer_bytes;i++)peer_buffer[i]=(unsigned char)(i^0x5a);phase=2;
 }else if(phase==5){
  if(!doom_shared_enter(0)){exclusive_abort();return;}phase=6;
  /* This profile has no registered idle IRQ owner. Keep the holder
   * runnable while the waiter blocks; timer IRQs remain enabled. */
  i=upload_time();while(upload_time()-i<5){}
  doom_shared_leave(0);phase=7;
 }else if(phase==3){
  p=doom_heap_realloc(&peer_heap,peer_buffer,98304);if(!p){exclusive_abort();return;}peer_buffer=p;
  for(i=0;i<peer_bytes;i++)if(p[i]!=(unsigned char)(i^0x5a)){exclusive_abort();return;}
  peer_bytes=98304;for(i=65536;i<peer_bytes;i++)p[i]=(unsigned char)(i^0x5a);phase=4;
 }
 /* Audit a pinned, privately owned buffer while the OTHER task uses the same
  * allocator metadata. Payload work does not hold the shared task mutex. */
 if(!doom_shared_enter(0)){exclusive_abort();return;}
 if(!arena_valid(shared_arena)){exclusive_abort();return;}
 doom_shared_leave(0);
 off=(peer_turn++%96u)*1024u;if(off>=peer_bytes)off=0;
 for(i=off;i<off+1024;i++)if(peer_buffer[i]!=(unsigned char)(i^0x5a)){exclusive_abort();return;}

 /* Wrong task cannot enter the libc owner's namespace, even though it is a
  * legitimate arena user itself. */
 if(doom_shared_enter((void*)1)||doom_heap_malloc(owner_heap,16)||doom_heap_calloc(owner_heap,~0u,2)||doom_heap_free(owner_heap,peer_buffer)){exclusive_abort();return;}
 if(!doom_shared_enter(0)){exclusive_abort();return;}peer_checks++;wrong_owner_checks++;doom_shared_leave(0);
}
unsigned int doom_shared_finish(void){unsigned int i;
 if(!quiescent||phase!=4||!peer_checks||!wrong_owner_checks||timeout_checks!=1||recursive_checks!=1)return 0;
 for(i=0;i<peer_bytes;i++)if(peer_buffer[i]!=(unsigned char)(i^0x5a))return 0;
 if(!doom_heap_stop(&peer_heap)||!doom_heap_drain(&peer_heap))return 0;
 return !peer_heap.blocks&&!peer_heap.busy&&!peer_heap.fault&&!holder;
}
unsigned int doom_shared_report(unsigned int index){static unsigned int frozen[10];
 if(!index){if(!doom_shared_enter((void*)1)){exclusive_abort();return ~0u;}frozen[0]=0x53484152;frozen[1]=phase;frozen[2]=peer_checks;frozen[3]=wrong_owner_checks;frozen[4]=enters[0];frozen[5]=enters[1];frozen[6]=wait_max;frozen[7]=hold_max;frozen[8]=timeout_checks;frozen[9]=recursive_checks;doom_shared_leave((void*)1);}
 return index<10?frozen[index]:~0u;
}
#endif

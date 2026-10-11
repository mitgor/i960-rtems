/* Explicit two-task references; cancellation never guesses that a pointer died. */
struct shared_block {void*p;unsigned int generation,owner,refs,pins,cancel,closed;};
static struct shared_block shared[8];
static unsigned int shared_generation,shared_cancelled,shared_testing;
static unsigned int shared_created,shared_retired,shared_cancels,shared_deferred,shared_rejects,shared_cycles,shared_checks,shared_tested;
static volatile unsigned int shared_phase,shared_handle,shared_since;
static unsigned char*shared_hold;
static unsigned int shared_bytes=256;
static unsigned int shared_bench_tick,shared_bench_oom;
#ifndef HEAP_NATIVE
#include <rtems/score/thread.h>
extern volatile unsigned int switch_threads[2];
static unsigned int shared_actor(unsigned int a){return a<2&&(shared_testing||(unsigned int)_Thread_Executing==switch_threads[a]);}
#else
static unsigned int shared_actor(unsigned int a){return a<2&&(shared_testing||a==native_actor);}
#endif
static unsigned int shared_valid(void){unsigned int i,j,k;if(shared_cancelled&~3u)return 0;
 for(i=0;i<8;i++){struct shared_block*s=&shared[i];
  if(!s->p){if(s->generation||s->owner||s->refs||s->pins||s->cancel||s->closed)return 0;continue;}
  k=find_block(s->p);
  if(k==HEAP_SLOTS||blocks[k].busy||!s->generation||s->generation>shared_generation||s->owner>1||!s->refs||(s->refs&~3u)||(s->pins&~s->refs)||(s->cancel&~s->refs)||(s->cancel&~shared_cancelled)||s->closed>1)return 0;
  for(j=0;j<i;j++)if(shared[j].p&&(shared[j].p==s->p||shared[j].generation==s->generation))return 0;
 }return 1;
}
static unsigned int shared_protected(void*p){unsigned int i;for(i=0;i<8;i++)if(p&&shared[i].p==p)return 1;return 0;}
static struct shared_block*shared_lookup(unsigned int h){struct shared_block*s=&shared[h&7];return h&&s->p&&s->generation==(h>>3)?s:0;}
static unsigned int shared_bad(void){shared_rejects++;return 1;}
unsigned int resident_shared_new(unsigned int a,unsigned int n){unsigned int v,i,h=0;void*p;
 if(!enter_op(&v,5))return 0;
 if(!shared_actor(a)||(shared_cancelled&(1u<<a))||shared_generation==0x1fffffff){shared_bad();goto out;}
 for(i=0;i<8&&shared[i].p;i++);if(i==8){shared_bad();goto out;}
 p=allocate(n);if(!p)goto out;
 shared[i].p=p;shared[i].generation=++shared_generation;shared[i].owner=a;shared[i].refs=1u<<a;
 h=(shared_generation<<3)|i;shared_created++;
out:unlock_heap(v);return h;
}
unsigned int resident_shared_acquire(unsigned int h,unsigned int a){unsigned int v,rc=0;struct shared_block*s;
 if(!enter_op(&v,5))return 1;s=shared_lookup(h);
 if(!shared_actor(a)||!s||s->closed||(shared_cancelled&(1u<<a))||(s->refs&(1u<<a))){rc=shared_bad();goto out;}
 s->refs|=1u<<a;
out:unlock_heap(v);return rc;
}
void*resident_shared_pin(unsigned int h,unsigned int a){unsigned int v;void*p=0;struct shared_block*s;
 if(!enter_op(&v,5))return 0;s=shared_lookup(h);
 if(!shared_actor(a)||!s||!(s->refs&(1u<<a))||(s->pins&(1u<<a))||(shared_cancelled&(1u<<a))){shared_bad();goto out;}
 s->pins|=1u<<a;p=s->p;
out:unlock_heap(v);return p;
}
unsigned int resident_shared_unpin(unsigned int h,unsigned int a){unsigned int v,rc=0;struct shared_block*s;
 if(!enter_op(&v,5))return 1;s=shared_lookup(h);
 if(!shared_actor(a)||!s||!(s->pins&(1u<<a)))rc=shared_bad();else s->pins&=~(1u<<a);
 unlock_heap(v);return rc;
}
unsigned int resident_shared_cancel(unsigned int a){unsigned int v,i;
 if(!enter_op(&v,6))return 1;
 if(a>=2){shared_bad();unlock_heap(v);return 1;}
 shared_cancelled|=1u<<a;shared_cancels++;
 for(i=0;i<8;i++)if(shared[i].p){if(shared[i].owner==a)shared[i].closed=1;shared[i].cancel|=shared[i].refs&(1u<<a);}
 unlock_heap(v);return 0;
}
unsigned int resident_shared_ack(unsigned int h,unsigned int a){unsigned int v,rc=0;struct shared_block*s;
 if(!enter_op(&v,6))return 1;s=shared_lookup(h);
 if(!shared_actor(a)||!s||!(s->cancel&(1u<<a))||!(s->refs&(1u<<a))){rc=shared_bad();goto out;}
 if(s->pins&(1u<<a)){shared_deferred++;rc=2;goto out;}
 s->refs&=~(1u<<a);s->cancel&=~(1u<<a);
 if(!s->refs){if(release_raw(s->p))poison(9);memset(s,0,sizeof(*s));shared_retired++;}
out:unlock_heap(v);return rc;
}
unsigned int resident_shared_resume(unsigned int a){unsigned int v,i,rc=0;
 if(!enter_op(&v,6))return 1;
 if(!shared_actor(a)){rc=shared_bad();goto out;}
 for(i=0;i<8;i++)if(shared[i].p&&(shared[i].refs&(1u<<a))){rc=shared_bad();goto out;}
 shared_cancelled&=~(1u<<a);
out:unlock_heap(v);return rc;
}
#define SHCHECK(x) do{if(!(x))poison(10);}while(0)
static unsigned int shared_selftest(void){unsigned int h,old,i,v;unsigned char*p;void*q;
 shared_testing=1;
 for(i=0;i<32;i++){v=lock_heap();timing_op=7;unlock_heap(v);}
 q=resident_calloc(1,RESIDENT_HEAP_BYTES-256);SHCHECK(q);SHCHECK(!resident_free(q));
 q=resident_malloc(32768);SHCHECK(q);memset(q,0x73,32768);q=resident_realloc(q,32768);SHCHECK(q);
 for(i=0;i<32768;i++)SHCHECK(((unsigned char*)q)[i]==0x73);SHCHECK(!resident_free(q));
 #ifdef I960_QUEUE_RECLAIM
 shared_bytes=81920;
#endif
 h=resident_shared_new(0,shared_bytes);SHCHECK(h);SHCHECK(!resident_shared_acquire(h,1));
 SHCHECK(resident_shared_acquire(h,1));p=resident_shared_pin(h,1);SHCHECK(p);memset(p,0x6d,shared_bytes);old=frees;
 SHCHECK(!resident_shared_cancel(0));SHCHECK(!resident_shared_ack(h,0));
 SHCHECK(resident_free(p)&&!resident_realloc(p,512)&&frees==old);
 SHCHECK(!resident_shared_cancel(1)&&resident_shared_ack(h,1)==2&&frees==old);
 SHCHECK(!resident_shared_resume(0)&&resident_shared_resume(1));
 for(i=0;i<shared_bytes;i++)SHCHECK(p[i]==0x6d);
 SHCHECK(!resident_shared_unpin(h,1)&&!resident_shared_ack(h,1)&&frees==old+1);
 SHCHECK(!resident_shared_pin(h,1)&&resident_shared_ack(h,1));SHCHECK(!resident_shared_resume(1));
 SHCHECK(!live_bytes&&allocations==frees);shared_tested=1;shared_testing=0;return 0;
}
static void shared_worker(unsigned int a,unsigned int tick){unsigned int i;unsigned char*p;
 if(!a&&tick-shared_bench_tick>=1000){void*q,*old;shared_bench_tick=tick;
  /* A fragmented general heap may refuse these deliberately large requests.
   * Realloc refusal must preserve the old block, not poison a healthy heap. */
  q=resident_calloc(1,57344);
  if(q){for(i=0;i<57344;i++)SHCHECK(!((unsigned char*)q)[i]);SHCHECK(!resident_free(q));}
  else shared_bench_oom++;
  q=resident_malloc(30720);
  if(q){memset(q,0x71,30720);old=q;q=resident_realloc(q,30720);
   if(!q){shared_bench_oom++;q=old;}
   for(i=0;i<30720;i++)SHCHECK(((unsigned char*)q)[i]==0x71);SHCHECK(!resident_free(q));
  }else shared_bench_oom++;
 }
 if(!a&&shared_phase==0){
#ifdef I960_QUEUE_RECLAIM
 shared_bytes=(shared_cycles&31)?256:81920;
#endif
 shared_handle=resident_shared_new(0,shared_bytes);SHCHECK(shared_handle);p=resident_shared_pin(shared_handle,0);SHCHECK(p);memset(p,0x6d,shared_bytes);SHCHECK(!resident_shared_unpin(shared_handle,0));shared_phase=1;}
 else if(a==1&&shared_phase==1){SHCHECK(!resident_shared_acquire(shared_handle,1));shared_hold=resident_shared_pin(shared_handle,1);SHCHECK(shared_hold);shared_since=tick;shared_phase=2;}
 else if(!a&&shared_phase==2){
  SHCHECK(!resident_shared_cancel(0)&&!resident_shared_ack(shared_handle,0));
  SHCHECK(resident_shared_acquire(shared_handle,1)); /* wrong running task */
  SHCHECK(resident_free(shared_hold)&&!resident_realloc(shared_hold,512));
  SHCHECK(!resident_shared_cancel(1));shared_phase=3;
 }else if(a==1&&shared_phase==3){
  for(i=0;i<shared_bytes;i++)SHCHECK(shared_hold[i]==0x6d);shared_checks++;
  SHCHECK(resident_shared_ack(shared_handle,1)==2);
  if(tick-shared_since>=8){SHCHECK(!resident_shared_unpin(shared_handle,1)&&!resident_shared_ack(shared_handle,1));shared_hold=0;SHCHECK(!resident_shared_resume(1));shared_phase=4;}
 }else if(!a&&shared_phase==4){SHCHECK(!resident_shared_pin(shared_handle,0));SHCHECK(!resident_shared_resume(0));shared_cycles++;shared_phase=0;}
}
static void shared_drain(unsigned int a){unsigned int i,h;
 SHCHECK(!resident_shared_cancel(a));
 if(a==1&&shared_hold){for(i=0;i<shared_bytes;i++)SHCHECK(shared_hold[i]==0x6d);SHCHECK(!resident_shared_unpin(shared_handle,1));shared_hold=0;}
 for(i=0;i<8;i++)if(shared[i].p&&(shared[i].refs&(1u<<a))){h=(shared[i].generation<<3)|i;SHCHECK(!resident_shared_ack(h,a));}
}
void resident_heap_diagnostics(unsigned int*w){unsigned int i,j;
 memset(w,0,256);w[0]=0x314c5348;w[1]=3;w[2]=4166700;w[3]=~0u;w[4]=timing_ready;
#ifdef I960_QUEUE_RECLAIM
 {extern void resident_net_irq_counts(unsigned int*);w[1]=4;resident_net_irq_counts(w+3);}
#endif
 w[5]=irq_samples;w[6]=irq_max_gap;w[7]=irq_late;w[8]=irq_elapsed[0];w[9]=irq_elapsed[1];w[10]=irq_min_gap;w[11]=41667;
 for(i=0;i<8;i++)for(j=0;j<4;j++)w[12+4*i+j]=timing_stats[i][j];
 w[44]=shared_created;w[45]=shared_retired;w[46]=shared_cancels;w[47]=shared_deferred;w[48]=shared_rejects;
 for(i=0;i<8;i++)if(shared[i].p){w[49]++;w[50]+=(shared[i].refs&1)+((shared[i].refs>>1)&1);w[51]+=(shared[i].pins&1)+((shared[i].pins>>1)&1);}
 w[52]=shared_cycles;w[53]=shared_checks;w[54]=heap_error;w[55]=shared_tested;w[56]=shared_bench_oom;w[57]=copy_preemptions[0];w[58]=copy_preemptions[1];w[59]=shared_cancelled;
 w[60]=allocations;w[61]=frees;w[62]=live_bytes;w[63]=resident_heap_valid();
}

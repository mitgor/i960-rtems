#ifndef I960_PEER_YIELD_H
#define I960_PEER_YIELD_H
/* Task 0 only, after a complete service pass and outside locks/IRQ masking.
 * Yield (zero delay) never blocks the last ready worker or admits idle. */
static unsigned peer_last_tick,peer_max_gap,peer_passes;
#ifndef PEER_YIELD_ACTIVE
#define PEER_YIELD_ACTIVE() 1
#endif
unsigned peer_service_complete(unsigned now){
 if(peer_passes){unsigned gap=now-peer_last_tick;if(gap>peer_max_gap)peer_max_gap=gap;}
 peer_last_tick=now;peer_passes++;return PEER_YIELD_ACTIVE();
}
/* Ten words fit the existing audited mutable reserve. One writer per worker;
 * diagnostics are frozen only by the serialized control path. */
#ifndef PEER_COUNTER
#define PEER_COUNTER() (*(volatile unsigned*)0xff000304u)
#endif
static unsigned drain_record[10];
extern unsigned upload_time(void);
extern void resident_heap_drain(unsigned);
void peer_heap_drain(unsigned id){
 drain_record[id]=PEER_COUNTER();drain_record[4+id]=upload_time();
 /* Both workers have passed the existing STOP arrival barrier. No new work or
  * shared acquisition can start. Payloads remain pinned/private; allocator and
  * shared-reference mutations retain their own IRQ locks. Keep the worker's
  * registered ISR context usable through the scans, then mask before done and
  * suspend. The controller still waits for both task/IRQ continuations. */
#ifndef PEER_DRAIN_PRIORITY
#define PEER_DRAIN_PRIORITY(level) do{unsigned pc=(level)<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(pc)::"g0","memory");}while(0)
#endif
 PEER_DRAIN_PRIORITY(20);
 resident_heap_drain(id);
 PEER_DRAIN_PRIORITY(31);
 drain_record[2+id]=drain_record[id]-PEER_COUNTER();
 drain_record[6+id]=upload_time()-drain_record[4+id];drain_record[8+id]++;
}
void peer_drain_report(unsigned*w){unsigned i;
 for(i=0;i<64;i++)w[i]=0;
 w[0]=0x314e5244u;w[1]=2;w[2]=4166700;
 for(i=0;i<10;i++)w[3+i]=drain_record[i];
}
unsigned exclusive_peer_report(unsigned index){return index?peer_passes:peer_max_gap;}
#endif

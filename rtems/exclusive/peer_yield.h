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
unsigned exclusive_peer_report(unsigned index){return index?peer_passes:peer_max_gap;}
#endif

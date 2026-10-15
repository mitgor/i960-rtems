#!/usr/bin/env python3
"""Peer service-gap counter, wrap handling and placement outside service work."""
import subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
static unsigned active,clock_counter=1000000,clock_tick,priority=31;
#define PEER_DRAIN_PRIORITY(level) (priority=(level))
#define PEER_COUNTER() clock_counter
unsigned upload_time(void){return clock_tick;}
void resident_heap_drain(unsigned id){assert(priority==20);clock_counter-=250000+id;clock_tick+=6;}

#define PEER_YIELD_ACTIVE() active
#include "peer_yield.h"
int main(void){assert(!peer_service_complete(0xfffffffdu));active=1;assert(exclusive_peer_report(0)==0);
assert(peer_service_complete(1));assert(exclusive_peer_report(0)==4);
peer_service_complete(1);assert(exclusive_peer_report(0)==4);
peer_service_complete(11);assert(exclusive_peer_report(0)==10);
assert(exclusive_peer_report(1)==4);active=0;assert(!peer_service_complete(12));peer_heap_drain(0);peer_heap_drain(1);unsigned w[64];peer_drain_report(w);
assert(w[0]==0x314e5244&&w[1]==2&&w[5]==250000&&w[6]==250001);
assert(priority==31&&w[9]==6&&w[10]==6&&w[11]==1&&w[12]==1);
clock_counter=10;clock_tick=0xfffffffdu;peer_heap_drain(0);peer_drain_report(w);
assert(w[5]==250000&&w[9]==6&&priority==31);return 0;}
'''
with tempfile.TemporaryDirectory() as t:
 p=Path(t);(p/'test.c').write_text(code)
 subprocess.run(['cc','-Os','-fsanitize=address,undefined','-I'+str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
s=(here/'runtime.c').read_text();a=s.index('  progress[id]++;');b=s.index('\n mask();',a)
assert 'if(resident&&!id&&!stop)' in s[a:b] and 'rtems_task_wake_after(RTEMS_YIELD_PROCESSOR)' in s[a:b]
assert s.index('doom_shared_peer_step();')<a
print('PASS peer service telemetry: first sample, wrap, same tick, maximum; yield after complete service pass')

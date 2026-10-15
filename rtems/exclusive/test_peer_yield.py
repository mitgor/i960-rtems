#!/usr/bin/env python3
"""Peer service-gap counter, wrap handling and placement outside service work."""
import subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
static unsigned active;
#define PEER_YIELD_ACTIVE() active
#include "peer_yield.h"
int main(void){assert(!peer_service_complete(0xfffffffdu));active=1;assert(exclusive_peer_report(0)==0);
assert(peer_service_complete(1));assert(exclusive_peer_report(0)==4);
peer_service_complete(1);assert(exclusive_peer_report(0)==4);
peer_service_complete(11);assert(exclusive_peer_report(0)==10);
assert(exclusive_peer_report(1)==4);active=0;assert(!peer_service_complete(12));return 0;}
'''
with tempfile.TemporaryDirectory() as t:
 p=Path(t);(p/'test.c').write_text(code)
 subprocess.run(['cc','-Os','-fsanitize=address,undefined','-I'+str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
s=(here/'runtime.c').read_text();a=s.index('  progress[id]++;');b=s.index('\n mask();',a)
assert 'if(resident&&!id&&!stop)' in s[a:b] and 'rtems_task_wake_after(RTEMS_YIELD_PROCESSOR)' in s[a:b]
assert s.index('doom_shared_peer_step();')<a
print('PASS peer service telemetry: first sample, wrap, same tick, maximum; yield after complete service pass')

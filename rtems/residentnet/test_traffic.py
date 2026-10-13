#!/usr/bin/env python3
"""Exercise actual client scheduling without target or wall-clock waits."""
from unittest.mock import patch
import live
now=0.;starts=[]
def clock():return now
def sleep(n):
 global now
 assert n>=0;now+=n
def client(families=None):
 global now
 starts.append(now);now+=2
 return [dict(family=2,protocol='test')]
with patch.object(live.time,'monotonic',clock),patch.object(live.time,'sleep',sleep),patch.object(live,'client_round',client):
 result=live.clients(3,False,10)
 assert starts==[0,10,20] and [r['round'] for r in result]==[0,1,2]
 assert [r['completed_seconds'] for r in result]==[2,12,22]
 now=0;starts.clear();result=live.clients(3,False,1)
 assert starts==[0,2,4] # late rounds do not go backward or drop traffic
 now=0;starts.clear();result=live.clients(3,False,0)
 assert starts==[0,2,4]
with patch.object(live,'client_round',side_effect=RuntimeError('client failure')):
 try:live.clients(2)
 except RuntimeError:pass
 else:raise AssertionError('client failure swallowed')
print('Actual traffic scheduler: spaced rounds, overrun, original zero interval and propagated failure passed')
assert live.traffic_limits([],0)==(180000,60,60)
assert live.traffic_limits([],12)==(360000,60,60)
flags=['-DI960_DOOM_STARTUP','-DI960_DOOM_ENGINE','-DI960_WAD_BATCH']
assert live.traffic_limits(flags,12)==(540000,90,60)
for bad,owned in [(flags,10),(flags[:-1],12),(flags[:1],12)]:
 try:live.traffic_limits(bad,owned)
 except AssertionError:pass
 else:raise AssertionError('extended budget without startup profile accepted')
print('90-minute aggregate budget is restricted to the owned startup profile; older limits unchanged')

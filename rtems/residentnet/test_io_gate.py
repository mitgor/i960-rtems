#!/usr/bin/env python3
import threading,time
from io_gate import IOGate,release_policy

g=IOGate();order=[];normal_started=threading.Event();release_started=threading.Event()
def normal():
 normal_started.set()
 with g:order.append('audit')
def release():
 release_started.set()
 with g.release_priority():
  with g:order.append('release')
with g:
 with g:assert g.depth==2
 a=threading.Thread(target=normal);a.start();assert normal_started.wait(2)
 b=threading.Thread(target=release);b.start();assert release_started.wait(2)
 deadline=time.monotonic()+2
 while True:
  with g.condition:pending=g.pending
  if pending:break
  assert time.monotonic()<deadline;time.sleep(.001)
for t in (a,b):t.join(2);assert not t.is_alive()
assert order==['release','audit'] and g.owner is None and not g.pending
try:
 with g.release_priority():raise ValueError('fault')
except ValueError:pass
with g:assert g.depth==1
assert [release_policy('abba',x) for x in (99,100,199,200,299,300,399,400,499,500)]==[False,False,False,True,True,True,True,False,False,False]
assert all(release_policy('abba',x)!=release_policy('baab',x) for x in range(100,500))
print('PASS current audit completes, queued release precedes new audit, reentry, exception cleanup and bounded schedules')

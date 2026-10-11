#!/usr/bin/env python3
"""A busy begin cannot discard a TUN packet or retry uncertain completion."""
import errno
from pump import send_pending
calls=[]
frame=bytes(range(256))*5
attempt=0
def busy_then_accept(op,data):
 global attempt
 calls.append((op,data));attempt+=1
 if attempt<4:raise BlockingIOError(errno.EAGAIN,'busy')
pending=frame
for _ in range(3):
 pending=send_pending(busy_then_accept,pending)
 assert pending is frame
pending=send_pending(busy_then_accept,pending)
assert pending is None and calls==[(1,frame)]*4
assert send_pending(busy_then_accept,None) is None and len(calls)==4
for code in (errno.ETIMEDOUT,errno.EIO,errno.EPROTO,errno.ESHUTDOWN,errno.EBUSY):
 count=[0]
 def uncertain(op,data):
  count[0]+=1
  raise OSError(code,'uncertain or closed')
 try:send_pending(uncertain,frame)
 except OSError as exc:assert exc.errno==code and count==[1]
 else:raise AssertionError('uncertain transaction retried')
print('three busy replies preserve identical packet; success consumes once; five fatal errors are never retried')

"""Reentrant host-I/O gate with priority only for pending frame releases.
Current holders finish; neither frozen audit contents nor card ownership change.
"""
from contextlib import contextmanager
import threading

class IOGate:
 def __init__(self):
  self.condition=threading.Condition();self.owner=None;self.depth=0;self.pending=0;self.priority_mode=False
 def _enter(self,priority=False):
  me=threading.get_ident()
  with self.condition:
   if self.owner==me:self.depth+=1;return
   if priority:self.pending+=1
   try:
    while self.owner is not None or (self.pending and not priority):self.condition.wait()
    self.owner=me;self.depth=1
   finally:
    if priority:self.pending-=1
 def __enter__(self):self._enter();return self
 def __exit__(self,*args):
  with self.condition:
   assert self.owner==threading.get_ident() and self.depth>0
   self.depth-=1
   if not self.depth:self.owner=None;self.condition.notify_all()
 @contextmanager
 def release_priority(self,enabled=True):
  self._enter(enabled)
  try:yield self
  finally:self.__exit__()

def release_policy(schedule,g):
 if schedule in ('baseline','priority'):return schedule=='priority'
 assert schedule in ('abba','baab')
 if not 100<=g<500:return False
 return (schedule=='abba')==(1<=(g-100)//100<=2)

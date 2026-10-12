#!/usr/bin/env python3
"""Actual snapshot wrapper excludes Upload.io until a whole snapshot finishes."""
import ast,threading,time
from pathlib import Path
from unittest.mock import patch
from upload_client import Upload
root=Path(__file__).resolve().parent
tree=ast.parse((root/'live.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');snapshot=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='snapshot')
gate=threading.RLock();inside=threading.Event();release=threading.Event();entered_ioctl=threading.Event();errors=[]
def body():inside.set();assert release.wait(2);assert not entered_ioctl.is_set();return 42
ns=dict(io_gate=gate,snapshot_locked=body);exec(compile(ast.Module(body=[snapshot],type_ignores=[]),'actual-snapshot-wrapper','exec'),ns)
u=Upload(0,1,root,gate);u.record=lambda e:None
def ioctl(fd,cmd,raw,mutate):
 entered_ioctl.set();raw[12:16]=(1).to_bytes(4,'little')
def invoke(fn):
 try:fn()
 except BaseException as e:errors.append(e)
with patch('upload_client.fcntl.ioctl',ioctl):
 a=threading.Thread(target=invoke,args=(ns['snapshot'],));a.start();assert inside.wait(2)
 b=threading.Thread(target=invoke,args=(lambda:u.io(2),));b.start()
 assert not entered_ioctl.wait(.05);release.set();a.join(2);b.join(2)
 assert not a.is_alive() and not b.is_alive() and not errors and entered_ioctl.is_set()
print('PASS actual snapshot wrapper and upload client share a whole-snapshot exclusion gate')

class MaximumPrepare(Upload):
 def __init__(self,finish):self.calls=0;self.finish=finish
 def command(self,command):
  assert command==3;self.calls+=1;return [0,0,0,0,0,2 if self.calls==self.finish else 1]
x=MaximumPrepare(8224);assert x.prepare()[5]==2 and x.calls==8224
try:MaximumPrepare(8225).prepare();raise RuntimeError('unbounded preparation accepted')
except AssertionError:pass
print('PASS host preparation bound covers the full 8 MiB arena and terminates on non-completion')

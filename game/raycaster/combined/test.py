#!/usr/bin/env python3
"""Differential combined operation, rejection immutability and renderer state."""
import ctypes,struct,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;GAME=HERE.parent
sys.path.insert(0,str(GAME))
from combined.optimize import combined
from combined.model import Model,replace,request,cases
from callback.optimize import render_fast
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'queue.c').write_text(combined((GAME/'queue/queue.c').read_text()));(p/'ray.c').write_text(render_fast((GAME/'ray.c').read_text()))
 flags=['cc','-std=c99','-O2','-fno-builtin','-Wall','-Wextra','-Werror','-I'+str(GAME/'queue'),'-I'+str(GAME)]
 subprocess.run(flags+['-fsanitize=address,undefined',str(p/'ray.c'),str(p/'queue.c'),str(HERE/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
 subprocess.run(flags+['-shared','-fPIC',str(p/'ray.c'),str(p/'queue.c'),'-o',str(p/'queue.so')],check=True)
 lib=ctypes.CDLL(str(p/'queue.so'));lib.fq_request.argtypes=[ctypes.c_void_p]*4+[ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint]
 def fresh():return (ctypes.create_string_buffer(20),ctypes.create_string_buffer(lib.ray_size()),ctypes.create_string_buffer(10240),ctypes.create_string_buffer(64),Model())
 def step(ctx,data,seq):
  state,ray,slots,out,model=ctx
  assert lib.fq_request(state,ray,slots,ctypes.create_string_buffer(data),64,out,64,seq)==0
  assert out.raw==model.step(data,seq),(seq,data.hex())
  assert slots.raw==b''.join(model.slots),seq
 total=0;trajectories=[]
 for mode in [False,True]:
  ctx=fresh();frames=[]
  for seq,(label,data) in enumerate(cases(combined=mode),1):
   step(ctx,data,seq)
   if label in ('steady-publish','steady-combined'):frames.append(ctx[2].raw[64:4928])
  total+=seq;trajectories.append(frames)
 assert trajectories[0]==trajectories[1] and len(trajectories[0])==80
 # Every one-bit request mutation: model agreement, and all rejected requests
 # leave ownership, slot bytes AND renderer private state unchanged.
 rejected=0
 for bit in range(512):
  ctx=fresh();step(ctx,request(0),1);step(ctx,request(1,gen=1),2)
  before=tuple(x.raw for x in ctx[:3]);data=bytearray(replace());data[bit//8]^=1<<(bit%8)
  step(ctx,bytes(data),3)
  if struct.unpack_from('<I',ctx[3].raw,8)[0]:
   assert before==tuple(x.raw for x in ctx[:3]);rejected+=1
 print('PASS:',total,'differential requests; identical 80-frame trajectory; 512 request bit mutations;',rejected,'rejections preserve queue and renderer')

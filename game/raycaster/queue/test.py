#!/usr/bin/env python3
import subprocess,tempfile,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'callback'));from optimize import render_fast
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'ray.c').write_text(render_fast((HERE.parent/'ray.c').read_text()))
 subprocess.run(['cc','-std=c99','-O2','-fno-builtin','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I'+str(HERE),'-I'+str(HERE.parent),str(p/'ray.c'),str(HERE/'queue.c'),str(HERE/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
 # Differential C queue against independently serialized host ownership model.
 import ctypes
 from model import Model,cases
 subprocess.run(['cc','-std=c99','-O2','-fno-builtin','-shared','-fPIC','-I'+str(HERE),'-I'+str(HERE.parent),str(p/'ray.c'),str(HERE/'queue.c'),'-o',str(p/'queue.so')],check=True)
 lib=ctypes.CDLL(str(p/'queue.so'));lib.fq_request.argtypes=[ctypes.c_void_p]*4+[ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint]
 state=ctypes.create_string_buffer(20);ray=ctypes.create_string_buffer(lib.ray_size());slots=ctypes.create_string_buffer(10240);out=ctypes.create_string_buffer(64);model=Model()
 for seq,(label,data) in enumerate(cases(),1):
  assert lib.fq_request(state,ray,slots,ctypes.create_string_buffer(data),64,out,64,seq)==0
  assert out.raw==model.step(data,seq),(seq,label)
  assert slots.raw==b''.join(model.slots),(seq,label)
 print('PASS:',seq,'differential queue requests, responses and complete slot bytes')

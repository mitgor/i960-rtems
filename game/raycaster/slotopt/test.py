#!/usr/bin/env python3
import ctypes,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;GAME=HERE.parent
sys.path.insert(0,str(GAME))
from slotopt.optimize import header,diagnostic
from combined.optimize import combined
from callback.optimize import render_fast
from slotopt.model import Model,cases,bench
from combined.model import request
for mode in ('byte','hash','words'):
 # Reuse the full accepted combined mutation/state test with exact candidate
 # source substitution; test runtime and expected data are otherwise unchanged.
 for diagnostic_enabled in (False,True):
  s=(GAME/'combined/test.py').read_text().replace('from combined.optimize import combined','from combined.optimize import combined as original_combined\nfrom slotopt.optimize import header,diagnostic\ncombined=lambda s:diagnostic(original_combined(s))')
  needle="p=Path(d);(p/'queue.c')";assert s.count(needle)==1
  s=s.replace(needle,f"p=Path(d);(p/'queue.h').write_text(header((GAME/'queue/queue.h').read_text(),{mode!r}));(p/'queue.c')")
  if not diagnostic_enabled:s=s.replace('combined=lambda s:diagnostic(original_combined(s))','combined=original_combined')
  exec(compile(s,str(GAME/'combined/test.py'),'exec'),dict(__name__='__main__',__file__=str(GAME/'combined/test.py')))
 with tempfile.TemporaryDirectory() as d:
  p=Path(d);(p/'queue.h').write_text(header((GAME/'queue/queue.h').read_text(),mode));(p/'queue.c').write_text(diagnostic(combined((GAME/'queue/queue.c').read_text())));(p/'ray.c').write_text(render_fast((GAME/'ray.c').read_text()))
  flags=['cc','-O2','-fno-builtin','-Wall','-Wextra','-Werror','-I'+str(p),'-I'+str(GAME)]
  subprocess.run(flags+['-fsanitize=address,undefined',str(HERE/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
  subprocess.run(flags+['-shared','-fPIC',str(p/'queue.c'),str(p/'ray.c'),'-o',str(p/'q.so')],check=True)
  lib=ctypes.CDLL(str(p/'q.so'));lib.fq_request.argtypes=[ctypes.c_void_p]*4+[ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_uint]
  for suite in ('bench','stress'):
   state=ctypes.create_string_buffer(20);ray=ctypes.create_string_buffer(lib.ray_size());slots=ctypes.create_string_buffer(10240);out=ctypes.create_string_buffer(64);model=Model()
   for seq,(label,data) in enumerate(cases(suite=suite),1):
    before=(state.raw,ray.raw,slots.raw)
    assert lib.fq_request(state,ray,slots,ctypes.create_string_buffer(data),64,out,64,seq)==0
    assert out.raw==model.step(data,seq),(mode,label,seq)
    assert slots.raw==b''.join(model.slots)
    if label.startswith('bench-'):assert before==(state.raw,ray.raw,slots.raw)
   print('PASS',mode,suite,seq,'exact replies and slots')

  rejected=0
  for bit in range(512):
   state=ctypes.create_string_buffer(20);ray=ctypes.create_string_buffer(lib.ray_size());slots=ctypes.create_string_buffer(10240);out=ctypes.create_string_buffer(64);model=Model()
   for seq,data in enumerate([request(0),request(1,gen=1)],1):
    assert not lib.fq_request(state,ray,slots,ctypes.create_string_buffer(data),64,out,64,seq)
    assert out.raw==model.step(data,seq)
   before=(state.raw,ray.raw,slots.raw);data=bytearray(bench(count=1));data[bit//8]^=1<<(bit%8)
   assert not lib.fq_request(state,ray,slots,ctypes.create_string_buffer(bytes(data)),64,out,64,3)
   assert out.raw==model.step(bytes(data),3)
   assert before==(state.raw,ray.raw,slots.raw)
  print('PASS',mode,'512 diagnostic request mutations preserve all private state')

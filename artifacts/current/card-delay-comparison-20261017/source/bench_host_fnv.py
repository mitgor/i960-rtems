#!/usr/bin/env python3
import ctypes,hashlib,json,statistics,subprocess,sys,time
from pathlib import Path
source,frame,out=map(Path,sys.argv[1:])
lib=out.with_suffix('.so')
subprocess.run(['cc','-O2','-shared','-fPIC',str(source),'-o',str(lib)],check=True)
f=ctypes.CDLL(str(lib.resolve())).frame_fnv
f.argtypes=(ctypes.c_void_p,ctypes.c_size_t);f.restype=ctypes.c_uint32
def py(b):
 h=2166136261
 for v in b:h=((h^v)*16777619)&0xffffffff
 return h
payload=frame.read_bytes()
vectors=[b'',b'a',bytes(range(256)),bytes(65536),b'\xff'*65536,payload,
         bytes((i*17+13)%251 for i in range(524288))]
for b in vectors:
 buf=ctypes.create_string_buffer(b);assert f(buf,len(b))==py(b)
buf=ctypes.create_string_buffer(payload)
def bench(call,n):
 a=[]
 for _ in range(n):
  t=time.perf_counter_ns();call();a.append((time.perf_counter_ns()-t)/1e6)
 return dict(iterations=n,mean_ms=statistics.mean(a),p50_ms=statistics.median(a),min_ms=min(a),max_ms=max(a))
r=dict(bytes=len(payload),payload_sha256=hashlib.sha256(payload).hexdigest(),
       fnv=f'0x{py(payload):08x}',verified_vectors=len(vectors),
       compiler=subprocess.check_output(['cc','--version'],text=True).splitlines()[0],
       python=bench(lambda:py(payload),30),native=bench(lambda:f(buf,len(payload)),2000),
       limitation='Host-only microbenchmark; not integrated into the card runner')
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

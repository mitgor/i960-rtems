#!/usr/bin/env python3
"""Independent Python fixed-point oracle, boundary corpus and deterministic fuzz."""
import ctypes,itertools,json,random,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
HEADER='typedef int fixed_t; typedef struct {int x,y,dx,dy,bbox[2][4]; unsigned short children[2];} node_t;\n'
def s32(v): return ((v+2**31)%2**32)-2**31
def oracle(v):
 x,y,nx,ny,ndx,ndy=v
 if not ndx:return int(ndy>0) if x<=nx else int(ndy<0)
 if not ndy:return int(ndx<0) if y<=ny else int(ndx>0)
 dx=s32(x-nx);dy=s32(y-ny)
 if (ndy^ndx^dx^dy)&0x80000000:return int(bool((ndy^dx)&0x80000000))
 left=s32(((ndy//65536)*dx)//65536)
 right=s32((dy*(ndx//65536))//65536)
 return int(right>=left)
def vectors(count=1000000):
 edge=[-2147483648,-2147483647,-65537,-65536,-1,0,1,65535,65536,2147483647]
 for x,n,d in itertools.product(edge,repeat=3):
  yield (x,0,n,0,0,d)
  yield (0,x,0,n,d,0)
 rng=random.Random(960)
 for i in range(count):yield tuple(rng.randrange(-2**31,2**31) for _ in range(6))
if __name__=='__main__':
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'r_local.h').write_text(HEADER)
  subprocess.run(['cc','-O2','-shared','-fPIC','-I'+str(p),str(HERE/'point.c'),'-o',str(p/'point.so')],check=True)
  class Node(ctypes.Structure):_fields_=[('v',ctypes.c_int*12),('children',ctypes.c_ushort*2)]
  lib=ctypes.CDLL(str(p/'point.so'));fn=lib.R_PointOnSide;fn.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.POINTER(Node)]
  n=Node();count=0
  for v in vectors():
   x,y,*rest=v;n.v[:4]=rest;actual=fn(x,y,ctypes.byref(n));assert actual==oracle(v),(v,actual,oracle(v));count+=1
  print(json.dumps(dict(passed=True,cases=count,oracle='32-bit wrapped deltas, arithmetic floor shifts, exact signed products')))

 # Compile the same helper under UBSan and run a separate edge/random corpus.
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'r_local.h').write_text(HEADER)
  cases=list(vectors(10000))
  source=HEADER+'extern int R_PointOnSide(int,int,node_t*);\nstruct row{int v[6];int expected;};\nstatic const struct row rows[]={\n'
  for v in cases:source+='{ {'+','.join(str(x) if x!=-2147483648 else '(-2147483647-1)' for x in v)+'},'+str(oracle(v))+'},\n'
  source+='};\nint main(void){unsigned i;node_t n={0};for(i=0;i<sizeof(rows)/sizeof(rows[0]);i++){const int *v=rows[i].v;n.x=v[2];n.y=v[3];n.dx=v[4];n.dy=v[5];if(R_PointOnSide(v[0],v[1],&n)!=rows[i].expected)return 1;}return 0;}\n'
  (p/'main.c').write_text(source)
  subprocess.run(['cc','-O2','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(p),str(HERE/'point.c'),str(p/'main.c'),'-o',str(p/'check')],check=True)
  subprocess.run([str(p/'check')],check=True)
  print(json.dumps(dict(ubsan_passed=True,cases=len(cases))))

 # Option regression: C columns and this candidate are independently opt-in.
 import sys
 root=HERE.parents[2]
 for path,base,cut in [('game/doom/build.py',['--work','/tmp/unused','--archive','/tmp/unused','--target','i960'],'assert not a.platform_runtime'),('game/doom/play/build.py',['--work','/tmp/unused'],'if a.input_trace:')]:
  source=(root/path).read_text().split(cut,1)[0]
  for args in ([],['--fast-point-side'],['--fast-columns']):
   sys.argv=['build.py']+base+args;env={};exec(source,env)
   assert env['a'].fast_point_side==('--fast-point-side' in args)
   assert env['a'].fast_columns==('--fast-columns' in args)
 print('PASS point-side and C columns remain independently opt-in in both builders')

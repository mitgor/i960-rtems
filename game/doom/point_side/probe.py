#!/usr/bin/env python3
"""Prepare bounded card differential probes using actual engine object text."""
import argparse,hashlib,json,random,subprocess
from pathlib import Path
from test import HEADER,oracle,vectors
p=argparse.ArgumentParser();p.add_argument('workspace',type=Path);a=p.parse_args();w=a.workspace.resolve();out=w/'probe';out.mkdir(exist_ok=True)
cross='/home/mit/i960/tools/bin/i960-coff-';cc=cross+'gcc'
rng=random.Random(960)
axis=list(vectors(0));vv=[axis[i] for i in sorted(rng.sample(range(len(axis)),256))]+list(vectors(768))[2000:]
# Include exact historical failing root and horizontal paths as well as ties.
vv[:3]=[(0,-160*65536,1792*65536,544*65536,0,-128*65536),(0,600*65536,2064*65536,272*65536,128*65536,0),(1792*65536,0,1792*65536,0,0,-128*65536)]
assert len(vv)==1024
rows=[dict(values=v,expected=oracle(v)) for v in vv]
text=HEADER+'extern int R_PointOnSide(int,int,node_t*);\nextern int legacy_side(int,int,node_t*);\nstruct vector {int x,y,nx,ny,dx,dy;unsigned expected;};\nextern const struct vector vectors[1024];\nunsigned payload(unsigned batch){unsigned i;node_t n;const struct vector *v;if(batch>=32)return 0xbad0;for(i=batch*32;i<(batch+1)*32;i++){v=vectors+i;n.x=v->nx;n.y=v->ny;n.dx=v->dx;n.dy=v->dy;if(R_PointOnSide(v->x,v->y,&n)!=v->expected)return 0x10000u+i;if(legacy_side(v->x,v->y,&n)!=v->expected)return 0x20000u+i;}return 32;}\nconst struct vector vectors[1024]={\n'
for row in rows:
 x,y,nx,ny,dx,dy=row['values'];text+='{%d,%d,%d,%d,%d,%d,%du},\n'%(x,y,nx,ny,dx,dy,row['expected'])
text+='};\n';(out/'entry.c').write_text(text)
subprocess.run([cc,'-std=gnu99','-mrp','-mold-align','-O0','-ffreestanding','-fno-builtin','-c',str(out/'entry.c'),'-o',str(out/'entry.o')],check=True)
subprocess.run([cross+'objcopy','--redefine-sym','_R_PointOnSide=_legacy_side',str(w/'build/engine-cross/i960/r_point_side.o'),str(out/'legacy.o')],check=True)
# Recompile only FixedMul and require exact object-text equality with the accepted engine.
base=w/'build/engine-cross/i960';candidate=w/'build-fast/engine-cross/i960/r_point_side.o'
(out/'math.c').write_text('int FixedMul(int a,int b){return ((long long)a*(long long)b)>>16;}\n')
subprocess.run([cc,'-std=gnu99','-Os','-mrp','-mold-align','-ffreestanding','-fno-builtin','-c',str(out/'math.c'),'-o',str(out/'math.o')],check=True)
for obj,dest in [(base/'m_fixed.o',out/'original-math.bin'),(out/'math.o',out/'math.bin')]:
 subprocess.run([cross+'objcopy','-j','.text','-O','binary',str(obj),str(dest)],check=True)
math=(out/'math.bin').read_bytes();assert (out/'original-math.bin').read_bytes()[:len(math)]==math
subprocess.run([cross+'ld','-T',str(w/'project/loader/runtime/payload.ld'),str(out/'entry.o'),str(candidate),str(out/'legacy.o'),str(out/'math.o'),'-o',str(out/'probe.elf')],check=True)
subprocess.run([cross+'objcopy','-O','binary',str(out/'probe.elf'),str(out/'probe.bin')],check=True)
with (out/'probe.dis').open('w') as f:subprocess.run([cross+'objdump','-dr',str(out/'probe.elf')],stdout=f,check=True)
assert (out/'probe.bin').stat().st_size<=65536
subprocess.run([cross+'objcopy','-j','.text','-O','binary',str(candidate),str(out/'candidate-text.bin')],check=True)
syms={row.split()[-1]:int(row.split()[0],16) for row in subprocess.check_output([cross+'nm',str(out/'probe.elf')],text=True).splitlines() if len(row.split())==3}
body=(out/'candidate-text.bin').read_bytes();offset=syms['_R_PointOnSide']-0xc0f2c000
assert (out/'probe.bin').read_bytes()[offset:offset+len(body)]==body, 'linked probe candidate differs from engine'
(out/'build.json').write_text(json.dumps(dict(vectors=rows,batches=32,per_batch=32,payload_bytes=(out/'probe.bin').stat().st_size,candidate_object_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),legacy_object_sha256=hashlib.sha256((base/'r_point_side.o').read_bytes()).hexdigest(),candidate_linked_directly=True,candidate_text_bytes=len(body),candidate_text_offset=offset,candidate_text_sha256=hashlib.sha256(body).hexdigest()),indent=2)+'\n')
print('Prepared 1024 exact target candidate/original/oracle comparisons in 32 bounded calls')

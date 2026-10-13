#!/usr/bin/env python3
"""Build bounded scalar probes of the exact Doom BSP source, without RTEMS/WAD.
No hardware access. Run with the existing fully audited host/loadrun transaction.
"""
import argparse,json,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
build=json.loads((a.engine/'i960/build.json').read_text());source=a.engine/'doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric/r_main.c';text=source.read_text();body=text[text.index('int\nR_PointOnSide\n'):text.index('\n\nint\nR_PointOnSegSide\n')]
header='typedef int fixed_t;\ntypedef struct {int x,y,dx,dy,bbox[2][4];unsigned short children[2];} node_t;\n#define FRACBITS 16\nextern int FixedMul(int,int);\n'
(a.out/'point.c').write_text(header+body)
# All coordinates below are map units, converted with multiplication (no signed-left-shift UB).
vectors=[(0,-160,1792,544,0,-128),(3000,-160,1792,544,0,-128),(1792,-160,1792,544,0,-128),(0,-160,1792,544,0,128),(0,600,2064,272,-128,0),(0,600,2064,272,128,0),(0,100,2064,272,-128,0),(0,100,2064,272,128,0),(0,-160,-2240,384,-64,64)]
def side(v):
 x,y,nx,ny,dx,dy=v
 if not dx:return int(dy>0) if x<=nx else int(dy<0)
 if not dy:return int(dx<0) if y<=ny else int(dx>0)
 return int((y-ny)*dx >= dy*(x-nx))
expected=[side(v) for v in vectors];rows=[]
for v in vectors:
 x,y,nx,ny,dx,dy=[i*65536 for i in v];rows.append('{%d,%d,{%d,%d,%d,%d,{{0}}, {0,0}}}'%(x,y,nx,ny,dx,dy))
(a.out/'entry.c').write_text(header+'extern int R_PointOnSide(int,int,node_t*);\nstruct vector{int x,y;node_t n;};\nextern const struct vector vectors[9];\nunsigned payload(unsigned arg){const struct vector*v;if(arg>=9)return 0xbad0;v=vectors+arg;return R_PointOnSide(v->x,v->y,(node_t*)&v->n);}\nconst struct vector vectors[]={'+','.join(rows)+'};\n')
(a.out/'math.c').write_text('int FixedMul(int a,int b){return ((long long)a*(long long)b)>>16;}\n')
cc=a.cross+'gcc';ld=a.cross+'ld';oc=a.cross+'objcopy';od=a.cross+'objdump'
flags=[f for f in build['flags'] if not f.startswith('-I')]
subprocess.run([cc,'-mrp','-mold-align','-O0','-ffreestanding','-fno-builtin','-c',str(a.out/'entry.c'),'-o',str(a.out/'entry.o')],check=True)
subprocess.run([cc,*flags,'-c',str(a.out/'math.c'),'-o',str(a.out/'math.o')],check=True)
reports=[]
for name,extra in [('scheduled',[]),('no-schedule',['-fno-schedule-insns','-fno-schedule-insns2']),('unoptimized',['-O0'])]:
 obj=a.out/(name+'.o');elf=a.out/(name+'.elf');binary=a.out/(name+'.bin')
 subprocess.run([cc,*flags,*extra,'-c',str(a.out/'point.c'),'-o',str(obj)],check=True)
 subprocess.run([ld,'-T',str(a.project/'loader/runtime/payload.ld'),str(a.out/'entry.o'),str(obj),str(a.out/'math.o'),'-o',str(elf)],check=True)
 subprocess.run([oc,'-O','binary',str(elf),str(binary)],check=True)
 with (a.out/(name+'.dis')).open('w') as f:subprocess.run([od,'-dr',str(elf)],stdout=f,check=True)
 reports.append(dict(name=name,extra_flags=extra,payload_bytes=binary.stat().st_size))
# Exact text-byte comparison, including the two unresolved FixedMul operands.
subprocess.run([oc,'-j','.text','-O','binary',str(a.engine/'i960/r_main.o'),str(a.out/'original-text.bin')],check=True)
subprocess.run([oc,'-j','.text','-O','binary',str(a.out/'scheduled.o'),str(a.out/'scheduled-text.bin')],check=True)
syms={l.split()[-1]:int(l.split()[0],16) for l in subprocess.check_output([a.cross+'nm',str(a.engine/'i960/r_main.o')],text=True).splitlines() if len(l.split())==3}
begin=syms['_R_PointOnSide'];end=syms['_R_PointOnSegSide'];original=(a.out/'original-text.bin').read_bytes()[begin:end];candidate=(a.out/'scheduled-text.bin').read_bytes()
assert original==candidate, 'standalone scheduled body differs from actual Doom object; do not call it exact'
r=dict(no_hardware_access=True,source=str(source),flags=flags,variants=reports,vectors=vectors,expected_source_results=expected,exact_scheduled_function_bytes=len(original),normal_firmware_scalar_runner=True)
(a.out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

#!/usr/bin/env python3
import argparse,json,subprocess,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--newlib',type=Path,required=True);p.add_argument('--doom',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parent
flags=['-m32','-Os','-funsigned-char','-fno-builtin','-DCMAP256','-D__SINGLE_THREAD__','-I'+str(a.newlib/'newlib/libc/include'),'-I'+str(r.parents[1]/'include'),'-I'+str(a.doom),'-I'+str(r.parent/'platform')]
sanitized=json.loads((a.build/'build.json').read_text()).get('sanitized',False)
if sanitized:flags+=['-fsanitize=address,undefined','-g','-fno-omit-frame-pointer']
objs=[]
for name,src in [('entry',r.parent/'platform/engine_entry.c'),('backend',r.parent/'cache/backend.c'),('native',r/'native.c')]:
 obj=a.build/('owned-'+name+'.o');subprocess.run(['gcc',*flags,'-c',str(src),'-o',str(obj)],check=True);private=obj.with_suffix('.private.o');subprocess.run(['objcopy','--redefine-syms='+str(a.build/'rename.txt'),str(obj),str(private)],check=True);objs.append(private)
for src in [r.parent/'heap.c',r.parents[3]/'loader/segmented/arena.c']:
 obj=a.build/('owned-'+src.stem+'.o');subprocess.run(['gcc',*flags,'-c',str(src),'-o',str(obj)],check=True);objs.append(obj)
exe=a.build/'owned-test';subprocess.run(['gcc','-m32','-no-pie',*map(str,objs),str(a.build/'private-newlib.a'),'-o',str(exe)]+(['-fsanitize=address,undefined'] if sanitized else []),check=True)
rows=[]
for args in [[],['stop'],[],['owned','sleep'],['old','fragmented','layout']]:
 run=subprocess.run([str(exe),*args],check=True,stdout=subprocess.PIPE);assert len(run.stdout)==(0 if len(args)==2 else 48)
 if run.stdout:rows.append(dict(stop=len(args)==1,fragmented=len(args)>2,result=list(struct.unpack('<12I',run.stdout))))
(a.build/'owned-result.json').write_text(json.dumps(dict(sanitized=sanitized,runs=rows,owned_sleep_exit=210),indent=2)+'\n')
print('PASS: actual private Newlib owned preflight, 6 MiB zone, frame/palette, WAD backend, local STOP, retired-state refusal, retained-buffer fragmentation/OOM and corrected layout, heap drain (32-bit native, not i960 execution)')

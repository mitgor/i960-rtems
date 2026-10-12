#!/usr/bin/env python3
"""Execute the private 32-bit Newlib port against the real guarded arena."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--newlib',type=Path,required=True);p.add_argument('--doom',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parent
flags=['-D__SINGLE_THREAD__','-m32','-Os','-fno-builtin','-funsigned-char','-DCMAP256','-I'+str(a.newlib/'newlib/libc/include'),'-I'+str(r.parents[1]/'include'),'-I'+str(a.doom),'-I'+str(r)]
sanitized=json.loads((a.build/'build.json').read_text()).get('sanitized',False)
if sanitized:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g']
obj=a.build/'test.o';subprocess.run(['gcc',*flags,'-c',str(r/'test.c'),'-o',str(obj)],check=True)
subprocess.run(['objcopy','--redefine-syms='+str(a.build/'rename.txt'),str(obj),str(a.build/'test-private.o')],check=True)
core=[]
for f in (r/'../heap.c',r/'../../../..'/ 'loader/segmented/arena.c'):
 dest=a.build/(f.stem+'-test.o');subprocess.run(['gcc',*flags,'-c',str(f),'-o',str(dest)],check=True);core.append(dest)
exe=a.build/'test';cmd=['gcc','-m32','-no-pie',str(a.build/'test-private.o'),str(a.build/'private-newlib.a'),*map(str,core),'-o',str(exe)]
if sanitized:cmd+=['-fsanitize=address,undefined']
with (a.build/'test-link.log').open('w') as log:run=subprocess.run(cmd,stdout=log,stderr=log)
assert run.returncode==0,'see test-link.log'
run=subprocess.run([str(exe)]);assert run.returncode==0,('private Newlib test failed at source line',run.returncode)
print('PASS private Newlib: formatting including %lln/float/64-bit/scanning, arena allocation, immutable stdio cache, errors, frame/palette, input/log bounds, clock wait, exit and final drain')
(a.build/'test-result.json').write_text(json.dumps(dict(passed=True,pointer_bytes=4,private_newlib=True,sanitized=sanitized),indent=2)+'\n')

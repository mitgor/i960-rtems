#!/usr/bin/env python3
"""Use the accepted unchanged private host engine for matching 52-frame no-input baseline."""
from pathlib import Path
import subprocess
w=Path('/home/mit/i960-doom-pipeline-20261014');b=w/'build/platform-host';o=w/'native-52';o.mkdir(exist_ok=True)
s='#include <stdio.h>\n'+(b/'play-native.c').read_text().replace('frames==40','frames==52')
s=s.replace('frames=z;row[0]', 'frames=z;{char path[256];int f;snprintf(path,sizeof path,"'+str(o)+'/frame-%u.bin",frames);f=syscall(5,path,577,0600);if(f<0||syscall(4,f,p,65536)!=65536)return 0;syscall(6,f);}row[0]')
(o/'native.c').write_text(s)
r=w/'project/game/doom';flags=['-m32','-Os','-fno-builtin','-funsigned-char','-D__SINGLE_THREAD__','-DDOOM_CHECKPOINTS','-DDOOM_VISIBLE','-I'+str(r/'play'),'-I'+str(w/'build/newlib-1.11.0/newlib/libc/include'),'-fsanitize=address,undefined','-g']
subprocess.run(['gcc',*flags,'-c',str(o/'native.c'),'-o',str(o/'native.o')],check=True)
subprocess.run(['objcopy','--redefine-syms='+str(b/'rename.txt'),str(o/'native.o'),str(o/'private.o')],check=True)
subprocess.run(['gcc','-m32','-no-pie',str(o/'private.o'),str(b/'doom-platform.o'),str(b/'play-heap.o'),str(b/'play-arena.o'),'-fsanitize=address,undefined','-o',str(o/'native')],check=True)
for run in range(2):
 with (o/f'result-{run}.bin').open('wb') as out,(o/f'log-{run}.bin').open('wb') as err:
  subprocess.run([str(o/'native'),str(w/'build/freedoom1.wad'),'6',str(o/f'requests-{run}.bin'),str(o/f'checkpoints-{run}.bin')],stdout=out,stderr=err,check=True)
 if not run:
  reference=[(o/f'frame-{i}.bin').read_bytes() for i in range(1,53)]
 else:assert reference==[(o/f'frame-{i}.bin').read_bytes() for i in range(1,53)]
assert (o/'result-0.bin').read_bytes()==(o/'result-1.bin').read_bytes()
print('PASS two deterministic 52-frame native runs, matching no-input baseline and owned STOP')

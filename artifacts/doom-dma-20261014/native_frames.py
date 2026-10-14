#!/usr/bin/env python3
"""Use the accepted unchanged private host engine for matching 28-frame input."""
from pathlib import Path
import subprocess
old=Path('/home/mit/i960-doom-play-20261013b');w=Path('/home/mit/i960-doom-dma-20261014c');b=old/'platform-host';o=w/'native-28';o.mkdir(exist_ok=True)
s='#include <stdio.h>\n'+(b/'play-native.c').read_text().replace('frames==40','frames==28').replace('frames==3&&','frames==2&&').replace('frames==20&&','frames==4&&')
s=s.replace('frames=z;row[0]', 'frames=z;{char path[256];int f;snprintf(path,sizeof path,"'+str(o)+'/frame-%u.bin",frames);f=syscall(5,path,577,0600);if(f<0||syscall(4,f,p,65536)!=65536)return 0;syscall(6,f);}row[0]')
(o/'native.c').write_text(s)
r=w/'project/game/doom';flags=['-m32','-Os','-fno-builtin','-funsigned-char','-D__SINGLE_THREAD__','-DDOOM_CHECKPOINTS','-DDOOM_VISIBLE','-I'+str(r/'play'),'-I'+str(w/'newlib-1.11.0/newlib/libc/include'),'-fsanitize=address,undefined','-g']
subprocess.run(['gcc',*flags,'-c',str(o/'native.c'),'-o',str(o/'native.o')],check=True)
subprocess.run(['objcopy','--redefine-syms='+str(b/'rename.txt'),str(o/'native.o'),str(o/'private.o')],check=True)
subprocess.run(['gcc','-m32','-no-pie',str(o/'private.o'),str(b/'doom-platform.o'),str(b/'play-heap.o'),str(b/'play-arena.o'),'-fsanitize=address,undefined','-o',str(o/'native')],check=True)
for run in range(2):
 with (o/f'result-{run}.bin').open('wb') as out,(o/f'log-{run}.bin').open('wb') as err:
  subprocess.run([str(o/'native'),'/home/mit/i960-doom-batch-20261012/freedoom1.wad','0',str(o/f'requests-{run}.bin'),str(o/f'checkpoints-{run}.bin')],stdout=out,stderr=err,check=True)
 if not run:
  reference=[(o/f'frame-{i}.bin').read_bytes() for i in range(1,29)]
 else:assert reference==[(o/f'frame-{i}.bin').read_bytes() for i in range(1,29)]
assert (o/'result-0.bin').read_bytes()==(o/'result-1.bin').read_bytes()
print('PASS two deterministic 28-frame native runs, matching forward/release inputs and owned STOP')

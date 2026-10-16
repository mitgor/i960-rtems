#!/usr/bin/env python3
from pathlib import Path
import subprocess,argparse
p=argparse.ArgumentParser();p.add_argument("--baseline",action="store_true");args=p.parse_args()
w=Path('/home/mit/i960-span-four-20261016');build='build' if args.baseline else 'build-fast';b=w/build/'platform-host';o=w/('native-baseline' if args.baseline else 'native-fast');o.mkdir(exist_ok=True)
s='#include <stdio.h>\n'+(b/'play-native.c').read_text().replace('frames==40','frames==52')
s=s.replace('frames=z;row[0]', 'frames=z;{char path[256];int f;snprintf(path,sizeof path,"'+str(o)+'/frame-%u.bin",frames);f=syscall(5,path,577,0600);if(f<0||syscall(4,f,p,65536)!=65536)return 0;syscall(6,f);}row[0]')
s=s.replace('unsigned row[3];','unsigned row[4];').replace('row[2]=heap.peak;', 'row[2]=heap.peak;row[3]=reads;')
a=s.index(' if(stage==101)');z=s.index('\n return 1;',a)
s=s[:a]+''' if(stage==101)return 1;\n'''+s[z:]
(o/'native.c').write_text(s)
r=w/'project/game/doom';flags=['-m32','-Os','-fno-builtin','-funsigned-char','-D__SINGLE_THREAD__','-DDOOM_CHECKPOINTS','-DDOOM_VISIBLE','-I'+str(r/'play'),'-I'+str(w/build/'newlib-1.11.0/newlib/libc/include'),'-fsanitize=address,undefined','-g']
subprocess.run(['gcc',*flags,'-c',str(o/'native.c'),'-o',str(o/'native.o')],check=True)
subprocess.run(['objcopy','--redefine-syms='+str(b/'rename.txt'),str(o/'native.o'),str(o/'private.o')],check=True)
subprocess.run(['gcc','-m32','-no-pie',str(o/'private.o'),str(b/'doom-platform.o'),str(b/'play-heap.o'),str(b/'play-arena.o'),'-fsanitize=address,undefined','-o',str(o/'native')],check=True)
for run in range(2):
 with (o/f'result-{run}.bin').open('wb') as out,(o/f'log-{run}.bin').open('wb') as err:
  subprocess.run([str(o/'native'),str(w/build/'freedoom1.wad'),'6',str(o/f'requests-{run}.bin'),str(o/f'checkpoints-{run}.bin')],stdout=out,stderr=err,check=True)
 if not run:reference=[(o/f'frame-{i}.bin').read_bytes() for i in range(1,53)]
 else:assert reference==[(o/f'frame-{i}.bin').read_bytes() for i in range(1,53)]
assert (o/'result-0.bin').read_bytes()==(o/'result-1.bin').read_bytes()
print('PASS two deterministic native 52-frame no-input runs with STOP and heap drain')

import struct
for i in range(1,53):
 w=struct.unpack_from('<16I',(o/f'frame-{i}.bin').read_bytes(),64960)
 assert w[:2]==(0x31435057,1) and min(w[6:9])>0 and w[10]>0 and w[11]>0
print('PASS actual backend cache counters are nonzero in all 52 native frames')

for i in range(1,53):
 assert (o/f"frame-{i}.bin").read_bytes()[:64768]==(Path("/home/mit/i960-columns-20261015/native-fast")/f"frame-{i}.bin").read_bytes()[:64768]
print("PASS all 52 native pixel/palette images equal prior column baseline")

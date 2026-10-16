#!/usr/bin/env python3
"""Repeat actual host32 engine and match the target's observed quality sequence."""
import argparse,json,subprocess,struct,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--newlib',type=Path,required=True);p.add_argument('--wad',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--capture',type=Path);a=p.parse_args();o=a.out.resolve();o.mkdir(exist_ok=True)
r=Path(__file__).resolve().parents[1];b=a.build.resolve()
modes=[0]*53
if a.capture:
 rows=[json.loads(x) for x in (a.capture/'play-frames.jsonl').read_text().splitlines()][:52]
 assert len(rows)==52;modes=[0]+[x['profile']['flat_planes'] for x in rows]
s=(r/'runtime/startup/native.c').read_text();begin=s.index('static int mark(');end=s.index('\n#endif',begin)
mark='''extern unsigned doom_flat_planes;
static unsigned frames,last=~0u,event,toggle;
static const unsigned char wanted[53]={MODES};
static int mark(unsigned stage,unsigned x,unsigned y,unsigned z){
 if(stage==100){char name[512];int fd;unsigned char*p=(void*)x;
  if(y!=65536||z!=frames+1||z>52||((unsigned*)(p+64880))[2]!=wanted[z])return 0;
  frames=z;snprintf(name,sizeof name,"OUT/frame-%u.bin",z);fd=syscall(5,name,577,0600);
  if(fd<0||syscall(4,fd,p,65536)!=65536)return 0;syscall(6,fd);
  if(frames==52){stop=1;return -1;}return 1;
 }
 if(stage==101){
  if(last!=frames){last=frames;event=0;toggle=wanted[frames+1]!=doom_flat_planes;}
  if(toggle&&event<2)return 2+192+((event++==0)?256:0);
  return 1;
 }
 return 1;
}'''.replace('MODES',','.join(map(str,modes))).replace('OUT',str(o))
s='#include <stdio.h>\n'+s[:begin]+mark+s[end:]
s=s.replace('"checkpoint_log.h"','"../runtime/startup/checkpoint_log.h"').replace('"../platform/platform.h"','"../runtime/platform/platform.h"').replace('"../heap.h"','"../runtime/heap.h"')
(o/'native.c').write_text(s)
flags=['-m32','-Os','-fno-builtin','-funsigned-char','-D__SINGLE_THREAD__','-DDOOM_CHECKPOINTS','-DDOOM_VISIBLE','-I'+str(r/'play'),'-I'+str(a.newlib/'newlib/libc/include'),'-fsanitize=address,undefined','-g']
subprocess.run(['gcc',*flags,'-c',str(o/'native.c'),'-o',str(o/'native.o')],check=True)
subprocess.run(['objcopy','--redefine-syms='+str(b/'rename.txt'),str(o/'native.o'),str(o/'private.o')],check=True)
subprocess.run(['gcc','-m32','-no-pie',str(o/'private.o'),str(b/'doom-platform.o'),str(b/'play-heap.o'),str(b/'play-arena.o'),'-fsanitize=address,undefined','-o',str(o/'native')],check=True)
for run in range(2):
 with (o/f'result-{run}.bin').open('wb') as out,(o/f'log-{run}.txt').open('wb') as err:
  subprocess.run([str(o/'native'),str(a.wad),'6',str(o/f'requests-{run}.bin'),str(o/f'checkpoints-{run}.bin')],stdout=out,stderr=err,check=True,timeout=180)
 frames=[(o/f'frame-{g}.bin').read_bytes() for g in range(1,53)]
 if run:assert frames==reference
 else:reference=frames
assert (o/'result-0.bin').read_bytes()==(o/'result-1.bin').read_bytes()
result=dict(repeated_frames=52,mode_sequence=modes[1:],stop_and_heap_drain=True)
if a.capture:
 differences=[]
 for g,frame in enumerate(reference,1):
  card=(a.capture/f'play-0-{g}.bin').read_bytes();diff=[i for i in range(64768) if card[i]!=frame[i]]
  assert diff==[29260,29261,29580,29581],(g,diff[:30],len(diff))
  differences.append(dict(frame=g,mode=modes[g],known_differences=diff))
 result['card_comparison']=differences
(o/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS repeated native frames, quality sequence, STOP, heap drain'+(' and exact known card differences' if a.capture else ''))

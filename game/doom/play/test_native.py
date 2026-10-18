#!/usr/bin/env python3
"""Exercise the actual interactive engine, input, STOP and heap drain on host32."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--newlib',type=Path,required=True);p.add_argument('--wad',type=Path,required=True);p.add_argument('--frames',type=int,default=40);p.add_argument('--wad-ring',action='store_true');p.add_argument('--runtime-flat-test',action='store_true');p.add_argument('--runtime-half-height-test',action='store_true');p.add_argument('--runtime-detail-test',action='store_true');a=p.parse_args()
assert 40<=a.frames<=1024
r=Path(__file__).resolve().parents[1];s=(r/'runtime/startup/native.c').read_text();begin=s.index('static int mark(');end=s.index('\n#endif',begin)
s=s[:begin]+'''static unsigned frames,event_sent;
static int mark(unsigned stage,unsigned x,unsigned y,unsigned z){
 if(stage==100){unsigned h=2166136261u,i;unsigned char*p=(void*)x;unsigned row[3];if(y!=65536||z!=frames+1)return 0;
 for(i=0;i<65536;i++)h=(h^p[i])*16777619u;frames=z;row[0]=frames;row[1]=h;row[2]=heap.peak;syscall(4,2,row,sizeof row);
 if(frames==40){stop=1;return -1;}return 1;}
 if(stage==101){if(mode==6)return 1;if(frames==3&&event_sent==0){event_sent++;return 2+256+0xad;}if(frames>=20&&event_sent==1){event_sent++;return 2+0xad;}return 1;}
 return 1;
}'''+s[end:];s=s.replace('if(frames==40)',f'if(frames=={a.frames})');s=s.replace('"checkpoint_log.h"','"../runtime/startup/checkpoint_log.h"').replace('"../platform/platform.h"','"../runtime/platform/platform.h"').replace('"../heap.h"','"../runtime/heap.h"')
# I_GetEvent stops after key-up; queued test events must survive that frame.
if a.runtime_detail_test:
 s='#include <stdlib.h>\n'+s
 assert json.loads((a.build/'build.json').read_text()).get('runtime_detail')
 assert json.loads((a.build/'build.json').read_text()).get('low_detail')
 s='static unsigned detail_event;\n'+s
 s=s.replace('if(stage==101){', 'if(stage==101){if(frames>=12 && detail_event<2){return 2+191+((detail_event++==0)?256:0);}if(frames>=24 && detail_event<4){return 2+191+((detail_event++==2)?256:0);}')
 s=s.replace('frames=z;row[0]', 'if(z==10 && ((unsigned*)(p+64832))[2]!=1)abort();if(z==20 && ((unsigned*)(p+64832))[2]!=0)abort();if(z==32 && ((unsigned*)(p+64832))[2]!=1)abort();frames=z;row[0]')
if a.runtime_flat_test:
 s='#include <stdlib.h>\n'+s
 assert json.loads((a.build/'build.json').read_text()).get('runtime_flat')
 s='static unsigned flat_event;\n'+s
 s=s.replace('if(stage==101){', 'if(stage==101){if(frames>=12 && flat_event<2){return 2+192+((flat_event++==0)?256:0);}if(frames>=24 && flat_event<4){return 2+192+((flat_event++==2)?256:0);}')
 s=s.replace('frames=z;row[0]', 'if(z==10 && ((unsigned*)(p+64880))[2]!=0)abort();if(z==20 && ((unsigned*)(p+64880))[2]!=1)abort();if(z==32 && ((unsigned*)(p+64880))[2]!=0)abort();frames=z;row[0]')
if a.runtime_half_height_test:
 s='#include <stdlib.h>\nstatic unsigned half_event;\n'+s
 assert json.loads((a.build/'build.json').read_text()).get('runtime_half_height')
 s=s.replace('if(stage==101){', 'if(stage==101){if(frames>=8 && half_event<2){return 2+193+((half_event++==0)?256:0);}if(frames>=20 && half_event<4){return 2+193+((half_event++==2)?256:0);}')
 s=s.replace('frames=z;row[0]', 'if(z==6 && ((unsigned*)(p+64896))[2]!=0)abort();if(z==16 && ((unsigned*)(p+64896))[2]!=1)abort();if(z==32 && ((unsigned*)(p+64896))[2]!=0)abort();frames=z;row[0]')
if a.wad_ring:
 s=s.replace('n>4096','n>65536').replace('a.io.max_read=4096','a.io.max_read=65536')
 s=s.replace('token=doom_heap_borrow(&heap,dst,n);', 'void*stage=allocate(41216);if(!stage)return -1;token=doom_heap_borrow(&heap,dst,n);')
 s=s.replace('wire_bytes+=n;', 'wire_bytes+=n;release(stage);')
source=a.build/'play-native.c';source.write_text(s)
flags=['-m32','-Os','-fno-builtin','-funsigned-char','-D__SINGLE_THREAD__','-DDOOM_CHECKPOINTS','-DDOOM_VISIBLE','-I'+str(r/'play'),'-I'+str(a.newlib/'newlib/libc/include'),'-fsanitize=address,undefined','-g']
obj=a.build/'play-native.o';subprocess.run(['gcc',*flags,'-c',str(source),'-o',str(obj)],check=True)
private=a.build/'play-native-private.o';subprocess.run(['objcopy','--redefine-syms='+str(a.build/'rename.txt'),str(obj),str(private)],check=True)
objs=[private,a.build/'doom-platform.o']
for src in [r/'runtime/heap.c',r.parents[1]/'loader/segmented/arena.c']:
 obj=a.build/('play-'+src.stem+'.o');subprocess.run(['gcc',*flags,'-c',str(src),'-o',str(obj)],check=True);objs.append(obj)
exe=a.build/'play-native';subprocess.run(['gcc','-m32','-no-pie',*map(str,objs),'-fsanitize=address,undefined','-o',str(exe)],check=True)
rows=[]
for i in range(3):
 run=subprocess.run([str(exe),str(a.wad),'6' if i==2 else '0',str(a.build/f'play-{i}.requests'),str(a.build/f'play-{i}.checkpoints')],capture_output=True,timeout=180)
 (a.build/f'play-{i}.bin').write_bytes(run.stdout);(a.build/f'play-{i}.log').write_bytes(run.stderr)
 assert run.returncode==0,(run.returncode,run.stderr[-2000:])
 result=struct.unpack_from('<12I',run.stdout);extra=struct.unpack_from('<8I',run.stdout,48)
 assert result[5]==a.frames and result[9:]==(2,1,210) and extra[3]==2,(result,extra)
 rows.append(dict(result=result,extra=extra,trace_sha256=hashlib.sha256(run.stderr[:a.frames*12]).hexdigest()))
assert rows[0]==rows[1]
assert rows[0]['trace_sha256']!=rows[2]['trace_sha256'], 'keyboard must alter rendered output'
(a.build/'play-native.json').write_text(json.dumps(rows,indent=2)+'\n');print(f'PASS {a.frames} interactive frames, input, STOP, heap drain and deterministic repeat')

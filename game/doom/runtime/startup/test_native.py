#!/usr/bin/env python3
import argparse,json,subprocess,struct,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--newlib',type=Path,required=True);p.add_argument('--wad',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parent
flags=['-m32','-Os','-fno-builtin','-funsigned-char','-D__SINGLE_THREAD__','-I'+str(a.newlib/'newlib/libc/include')];san=json.loads((a.build/'build.json').read_text())['sanitized']
if json.loads((a.build/'build.json').read_text()).get('checkpoints'):flags+=['-DDOOM_CHECKPOINTS']
if san:flags+=['-fsanitize=address,undefined','-g']
obj=a.build/'startup-native.o';subprocess.run(['gcc',*flags,'-c',str(r/'native.c'),'-o',str(obj)],check=True);private=a.build/'startup-native-private.o';subprocess.run(['objcopy','--redefine-syms='+str(a.build/'rename.txt'),str(obj),str(private)],check=True)
objs=[private,a.build/'doom-platform.o']
for src in [r.parent/'heap.c',r.parents[3]/'loader/segmented/arena.c']:
 obj=a.build/('startup-'+src.stem+'.o');subprocess.run(['gcc',*flags,'-c',str(src),'-o',str(obj)],check=True);objs.append(obj)
exe=a.build/'startup-native';subprocess.run(['gcc','-m32','-no-pie',*map(str,objs),'-o',str(exe)]+(['-fsanitize=address,undefined'] if san else []),check=True)
rows=[]
for i,mode in enumerate([0,1,2,3,0]):
 run=subprocess.run([str(exe),str(a.wad),str(mode),str(a.build/f'startup-{i}.requests.bin'),str(a.build/f'startup-{i}.checkpoints.bin')],capture_output=True,timeout=120);(a.build/f'startup-{i}.bin').write_bytes(run.stdout);(a.build/f'startup-{i}.log').write_bytes(run.stderr)
 assert run.returncode==0,(mode,run.returncode,run.stderr[-4000:])
 assert len(run.stdout)>=80;result=struct.unpack_from('<12I',run.stdout);extra=struct.unpack_from('<8I',run.stdout,48)
 assert result[0:2]==(0x454e4750,2) and result[10]==1 and extra[3]==2
 assert result[9]==[0,2,4,3][mode],(mode,result)
 if not mode:assert len(run.stdout)==64848 and result[5:7]==(1,1)
 rows.append(dict(mode=mode,result=result,extra=extra,frame_sha256=hashlib.sha256(run.stdout[80:]).hexdigest() if not mode else None))
assert rows[0]==rows[-1]
(a.build/'startup-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS actual private-libc engine first frame, STOP, deadline, read failure, repeatability and complete owned-heap drain')

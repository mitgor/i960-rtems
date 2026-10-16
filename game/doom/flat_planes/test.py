#!/usr/bin/env python3
"""Test the pinned patch, real key responder and unchanged boundary contracts."""
import importlib.util,tarfile,tempfile,subprocess,sys
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[2]
spec=importlib.util.spec_from_file_location('flat_patch',here/'patch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 with tarfile.open(root/'artifacts/doom-m1-20261011/doomgeneric-source.tar.gz') as a:a.extractall(t,filter='data')
 src=next(t.glob('doomgeneric-*/doomgeneric'))
 original=(src/'r_plane.c').read_text()
 def patch(name,old,new):
  f=src/name;s=f.read_text();assert s.count(old)==1;f.write_text(s.replace(old,new))
 m.apply(patch)
 changed=(src/'r_plane.c').read_text()
 assert changed[changed.index('void R_DrawPlanes'):]==original[original.index('void R_DrawPlanes'):]
 assert changed[changed.index('    if (planeheight != cachedheight[y])'):]==original[original.index('    if (planeheight != cachedheight[y])'):]
 # Compile actual generated debounce/toggle implementation, not a duplicate.
 begin=changed.index('unsigned doom_flat_planes');end=changed.index('\n\n',begin)
 (t/'key.c').write_text('#include <assert.h>\n'+changed[begin:end]+'''\nint main(void){
 assert(!doom_flat_planes && !doom_flat_switches);
 doom_flat_key(1);doom_flat_key(1);assert(doom_flat_planes==1&&doom_flat_switches==1);
 doom_flat_key(0);doom_flat_key(0);doom_flat_key(1);assert(!doom_flat_planes&&doom_flat_switches==2);
 return 0;}\n''')
 for source in (t/'key.c',here/'test_fill.c'):
  out=t/source.stem;subprocess.run(['cc','-O2','-fno-strict-aliasing','-fsanitize=address,undefined',str(source),'-o',str(out)],check=True);subprocess.run([str(out)],check=True)
sys.path.insert(0,str(root/'rtems/residentnet'))
from presentation_profile import decode,preflight,OFFSET
import struct
opt=dict(cpu_profile=True,frame_profile=True,double_buffer=True,runtime_flat=True)
b=bytearray(65536);struct.pack_into('<16I',b,OFFSET,0x31524650,1,1,2,100,60,30,10,20,0,0,100,0,0,10,0)
struct.pack_into('<12I',b,64832,0x31555043,1,0,10,8,5,2,1,1,0,0,0)
for count in range(5):
 struct.pack_into('<4I',b,64880,0x31544c46,1,count&1,count)
 assert decode(b,1,options=opt)['flat_planes']==count&1
for off,val in ((64880,0),(64884,2),(64888,2),(64892,3),(64896,1)):
 bad=bytearray(b);struct.pack_into('<I',bad,off,val)
 try:decode(bad,1,options=opt)
 except AssertionError:pass
 else:raise AssertionError(('bad flat telemetry',off))
preflight(opt,True,False,False)
for key in ('double_buffer','frame_profile','cpu_profile'):
 try:preflight(dict(opt,**{key:False}),True,False,False)
 except AssertionError:pass
 else:raise AssertionError(key)
print('PASS flat patch, textured/sky paths, debounced key, telemetry and admission checks')

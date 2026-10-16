#!/usr/bin/env python3
"""Actual helper boundary tests plus independent strict telemetry decoding."""
import subprocess,tempfile,sys,struct,importlib.util,tarfile
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[2]
with tempfile.TemporaryDirectory() as d:
 t=Path(d);exe=t/'test'
 subprocess.run(['cc','-O2','-fno-strict-aliasing','-fsanitize=address,undefined','-I'+str(here.parent),str(here/'test.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
 with tarfile.open(root/'artifacts/doom-m1-20261011/doomgeneric-source.tar.gz') as a:a.extractall(t,filter='data')
 src=next(t.glob('doomgeneric-*/doomgeneric'))
 def patch(name,old,new):
  p=src/name;s=p.read_text();assert s.count(old)==1;p.write_text(s.replace(old,new))
 for name in ('half_height','flat_planes'):
  spec=importlib.util.spec_from_file_location(name,here.parent/name/'patch.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.apply(patch)
 s=(src/'r_plane.c').read_text();assert s.index('if (doom_half_height && (y & 1))')<s.index('if (doom_flat_planes)')
 s=(src/'r_main.c').read_text();begin=s.index('unsigned doom_half_height');end=s.index('\n}',begin)+2
 (t/'key.c').write_text('#include <assert.h>\n'+s[begin:end]+'''\nint main(void){
 assert(!doom_half_height&&!doom_half_switches);doom_half_key(1);doom_half_key(1);
 assert(doom_half_height==1&&doom_half_switches==1);doom_half_key(0);doom_half_key(1);
 assert(!doom_half_height&&doom_half_switches==2);return 0;}''')
 subprocess.run(['cc',str(t/'key.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
sys.path.insert(0,str(root/'rtems/residentnet'))
from presentation_profile import decode,preflight
for flat in (False,True):
 opt=dict(cpu_profile=True,frame_profile=True,double_buffer=True,runtime_half_height=True,runtime_flat=flat)
 b=bytearray(65536);struct.pack_into('<16I',b,64768,0x31524650,1,1,2,100,60,30,10,20,0,0,100,0,0,10,0)
 struct.pack_into('<12I',b,64832,0x31555043,1,0,10,8,5,2,1,1,0,0,0)
 if flat:struct.pack_into('<4I',b,64880,0x31544c46,1,1,1)
 for count in range(4):
  struct.pack_into('<4I',b,64896,0x31464c48,1,count&1,count)
  assert decode(b,1,options=opt)['half_height']==count&1
 for off,val in ((64896,0),(64900,2),(64904,2),(64908,2),(64912,1)):
  bad=bytearray(b);struct.pack_into('<I',bad,off,val)
  try:decode(bad,1,options=opt)
  except AssertionError:pass
  else:raise AssertionError(('invalid half telemetry',off))
 preflight(opt,True,False,False)
 for key in ('double_buffer','frame_profile','cpu_profile'):
  try:preflight(dict(opt,**{key:False}),True,False,False)
  except AssertionError:pass
  else:raise AssertionError(key)
print('PASS independent half-height toggle, flat span skip, strict metadata and preflight')

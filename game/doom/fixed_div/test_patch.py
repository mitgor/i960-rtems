#!/usr/bin/env python3
"""Exercise both optional transforms against the pinned engine sources."""
import importlib.util,json,tarfile,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('divide_patch',here/'patch.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
archive=here.parents[2]/'artifacts/doom-m1-20261011/doomgeneric-source.tar.gz'
for fast,profile in [(True,False),(False,True),(True,True)]:
 with tempfile.TemporaryDirectory() as tmp:
  with tarfile.open(archive) as tf:tf.extractall(tmp,filter='data')
  src=next(Path(tmp).glob('*/doomgeneric'))
  original={f.name:f.read_bytes() for f in src.glob('*.c')}
  def patch(name,old,new):
   p=src/name;s=p.read_text();assert s.count(old)==1;p.write_text(s.replace(old,new))
  m.apply(src,patch,fast,profile)
  if profile:
   assert len(json.loads((src/'fixed-sites.json').read_text()))==47
   assert (src/'fixed_profile.c').exists()
  else:
   assert not (src/'fixed_profile.c').exists()
   assert not (src/'fixed_profile.h').exists()
   assert 'return doom_div_fast(a,b)' in (src/'m_fixed.c').read_text()
   for name,data in original.items():
    if name!='m_fixed.c':assert (src/name).read_bytes()==data,name
  for name in ('divide.c','divide.S'):
   assert (src/('fixed_'+name)).read_bytes()==(here/name).read_bytes()
print('PASS profiled original/exact and unprofiled exact transforms; call sites unchanged in play mode')

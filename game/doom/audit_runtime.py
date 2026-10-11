#!/usr/bin/env python3
"""Map unresolved i960 symbols to object callers; preserve expected final-link failure."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve();out=root/'cross/i960';prefix='/home/mit/i960/tools/bin/i960-coff-'
undef={s.split()[-1]:[] for s in (out/'undefined.txt').read_text().splitlines() if s.strip()}
for obj in sorted(out.glob('*.o')):
 if obj.name=='doom-engine.o':continue
 for line in subprocess.check_output([prefix+'nm','-u',str(obj)],text=True).splitlines():
  sym=line.split()[-1]
  if sym in undef:undef[sym].append(obj.name)
(out/'runtime-callers.json').write_text(json.dumps(undef,indent=2)+'\n')
with (out/'expected-unresolved-link.log').open('w') as f:
 r=subprocess.run([prefix+'ld','-e','_doomgeneric_Create','-o',str(out/'not-loadable.elf'),str(out/'doom-engine.o')],stdout=f,stderr=f)
assert r.returncode!=0,'Milestone 1 must not silently resolve missing runtime with fake stubs'
assert not (out/'not-loadable.elf').exists()
flags=json.loads((out/'build.json').read_text())['flags']
subprocess.run([prefix+'gcc',*flags,'-c',str(root/'tools/abi.c'),'-o',str(out/'abi-probe.o')],check=True)
with (out/'abi-sizes.txt').open('w') as f:subprocess.run([prefix+'nm','-S','--size-sort',str(out/'abi-probe.o')],stdout=f,check=True)

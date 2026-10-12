#!/usr/bin/env python3
"""Link real compiler helpers, inventory remaining imports/relocations. No stubs."""
import argparse,collections,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('engine',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def run(tool,*args):return subprocess.check_output([a.cross+tool,*map(str,args)],text=True)
def undefined(path):return sorted(s.split()[-1] for s in run('nm','-u',path).splitlines() if s.strip())
lib=Path(run('gcc','-mrp','-msoft-float','-print-libgcc-file-name').strip());assert lib.is_file()
output=a.out/'doom-runtime.o';command=[a.cross+'ld','-r','-d','-o',str(output),str(a.engine),str(lib)];subprocess.run(command,check=True)
before=undefined(a.engine);after=undefined(output);assert set(after)<=set(before)
(a.out/'undefined.txt').write_text('\n'.join(after)+'\n')
relocs=run('objdump','-r',output);(a.out/'relocations.txt').write_text(relocs)
counts=collections.Counter(s.split()[1] for s in relocs.splitlines() if len(s.split())>=3 and s.split()[1].startswith('R_960_'))
with (a.out/'disassembly.txt').open('w') as f:subprocess.run([a.cross+'objdump','-dr',str(output)],stdout=f,check=True)
with (a.out/'sections.txt').open('w') as f:subprocess.run([str(Path(a.cross).parent/'i960-elf-size'),'-A',str(output)],stdout=f,check=True)
callers={sym:[] for sym in after}
for obj in sorted(a.engine.parent.glob('*.o')):
 if obj.name in ('doom-engine.o','doom-with-libgcc.o','doom-runtime.o'):continue
 for sym in undefined(obj):
  if sym in callers:callers[sym].append(obj.name)
(a.out/'import-callers.json').write_text(json.dumps(callers,indent=2)+'\n')
# Missing platform/libc services must fail a final link; never manufacture a
# nominally executable image by assigning imports to zero or success stubs.
with (a.out/'expected-final-link-failure.txt').open('w') as f:
 failed=subprocess.run([a.cross+'ld','-e','_doomgeneric_Create','-o',str(a.out/'not-loadable.elf'),str(output)],stdout=f,stderr=f)
assert failed.returncode and not (a.out/'not-loadable.elf').exists()
report=dict(engine_sha256=hashlib.sha256(a.engine.read_bytes()).hexdigest(),runtime_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),compiler_archive=str(lib),compiler_archive_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),command=command,imports_before=len(before),imports_after=len(after),resolved=sorted(set(before)-set(after)),remaining=after,relocations=dict(counts),final_link_correctly_refused=True,loadable=False)
(a.out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

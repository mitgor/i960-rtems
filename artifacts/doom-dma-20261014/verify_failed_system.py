#!/usr/bin/env python3
"""Validate the recorded audit prefix, explicitly excluding terminal acceptance.
Reuse the unchanged verifier through its pre-terminal snapshot/RAM checks. The
original full verifier MUST still reject this run; no shutdown is synthesized.
"""
import inspect,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'rtems/residentnet'))
import verify as full
marker=' assert groups[-1][2]==2 and groups[-1][4:36]==groups[-2][4:36]'
source=inspect.getsource(full.verify);assert source.count(marker)==1
prefix=source[:source.index(marker)].replace('def verify(root,out):','def prefix(root,out):')
prefix+=''' assert len(groups)==len(ram_groups)==23 and len(diag_groups)==22
 assert diag_groups==[d['words'] for d in json.loads((out/'heap-diagnostics.json').read_text())]
 assert groups[-1][2]==1 and groups[-1][3]==0
 return dict(acceptance=False,monitor_ram_pairs=len(groups),heap_pages=len(diag_groups),last_audited_tick=groups[-1][5],terminal_snapshot=False,heap_drain_proven=False)
'''
namespace={};exec(compile(prefix,'unchanged-preterminal-audit-checks','exec'),vars(full),namespace)
root=Path(sys.argv[1]);out=root/'live';check=namespace['prefix'];result=check(root,out)
try:full.verify(root,out)
except AssertionError:result['full_verifier_correctly_rejected']=True
else:raise AssertionError('failed run passed full acceptance')
with tempfile.TemporaryDirectory() as d:
 t=Path(d)
 for p in out.iterdir():
  if p.name!='snapshots.json':(t/p.name).symlink_to(p.resolve(),target_is_directory=p.is_dir())
 original=(out/'snapshots.json').read_text();count=0
 for i in (0,1,2,3,4,5,8,11,12,16,20,27,32,36,42,45,47,48,50,52,53,54,56,63):
  rows=json.loads(original);rows[-1]['words'][i]^=1;(t/'snapshots.json').write_text(json.dumps(rows))
  try:check(root,t)
  except AssertionError:count+=1
  else:raise AssertionError(('snapshot mutation accepted',i))
 result['snapshot_mutations_rejected']=count
print(json.dumps(result,indent=2))

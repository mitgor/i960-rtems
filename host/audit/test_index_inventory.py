#!/usr/bin/env python3
"""Staged inventory must not absorb a concurrent task's dirty artifact bytes."""
import json,subprocess,sys,tempfile
from pathlib import Path
source=Path(__file__).with_name('artifacts.py')
with tempfile.TemporaryDirectory() as d:
 root=Path(d);script=root/'host/audit/artifacts.py';script.parent.mkdir(parents=True);script.write_bytes(source.read_bytes())
 a=root/'artifacts';a.mkdir();(a/'artifact-inventory.json').write_text('{"files":[]}\n');(a/'one.bin').write_bytes(b'original\0bytes')
 def run(*args,ok=True):
  r=subprocess.run(args,cwd=root,capture_output=True,text=True)
  assert (r.returncode==0)==ok,(args,r.stdout,r.stderr)
  return r
 (a/'d').mkdir();(a/'d/nested.bin').write_bytes(b'nested');(a/'d.bin').write_bytes(b'sibling')
 run('git','init','-q');run('git','add','artifacts/one.bin','artifacts/d/nested.bin','artifacts/d.bin')
 (a/'one.bin').write_bytes(b'unfinished replacement')
 flags=[sys.executable,str(script),'--tracked-only','--index-bytes']
 run(*flags,'--update');rows=json.loads((a/'artifact-inventory.json').read_text())['files'];assert next(r for r in rows if r['path']=='artifacts/one.bin')['size']==len(b'original\0bytes')
 run('git','add','artifacts/artifact-inventory.json','artifacts/SHA256SUMS');run(*flags,'--check-git')
 run(sys.executable,str(script),'--tracked-only','--check-git',ok=False)
 assert (a/'one.bin').read_bytes()==b'unfinished replacement'
 run('git','add','artifacts/one.bin');run(*flags,'--check-git',ok=False)
 run(*flags,'--update');run('git','add','artifacts/artifact-inventory.json','artifacts/SHA256SUMS');run(*flags,'--check-git')
 run(sys.executable,str(script),'--tracked-only','--check-git')
 (a/'link').symlink_to('one.bin');run('git','add','artifacts/link');run(*flags,'--update',ok=False)
 run(sys.executable,str(script),'--index-bytes',ok=False)
print('Index inventory: dirty bytes excluded, stale index rejected, updates verified, symlinks denied; worktree preserved.')

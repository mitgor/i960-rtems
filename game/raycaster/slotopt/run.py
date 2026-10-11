#!/usr/bin/env python3
"""Select a request suite around the unchanged accepted live/audit implementation.

Only model/cases selection and random-epoch headroom are changed, with exact source assertions. Every Board,
paired/full read, command check, timing capture and CLOSE line stays unchanged.
"""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;GAME=HERE.parent
sys.path.insert(0,str(GAME));sys.path.insert(0,str(GAME/'queue'))
from combined.optimize import once
p=argparse.ArgumentParser();p.add_argument('--suite',choices=['combined','bench','stress']);p.add_argument('--verify',type=Path);a,rest=p.parse_known_args()
if a.verify:
 suite=json.loads((a.verify/'slotopt-test.json').read_text())['suite'];assert suite in ('combined','bench','stress')
 if a.suite:assert a.suite==suite
 file=GAME/'queue/verify.py';args=[str(a.verify),*rest];out=None
else:
 if not a.suite:p.error('--suite required for live test')
 suite=a.suite;file=GAME/'queue/live.py';args=[*rest,'--queue','--pipeline','combined']
 out=Path(rest[rest.index('--output')+1])
s=file.read_text();s=once(s,' from combined.model import Model,cases as pipeline_cases\n cases=lambda epoch:pipeline_cases(epoch=epoch,combined='+('cfg[\'pipeline\']' if a.verify else 'a.pipeline')+"=='combined')",f' from slotopt.model import Model,cases as selected_cases\n cases=lambda epoch:selected_cases(epoch=epoch,suite={suite!r})')
if not a.verify:s=once(s,'secrets.randbelow(0xfffffffd)+1','secrets.randbelow(0xfffffff8)+1')
sys.argv=[str(file),*args]
try:exec(compile(s,str(file),'exec'),dict(__name__='__main__',__file__=str(file)))
finally:
 if out and out.exists():(out/'slotopt-test.json').write_text(json.dumps(dict(suite=suite),indent=2)+'\n')

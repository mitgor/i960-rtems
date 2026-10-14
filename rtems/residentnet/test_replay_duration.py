#!/usr/bin/env python3
"""Run actual verifier duration gates with a generous budget and short capture."""
import ast
from pathlib import Path
s=ast.parse(Path(__file__).with_name('verify.py').read_text())
checks=[n for n in ast.walk(s) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(x,ast.Constant) and x.value in (180000,210000) for x in n.test.comparators)]
assert len(checks)==2
code=compile(ast.fix_missing_locations(ast.Module(body=checks,type_ignores=[])),'duration gates','exec')
def run(ticks,rollovers,preemptions=(1,1)):
 exec(code,dict(options={'ticks':360000},groups=[[0]*5+[ticks]],diag_groups=[[0]*9+[rollovers]],diagnostics={'unlocked_copy_preemptions':preemptions}))
run(150000,1);run(180000,1);run(210000,2)
for args in ((180000,0),(180000,1,(0,1)),(210000,1)):
 try:run(*args)
 except AssertionError:pass
 else:raise AssertionError(('missing duration coverage accepted',args))
print('PASS actual elapsed-duration audit gates; maximum budget cannot demand unelapsed timer wraps')

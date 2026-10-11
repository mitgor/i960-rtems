#!/usr/bin/env python3
"""Exercise the live recorder without hardware; reconstruct every event."""
import ast,json,tempfile
from pathlib import Path
from types import SimpleNamespace
source=ast.parse((Path(__file__).parent/'live.py').read_text())
main=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='main')
funcs=[n for n in main.body if isinstance(n,ast.FunctionDef) and n.name in ('save','record_control')]
assert len(funcs)==2
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);events=[];snaps=[{'words':[1,2,3]}]
 scope=dict(json=json,b=SimpleNamespace(out=p),events=events,snaps=snaps)
 exec(compile(ast.Module(body=funcs,type_ignores=[]),'live-recorder','exec'),scope)
 for i in range(2000):
  scope['record_control'](dict(words=[i]*8,ns=i+1) if i%3 else dict(packet_op=1,errno=11,epoch=17,length=1500))
  if i%100==0:scope['save']()
 assert not (p/'controls.json').exists()
 recovered=[json.loads(l) for l in (p/'control-journal.jsonl').read_text().splitlines()]
 assert recovered==events and len(recovered)==2000
 scope['save'](final=True)
 assert json.loads((p/'controls.json').read_text())==events
 assert json.loads((p/'snapshots.json').read_text())==snaps
print('Control journal: 2,000 success/error records reconstruct exactly; full history written only at finalization')

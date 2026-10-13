#!/usr/bin/env python3
"""Exercise exact bridge ioctl framing with a fake transport, never a card."""
import ast,json,struct,tempfile,time,types
from pathlib import Path
source=ast.parse(Path(__file__).with_name('input_bridge.py').read_text());function=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='ctl')
class Fake:
 fail=False
 def ioctl(self,fd,code,raw,mutate):
  assert fd==77 and code==0xc4204d06 and len(raw)==1056 and mutate
  w=struct.unpack_from('<10I',raw);assert w[:8]==(10,42,8,0,0,0,0,0) and w[8:]==(2,419) and not any(raw[40:])
  if self.fail:raise OSError(5,'injected transport failure')
  struct.pack_into('<I',raw,8,4);struct.pack_into('<I',raw,12,1);struct.pack_into('<I',raw,32,0)
with tempfile.TemporaryDirectory() as d:
 fake=Fake();env=dict(a=types.SimpleNamespace(epoch=42,output=Path(d)),fd=77,fcntl=fake,json=json,struct=struct,time=time)
 exec(compile(ast.Module(body=[function],type_ignores=[]),'bridge ctl','exec'),env)
 assert env['ctl'](2,419)==0 # pressed KEY_FIRE=163, not classic Ctrl=157
 fake.fail=True
 try:env['ctl'](2,419)
 except OSError as e:assert e.errno==5
 else:raise AssertionError('transport failure must propagate without retry')
 rows=[json.loads(x) for x in (Path(d)/'keys.jsonl').read_text().splitlines()];assert len(rows)==2 and rows[1]['errno']==5
print('PASS exact bridge framing, response checks and logged transport failure')

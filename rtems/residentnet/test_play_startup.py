#!/usr/bin/env python3
"""Exercise the actual relay's pre-frame path with runtime quality enabled."""
import ast,types,sys
from pathlib import Path
source=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('play_client.py')
module=ast.parse(source.read_text())
exercise=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='exercise')
serve=next(x for x in ast.walk(exercise) if isinstance(x,ast.FunctionDef) and x.name=='serve')
# Stop at the first frame-transfer helper: these cases must never read card bytes.
end=next(i for i,x in enumerate(serve.body) if isinstance(x,ast.FunctionDef) and x.name=='read_frame')
serve.body=[ast.Global(names=x.names) if isinstance(x,ast.Nonlocal) else x for x in serve.body[:end]]+[ast.Return(value=ast.Constant(value='ready'))]
code=compile(ast.fix_missing_locations(ast.Module(body=[serve],type_ignores=[])),'play_client.py startup path','exec')
for frame,seen,expected in [(0,0,False),(9,9,False),(10,9,'ready'),(0xffffffff,0,'error')]:
 env=dict(abort=None,stop=types.SimpleNamespace(is_set=lambda:False),stop_sent=False,seen=seen,last_poll=0,last_loading_message=0,pp_active=False,pipeline_test=True,m={'runtime_detail':True},server=types.SimpleNamespace(serve=lambda:False),time=types.SimpleNamespace(monotonic=lambda:1),ctl=lambda:frame)
 exec(code,env)
 try:result=env['serve']()
 except RuntimeError:
  assert expected=='error'
 else:assert result==expected,(frame,result)
print('PASS runtime-detail relay before first frame, duplicate, ready and refused frame')

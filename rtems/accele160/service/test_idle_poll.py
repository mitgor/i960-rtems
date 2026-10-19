#!/usr/bin/env python3
"""Exercise the production idle loop with a virtual clock and injected fault."""
import ast,struct,types
from pathlib import Path
src=Path(__file__).parents[1]/'doom_dma/run_bridge.py';tree=ast.parse(src.read_text())
loop=next(n for n in ast.walk(tree) if isinstance(n,ast.While) and 'not a.restart_cycles' in ast.unparse(n.test))
code=compile(ast.fix_missing_locations(ast.Module(body=[loop],type_ignores=[])),str(src),'exec')
def run(fault_at=None):
 state=dict(t=100.,pumps=0,audits=[],snapshots=[],stop=False)
 class Time:
  def monotonic(self):return state['t']
  def sleep(self,n):assert n==.005;state['t']+=n
 class Stop:
  def is_set(self):return state['t']>=101 or state['stop']
 def pump():state['pumps']+=1
 def owner(base):state['audits'].append(state['t'])
 def snap(addr):
  state['snapshots'].append(state['t']);b=bytearray(4096)
  if fault_at is not None and state['t']>=fault_at:struct.pack_into('<I',b,0xb58,1)
  return b
 def need(ok,why):
  if not ok:raise RuntimeError(why)
 ns=dict(a=types.SimpleNamespace(restart_cycles=0),signal_stop=Stop(),browser=None,application_service=None,pump_heartbeat=pump,ownercheck=owner,owned=None,snap=snap,status=lambda name:{'done':'0'},need=need,struct=struct,time=Time(),last_idle_audit=0)
 try:exec(code,ns)
 except RuntimeError as e:assert fault_at is not None and str(e)=='idle owner fault'
 return state
normal=run();assert 199<=normal['pumps']<=201 and 9<=len(normal['audits'])<=11
assert normal['audits']==normal['snapshots'] and all(.099<=b-a<=.106 for a,b in zip(normal['audits'],normal['audits'][1:]))
fault=run(100.05);assert 100.05<=fault['t']<=100.155 and fault['pumps']<32
print('production idle loop: 5 ms pumping, separate 100 ms ownership/fault audit and bounded fault detection passed')

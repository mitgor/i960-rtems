#!/usr/bin/env python3
"""Actual owner functions: nested console reads cannot corrupt an audit page."""
import ast,textwrap
from pathlib import Path
source=Path(__file__).parents[1]/'doom_dma/run_bridge.py'
tree=ast.parse(source.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
parts=[ast.unparse(n) for n in main.body if isinstance(n,ast.FunctionDef) and n.name in ('snap','write','pump_service')]
body=textwrap.indent('\n'.join(parts),'    ')
setup='''def make(service):
    service_pumping=False
    PAGE=4096
    selected=[0]
    pages={a:bytearray(bytes([a])*8192) for a in (1,2,3)}
    class Window:
        def __getitem__(self,key):return pages[selected[0]][key]
        def __setitem__(self,key,value):pages[selected[0]][key]=value
    bar=Window()
    def need(ok,why):assert ok,why
    def translate(addr):selected[0]=addr
'''
ns={};exec(setup+body+'\n    return snap,write,pages\n',ns)
class Service:
    started=True;testing=False;calls=0;fail=False
    def pump(self,snap,write):
        self.calls+=1
        assert snap(2)==bytes([2])*4096
        write(3,0,b'test')
        if self.fail:raise RuntimeError('probe')
s=Service();snap,write,pages=ns['make'](s)
assert snap(1)==bytes([1])*4096 and s.calls==1 and pages[3][4096:4100]==b'test'
s.testing=True;assert snap(1)==bytes([1])*4096 and s.calls==1
s.testing=False;s.fail=True
try:snap(1);raise AssertionError('failure not propagated')
except RuntimeError:pass
s.fail=False;assert snap(1)==bytes([1])*4096 and s.calls==3
print('production audit pump: original page preserved, recursion excluded, selftest exclusion, exception reset PASS')

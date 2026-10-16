#!/usr/bin/env python3
import struct,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'rtems/residentnet'))
from presentation_profile import decode
raw=bytearray(65536);struct.pack_into('<16I',raw,64768,0x31524650,1,7,2,*([0]*10),10,0)
struct.pack_into('<8I',raw,65024,0x31525449,1,7,3,3,0,21,22)
for i,phase in enumerate((1,2,3)):struct.pack_into('<7I',raw,65056+i*28,i+1,phase,7,21,22,283,int(phase==3))
opts=dict(input_trace=True,fast_fixed_div=True)
assert len(decode(raw,7,options=opts)['input_trace']['events'])==3
n=0
for offset,value in [(65024,0),(65028,2),(65032,6),(65036,17),(65040,1),(65044,1),(65056,9),(65060,4),(65064,8),(65076,512),(65080,2),(65532,1)]:
 bad=raw.copy();struct.pack_into('<I',bad,offset,value)
 try:decode(bad,7,options=opts)
 except AssertionError:n+=1
 else:raise AssertionError((offset,value))
for options in ({},dict(input_trace=True,fixed_div_profile=True)):
 try:decode(raw,7,options=options)
 except AssertionError:n+=1
 else:raise AssertionError(options)
print('PASS input trace schema, overflow, sequence, frame, key, phase, menu, opt-in and padding:',n,'refusals')
# Parse only the option setup; avoid compilation or dependency access.
import argparse
source=(root/'game/doom/build.py').read_text().split('assert not a.platform_runtime',1)[0]
for args,expected in [([],False),(['--platform-runtime','--play'],True),(['--platform-runtime','--play','--no-fast-fixed-div'],False),(['--platform-runtime','--play','--fast-fixed-div'],True)]:
 sys.argv=['build.py','--work','/tmp/unused','--archive','/tmp/unused','--target','host32']+args
 env={'__name__':'option_test'};exec(source,env);assert env['a'].fast_fixed_div==expected
source=(root/'game/doom/play/build.py').read_text().split('if a.input_trace:',1)[0]
for args,expected in [([],True),(['--no-fast-fixed-div'],False),(['--fast-fixed-div'],True)]:
 sys.argv=['build.py','--work','/tmp/unused']+args;env={};exec(source,env);assert env['a'].fast_fixed_div==expected
print('PASS playable default, explicit original-divide switch and non-play build defaults')
# Compile the actual recorder, testing its bounded capacity and frame reset.
import subprocess,tempfile
recorder=(root/'game/doom/runtime/platform/presentation.h').read_text().split('#endif',1)[0].split('\n',1)[1]
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);source=p/'test.c';source.write_text('''#include <assert.h>
static struct {unsigned frames;} stats;
int gametic=21,menuactive=1;
int doom_input_maketic(void){return 22;}
'''+recorder+'''
int main(void){unsigned q[130],i;stats.frames=6;
 for(i=0;i<130;i++)q[i]=0xfeed;
 for(i=0;i<16;i++)doom_input_event(1,1,27);
 doom_input_event(2,1,27);input_record(q+1,7);
 assert(q[0]==0xfeed&&q[129]==0xfeed&&q[4]==16&&q[5]==17&&q[6]==1);
 input_record(q+1,8);assert(q[4]==0&&q[5]==17&&q[6]==1);
 for(i=9;i<129;i++)assert(q[i]==0);
 return 0;}
''')
 subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',str(source),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS actual recorder bounds, sticky overflow, trailer clearing and per-frame reset')
# Exercise the actual host logger with an explicit frame argument.
import ast,time,json
module=ast.parse((root/'rtems/residentnet/play_client.py').read_text())
node=next(n for n in ast.walk(module) if isinstance(n,ast.FunctionDef) and n.name=='ctl')
for call in ast.walk(module):
 if isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='ctl' and call.args and isinstance(call.args[0],ast.Constant) and call.args[0].value==2:assert len(call.args)==3
class Device:
 def io(self,op,data):assert op==10 and struct.unpack('<2I',data)==(2,283);return struct.pack('<I',0)
with tempfile.TemporaryDirectory() as tmp:
 env=dict(m={'input_trace':True},u=Device(),out=Path(tmp),time=time,struct=struct,json=json)
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<host-input-logger>','exec'),env)
 assert env['ctl'](2,283,60)==0
 row=json.loads((Path(tmp)/'input-submit.jsonl').read_text());assert row['observed_frame']==60 and row['key']==283 and row['result']==0
print('PASS actual host input logger frame scope and all key call sites')

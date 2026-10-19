#!/usr/bin/env python3
import runpy,sys,struct,json
# First run actual dual-stack TCP/UDP/HTTP qualification, then use the same
# loaded native module or card session for application operations and IP again.
x=runpy.run_path(str(__import__('pathlib').Path(__file__).with_name('test_net.py')))
call=x['call']
def app(op,id,gen=0,payload=b''):
 b=call(2,struct.pack('<5I',0x505041f1,1,op,id,gen)+payload)
 assert len(b)>=48;w=struct.unpack_from('<12I',b);assert w[:2]==(0x525041f1,1) and len(b)==48+w[11]
 return w,b[48:]
for i in (1,2):assert app(1,i)[0][2]==0
assert app(4,2,1,b'hello')[1]==b'HELLO'
if sys.argv[1]!='--rpc':call(1,ms=100)
a=app(3,1)[0];assert a[5]==1
assert app(2,1,0)[0][2]==4
assert app(2,1,1)[0][5]==0
assert app(1,1,1)[0][4]==2
assert app(2,1,1)[0][2]==4
reply=x['packets'](call(2,x['udp']));assert len(reply)==1 and x['split'](6,reply[0])[8:]==x['payload']
print(json.dumps(dict(combined_apps=True,echo=True,stale_stop_refused=True,network_after_app_restart=True)))

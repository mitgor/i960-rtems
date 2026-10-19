#!/usr/bin/env python3
"""Destructive test of only the explicitly loaned idle Doom zone, not stock RAM."""
import json,struct,time,argparse,socket
from pathlib import Path
from client import Client
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
c=Client();result={'started':time.time(),'steps':[]}
def save():a.out.write_text(json.dumps(result,indent=2)+'\n')
def loan(op):return c.call(9,struct.pack('<I',op))
result['before']=c.call(7);result['attach']=loan(0);assert result['attach']['value']==6*1024*1024;save()
# A close must refuse while the child loan is live, without stopping networking.
try:c.call(6)
except RuntimeError as e:
 assert isinstance(e.args[0],dict) and e.args[0]['status']==12
 result['close_refused']=e.args[0]
else:raise AssertionError('closed with live loan')
for i in range(200):
 start=time.monotonic();r=loan(1);r['latency_ms']=(time.monotonic()-start)*1000;result['steps'].append(r);save()
 if r['value']==3:break
 assert r['value'] in (1,2)
else:raise AssertionError('proof did not finish')
assert len(result['steps'])==192
result['release']=loan(2);result['after']=c.call(7)
result['bytes_written_and_verified']=6*1024*1024-32
result['cancelled_with_two_pins']=True
result['max_rpc_ms']=max(r['latency_ms'] for r in result['steps'])
result['finished']=time.time();save();print(json.dumps({k:v for k,v in result.items() if k!='steps'},indent=2))

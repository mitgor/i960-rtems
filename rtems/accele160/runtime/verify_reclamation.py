#!/usr/bin/env python3
"""Replay captured baseline, loan and routed IPv6 evidence without card access."""
import sys,json,tarfile,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'fault'))
from verify_runtime import verify

def replay(path):
 result=verify(path,live=True)
 with tarfile.open(path) as t:f={m.name:t.extractfile(m).read() for m in t if m.isfile()}
 j=lambda n:json.loads(f[n])
 manifest=j('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
 for n,h in manifest['runtime_sources'].items():assert hashlib.sha256(f['bundle/project/rtems/accele160/runtime/'+n]).hexdigest()==h
 modules=j('application-qualification.json')
 assert modules['hello_heap']['value']==255 and modules['hello_close']['reservation']==0
 for k in ('network_1','network_2'):
  v=modules[k];assert v['upload']['started'] and v['heap']['value']==255
  for family in ('ipv4','ipv6'):assert v['traffic'][family]['http200'] and v['traffic'][family]['udp_echo']
 assert modules['network_1']['close']['reservation']==0
 for name in ('hello','network'):
  m=j('bundle/'+name+'/manifest.json');assert hashlib.sha256(f['bundle/'+name+'/module.bin']).hexdigest()==m['sha256']
 assert b'2a02:8106:40:9000::960' in f['bundle/network/module.bin']
 q=j('loan-qualification.json');assert q['attach']['value']==6291456
 assert q['close_refused']['status']==12 and q['close_refused']['started']==1
 assert len(q['steps'])==192 and q['steps'][95]['value']==2 and q['steps'][-1]['value']==3
 assert all(not r['status'] and not r['poisoned'] and r['started'] for r in q['steps'])
 assert not q['release']['status'] and q['after']['calls']>q['before']['calls']
 assert q['bytes_written_and_verified']==6291424 and q['cancelled_with_two_pins']
 journals=[n for n in f if n.endswith('/run/applications.jsonl')];assert len(journals)==1
 rows=[json.loads(s) for s in f[journals[0]].splitlines()]
 assert not any(r['event']=='error' for r in rows)
 replies=[r for r in rows if r['event']=='reply']
 assert [r['status'] for r in replies if r['status']]==[12]
 assert not any(r['poisoned'] for r in replies)
 for fam in (4,6):
  assert f['http%d.headers'%fam].startswith(b'HTTP/1.0 200 OK')
  assert b'5 packets transmitted, 5 received, 0% packet loss' in f['ping%d.txt'%fam]
 for n in ('global-host','global-lan'):
  assert f[n+'.headers'].startswith(b'HTTP/1.0 200 OK')
  assert b'AcceleRAID 160' in f[n+'.html'] and b'Darth Vader' in f[n+'.html']
 route=j('public-routing.json');assert route['route'] and route['proxy'] and route['table'] and not route['dad']
 assert route['address']=='2a02:8106:40:9000::960'
 result.update(loan_bytes=6291456,pattern_bytes=6291424,two_reference_cancel_retention=True,
               loan_steps=192,max_loan_rpc_ms=q['max_rpc_ms'],global_ipv6_lan_http=True,
               internet_reachability_verified=False,new_stock_ram_reclaimed=False,unrestricted_task_cancellation=False)
 return result
if __name__=='__main__':print(json.dumps(replay(sys.argv[1]),indent=2))

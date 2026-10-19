#!/usr/bin/env python3
"""Replay the complete archived runtime qualification, not native claims."""
import hashlib,json,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'fault'))
from verify_runtime import verify

def replay(path):
 result=verify(path,live=True)
 with tarfile.open(path) as t:files={m.name:t.extractfile(m).read() for m in t if m.isfile()}
 prefix='bundle/project/';manifest=json.loads(files[prefix+'rtems/accele160/doom_dma/persistent-manifest.json'])
 assert manifest['runtime_schema']==1 and manifest['terminal_test']==5
 for key,folder in [('runtime_sources','rtems/accele160/runtime/'),('segmented_sources','loader/segmented/')]:
  for name,digest in manifest[key].items():assert hashlib.sha256(files[prefix+folder+name]).hexdigest()==digest
 q=json.loads(files['application-qualification.json'])
 assert q['initial']['state']==0 and q['initial']['reservation']==0
 assert bytes.fromhex(q['hello_reply']['data'])==b'Hello from Accele160 RTEMS segmented application\n'
 assert q['hello_heap']['value']==255 and q['hello_close']['reservation']==0 and q['hello_close']['state']==0
 for name in ('network_1','network_2'):
  row=q[name];assert row['upload']['started']==1 and row['heap']['value']==255
  for v in ('ipv4','ipv6'):
   p=row['traffic'][v];assert p['udp_echo'] and p['http200'] and p['fin'] and p['card_identity'] and p['http_bytes']>2500
  assert row['traffic']['counters']['rx']>0 and row['traffic']['counters']['tx']>0
 assert q['network_1']['close']['reservation']==0 and q['network_1']['close']['state']==0
 assert q['network_2']['query']['poisoned']==0 and q['network_2']['query']['busy']==0
 assert q['hello_upload']['epoch']<q['network_1']['upload']['epoch']<q['network_2']['upload']['epoch']
 assert 'idle=1' in q['final_apps'] and 'zone_loaned=0' in q['final_mem']
 journals=[n for n in files if n.endswith('/run/applications.jsonl')];assert len(journals)==1
 rows=[json.loads(s) for s in files[journals[0]].splitlines()]
 assert not any(r['event']=='error' for r in rows)
 console_name=next(n for n in files if n.endswith('/run/console.jsonl'))
 console=[json.loads(s) for s in files[console_name].splitlines()]
 gate=max(r['time'] for r in console if r['event']=='idle_gate')
 settled=next(r['time'] for r in console if r['event']=='selftest_pass' and r['time']>gate)
 assert min(r['time'] for r in rows if r['event']=='request')>=settled
 replies=[r for r in rows if r['event']=='reply'];assert all(r['status']==0 and not r['poisoned'] for r in replies)
 # Each module is matched to the independently archived bytes and manifest.
 for module in ('hello','network'):
  m=json.loads(files['bundle/'+module+'/manifest.json']);b=files['bundle/'+module+'/module.bin']
  assert hashlib.sha256(b).hexdigest()==m['sha256']
  assert m['base']==0xc0f50ca0 and m['board']==0x01601077 and m['abi']==1
 timers=json.loads(files['autonomous-timers.json'])
 assert timers['reconnected'] and timers['disconnect_events_after']>timers['disconnect_events_before'] and timers['module_calls_without_host_packets']>=20
 for family in (4,6):
  assert b'5 packets transmitted, 5 received, 0% packet loss' in files['ping%d.txt'%family]
  assert files['http%d.headers'%family].startswith(b'HTTP/1.0 200 OK')
  assert b'AcceleRAID 160' in files['http%d.html'%family] and b'Darth Vader' in files['http%d.html'%family]
 echo=json.loads(files['socket-echo.json']);assert len(echo)==2 and all(v['udp_echo'] and v['tcp_echo'] for v in echo.values())
 network_console=json.loads(files['network-console.json']);assert len(network_console)>=50 and all('error' not in r for r in network_console)
 result.update(network_console_exchanges=len(network_console),relay_reconnect=True,autonomous_module_calls=timers['module_calls_without_host_packets'],tun_ipv4_ipv6_ping_http=True,tun_udp_tcp_echo=True,
               hello_text=True,module_loads=3,zero_reservation_closes=2,general_heap_proofs=3,
               dual_stack_http_runs=2,application_replies=len(replies),network_left_running=True,
               new_stock_ram_reclaimed=False,unrestricted_task_containment=False)
 return result
if __name__=='__main__':print(json.dumps(replay(sys.argv[1]),indent=2))

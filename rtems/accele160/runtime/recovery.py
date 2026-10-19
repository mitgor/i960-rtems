#!/usr/bin/env python3
"""Explicit relay/process and interrupted-upload tests; never kill the PCI owner."""
import argparse,json,time,socket,struct,subprocess,urllib.request
from pathlib import Path
from service import Service
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root
s=Service();c=s.client;out={}
def save():(root/'recovery.json').write_text(json.dumps(out,indent=2)+'\n')
def cmd(*args):return subprocess.check_output(args,text=True).strip()
def route_remove():cmd('python3',str(root/'public_ipv6.py'),'remove')
def start_link():return cmd('bash',str(root/'start_link.sh'))
def http():
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://[fd96:196:960::2]/',timeout=5) as r:
  b=r.read();assert r.status==200 and b'AcceleRAID 160' in b;return len(b)
def refuse(op,data,status):
 try:c.call(op,data)
 except RuntimeError as e:
  assert isinstance(e.args[0],dict) and e.args[0]['status']==status;return e.args[0]
 raise AssertionError('operation unexpectedly accepted')
out['boot_before']=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
out['owner_pid_before']=cmd('systemctl','show','-p','MainPID','--value','i960-doom')
out['before']=c.call(7);out['occupied_upload_refused']=refuse(1,bytes(184),5);save()
# A client may disappear after publishing; the owner must retire its reply.
with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as peer:
 peer.connect('/run/i960-rtems-runtime.sock');peer.sendall(b'{"op":7}\n')
time.sleep(.3);out['abandoned_client_recovered']=c.call(7);save()
before=s.app(3,1);out['app_before_pause']=before;cmd('systemctl','kill','--kill-who=main','--signal=STOP','i960-rtems-ip')
try:
 with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as udp:
  udp.settimeout(.7);udp.sendto(b'paused-relay',( '10.196.0.2',9601))
  try:udp.recvfrom(1500)
  except TimeoutError:out['paused_packet_timed_out']=True
  else:raise AssertionError('paused relay unexpectedly delivered packet')
 out['console_during_pause']=s.console('tasks');assert 'fault=0' in out['console_during_pause']
 after=s.app(3,1);assert after['updates']>before['updates'] and after['generation']==before['generation'];out['app_during_pause']=after
finally:cmd('systemctl','kill','--kill-who=main','--signal=CONT','i960-rtems-ip')
out['http_after_resume']=http();save()
cmd('systemctl','kill','--kill-who=main','--signal=KILL','i960-rtems-ip')
for _ in range(50):
 if not Path('/sys/class/net/accele0').exists():break
 time.sleep(.1)
assert not Path('/sys/class/net/accele0').exists();out['tun_destroyed']=True
out['app_after_relay_death']=s.app(3,1);out['console_after_relay_death']=s.console('tasks')
route_remove();out['cleanup_without_tun']=True
out['broker_pid_before']=cmd('systemctl','show','-p','MainPID','--value','i960-combined')
cmd('systemctl','kill','--kill-who=main','--signal=KILL','i960-combined')
for _ in range(50):
 r=subprocess.run(['systemctl','show','-p','MainPID','--value','i960-combined'],capture_output=True,text=True)
 if r.stdout.strip() in ('','0'):break
 time.sleep(.1)
cmd('python3',str(root/'start_broker.py'),'--root',str(root))
for _ in range(50):
 try:out['query_after_broker_death']=c.call(7);break
 except (ConnectionRefusedError,FileNotFoundError):time.sleep(.1)
else:raise AssertionError('broker restart failed')
out['broker_pid_after']=cmd('systemctl','show','-p','MainPID','--value','i960-combined')
assert out['broker_pid_before']!=out['broker_pid_after']
out['link_restart']=start_link();out['http_after_relay_death']=http();save()
# A clean module close and abandoned partial upload must not jump to its code.
route_remove();cmd('systemctl','stop','i960-rtems-ip')
for i in (1,2):
 state=s.app(3,i);s.app(2,i,state['generation'])
out['close']=c.call(6);assert not out['close']['reservation']
m=json.loads((root/'bundle/network/manifest.json').read_text());b=(root/'bundle/network/module.bin').read_bytes()
words=[m['board'],m['abi'],m['base'],1,len(m['segments']),m['entry']]
for seg in m['segments']:words.extend(seg[k] for k in ('offset','file_bytes','memory_bytes','flags','crc32'))
words.extend([0]*(5*(8-len(m['segments']))))
out['partial_begin']=c.call(1,struct.pack('<46I',*words));out['partial_write']=c.call(2,struct.pack('<II',0,0)+b[:1016])
out['partial_start_refused']=refuse(4,b'',10);out['partial_query']=c.call(7)
assert out['partial_query']['state']==1 and not out['partial_query']['started']
out['console_during_partial']=s.console('tasks');assert 'fault=0' in out['console_during_partial']
out['partial_abort']=c.call(6);assert not out['partial_abort']['reservation'];save()
out['reload']=c.upload(root/'bundle/network');out['fresh_apps']=[s.app(3,i) for i in (1,2)]
assert all(not r['generation'] and not r['running'] and not r['requests'] for r in out['fresh_apps'])
for i in (1,2):s.app(1,i,0)
out['link_final']=start_link();out['http_final']=http();out['final']=c.call(7)
out['boot_after']=Path('/proc/sys/kernel/random/boot_id').read_text().strip();out['owner_pid_after']=cmd('systemctl','show','-p','MainPID','--value','i960-doom')
assert out['boot_before']==out['boot_after'] and out['owner_pid_before']==out['owner_pid_after']
save();print(json.dumps(dict(relay_pause_resume=True,relay_death_recovered=True,partial_upload_aborted=True,fresh_bss=True,same_boot_and_owner=True)))

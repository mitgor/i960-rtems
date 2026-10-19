#!/usr/bin/env python3
"""Replay packet-DMA and endurance evidence; does not execute captured code."""
import argparse,tarfile,json,hashlib,collections,struct,statistics,io
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--minimum-seconds',type=int,default=3600);a=p.parse_args()
with tarfile.open(a.archive) as t:f={m.name:t.extractfile(m).read() for m in t if m.isfile()}
j=lambda n:json.loads(f[n])
for n,h in j('bundle/bundle.json')['files'].items():assert hashlib.sha256(f['bundle/'+n]).hexdigest()==h,n
m=j('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
assert m['terminal_test']==5 and m['runtime_schema']==m['service_schema']==1
assert hashlib.sha256(f['bundle/kernel/kernel.bin']).hexdigest()==m['kernel_sha256']
paired=j('paired-under-load.json');assert paired['mode']=='dma-check' and len(paired['replies'])==200
assert all(r['transport']=='dma' and not r['poisoned'] and r['started'] for r in paired['replies'])
b=j('benchmark.json');assert b['paired_checks']==33 and len(b['rows'])>=352
for r in b['rows']:
 assert r['payload_bytes'] in (64,256,1024,1400) and r['reply_bytes']==r['payload_bytes']+32
 assert 0<r['ms']<5000 and r['owner_ms']>0
assert sum(r['mode']=='dma-check' for r in b['rows'])==32
assert all(sum(r['mode']==mode and r['payload_bytes']==n for r in b['rows'])>=40 for mode in ('pio','dma') for n in (64,256,1024,1400))
assert b['final']['transport']=='dma' and not b['final']['poisoned']
# Replay the actual raw-IP benchmark exchanges from the sole owner's journal.
# These use source UDP port 12346; endurance uses Linux ephemeral ports.
journal,= [n for n in f if n.endswith('/run/applications.jsonl')]
pending={};checked=collections.Counter();dma_endurance=0
e=j('endurance.json');lo=min(r['time'] for r in e['rows']);hi=max(r['time'] for r in e['rows'])
def checksum(data):
 if len(data)%2:data+=b'\0'
 v=sum(struct.unpack('!%dH'%(len(data)//2),data))
 while v>>16:v=(v&65535)+(v>>16)
 return (~v)&65535
for line in io.BytesIO(f[journal]):
 r=json.loads(line)
 if lo<=r.get('time',0)<=hi:
  assert r.get('event')!='error',r
  if r.get('event')=='reply' and r.get('transport')=='dma':
   assert not r['status'];dma_endurance+=1
 if r.get('event')=='request' and r.get('op')==5:
  packet=bytes.fromhex(r['data'])
  if len(packet)>=28 and packet[:1]==b'\x45' and packet[9]==17 and packet[20:24]==struct.pack('!HH',12346,9601):pending[r['seq']]=(packet,r['transport'])
 elif r.get('event')=='reply' and r['sequence'] in pending:
  request,mode=pending.pop(r['sequence']);data=bytes.fromhex(r['data']);assert not r['status']
  assert struct.unpack_from('<I',data)[0]==len(data)-4
  packet=data[4:];assert packet[0]==0x45 and packet[9]==17 and checksum(packet[:20])==0
  assert packet[12:16]==request[16:20] and packet[16:20]==request[12:16]
  assert packet[20:24]==struct.pack('!HH',9601,12346) and packet[28:]==request[28:]
  if packet[26:28]!=b'\0\0':assert checksum(packet[12:20]+struct.pack('!BBH',0,17,len(packet)-20)+packet[20:])==0
  assert r['transport']==('pio' if mode=='pio' else 'dma');checked[mode]+=1
assert not pending and checked=={'pio':160,'dma':160,'dma-check':32},checked
links=j('link-comparison.json');assert set(links)=={'pio','dma'}
for v in links.values():assert len(v['rows'])==20 and all(r['ms']<5000 and r['bytes']>2500 for r in v['rows']) and not v['net']['dropped']
s=j('endurance-summary.json');assert dma_endurance>10000
assert e['duration_s']>=a.minimum_seconds and s['duration_s']>=a.minimum_seconds and not e['errors'] and not s['errors']
counts=collections.Counter(r['kind'] for r in e['rows']);assert min(counts.values())>20 and s['events']==len(e['rows'])
for r in e['rows']:
 if r['kind'] in ('http','console'):assert r['ms']<5000
 if r['kind']=='echo':assert r['ms']<3000 and r['text']=='HELLO FROM CONCURRENT APP'
 if r['kind']=='restart':assert r['stale_stop']['status']==4 and r['stale_stop']['running']
q=j('concurrent-loan.json');assert q['bytes_written_and_verified']==6291424 and len(q['steps'])==192 and q['close_refused']['status']==12 and not q['release']['status']
end=j('endurance-health.json');final=j('final-health.json');assert end['relay_transport']=='dma'
for h in (end,final):
 assert h['net']['running'] and not h['net']['poisoned'] and not h['net']['dropped']
 assert 'fault=0' in h['tasks'] and 'guard_changes=0' in h['pin_status'] and 'retained=1' in h['pin_status']
 assert h['units']==['active']*3
assert end['boot']==final['boot'] and end['owner_pid']==final['owner_pid']
assert final['gateway']=='active'
r=j('recovery.json');reload=j('packet-reload.json')
assert r['boot_before']==r['boot_after']==final['boot'] and r['owner_pid_before']==r['owner_pid_after']==final['owner_pid']
assert r['paused_packet_timed_out'] and r['tun_destroyed'] and r['cleanup_without_tun']
assert r['occupied_upload_refused']['status']==5 and r['partial_start_refused']['status']==10
assert r['partial_query']['state']==1 and not r['partial_query']['started']
assert not r['close']['reservation'] and not r['partial_abort']['reservation']
assert r['broker_pid_before']!=r['broker_pid_after'] and r['http_final']>2500
assert all(not x['generation'] and not x['running'] and not x['requests'] for x in r['fresh_apps'])
assert reload['complete_page_comparisons'] and reload['after']['epoch']==reload['before']['epoch']+2
assert all(reload[k]['transport']=='dma' and reload[k]['started'] and not reload[k]['poisoned'] for k in ('before','after'))
assert final['relay_transport']=='pio', 'keep PIO default without a uniform DMA benefit'
assert b'Darth Vader' in f['global-http-final.html'] and b'200 OK' in f['global-http-final.headers']
print(json.dumps(dict(kernel_sha256=m['kernel_sha256'],packet_trials=len(b['rows']),raw_packet_replay=dict(checked),dma_replies_during_endurance=dma_endurance,paired_pages=235,benchmark=b['summary'],endurance_seconds=s['duration_s'],events=len(e['rows']),counts=dict(counts),max_ms=s['max_ms'],loan_max_ms=q['max_rpc_ms'],guards=True,prompt_and_http_restored=True,default_transport='pio',uniform_dma_speedup_proved=False),indent=2))

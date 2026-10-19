#!/usr/bin/env python3
"""Replay the combined-module batch; historical DMA evidence stays labelled."""
import json,sys,tarfile,hashlib,collections
from pathlib import Path

def verify(path):
 with tarfile.open(path) as t:f={m.name:t.extractfile(m).read() for m in t if m.isfile()}
 j=lambda n:json.loads(f[n])
 for name,digest in j('bundle/bundle.json')['files'].items():assert hashlib.sha256(f['bundle/'+name]).hexdigest()==digest,name
 m=j('bundle/network/manifest.json');assert hashlib.sha256(f['bundle/network/module.bin']).hexdigest()==m['sha256']
 e=j('endurance.json');summary=j('endurance-summary.json');assert not e['errors'] and not summary['errors'] and summary['duration_s']>=600
 rows=e['rows'];counts=collections.Counter(r['kind'] for r in rows)
 assert len(rows)>1000 and summary['events']>=len(rows)
 assert all(counts[k]>=20 for k in ('http','udp','console','counter','echo')) and counts['restart']>=5
 for r in rows:
  if r['kind'] in ('http','console'):assert r['ms']<5000
  if r['kind']=='echo':assert r['ms']<3000 and r['text']=='HELLO FROM CONCURRENT APP' and not r['status']
  if r['kind']=='restart':assert r['stale_stop']['status']==4 and r['stale_stop']['running']
 q=j('concurrent-loan.json');assert q['bytes_written_and_verified']==6291424 and len(q['steps'])==192
 assert q['close_refused']['status']==12 and all(not r['status'] and not r['poisoned'] for r in q['steps'])
 assert q['release']['status']==0
 r=j('recovery.json');assert r['boot_before']==r['boot_after'] and r['owner_pid_before']==r['owner_pid_after']
 assert r['occupied_upload_refused']['status']==5 and r['abandoned_client_recovered']['started']
 assert r['paused_packet_timed_out'] and r['app_during_pause']['updates']>r['app_before_pause']['updates']
 assert r['app_during_pause']['generation']==r['app_before_pause']['generation']
 assert r['tun_destroyed'] and r['cleanup_without_tun']
 assert r['broker_pid_before']!=r['broker_pid_after'] and r['query_after_broker_death']['started']
 assert not r['query_after_broker_death']['poisoned']
 import struct
 assert struct.unpack('<6I',bytes.fromhex(r['before']['data']))[2]==0
 broker=[json.loads(line) for line in f['broker-endurance.jsonl'].splitlines()]
 assert len(broker)>1000 and all(not x.get('error') for x in broker)
 assert j('failed-direct/endurance.json')['errors'], 'failed direct test must remain in evidence'
 assert all(r[k]>2500 for k in ('http_after_resume','http_after_relay_death','http_final'))
 assert r['partial_start_refused']['status']==10 and r['partial_query']['state']==1 and not r['partial_query']['calls']
 assert not r['partial_abort']['reservation'] and not r['partial_abort']['state']
 assert all(not a['generation'] and not a['running'] for a in r['fresh_apps'])
 assert r['final']['started'] and not r['final']['poisoned']
 final=j('final-status.json');assert not final['net']['dropped'] and final['net']['running'] and not final['net']['poisoned']
 assert all(a['running'] for a in final['apps']) and 'fault=0' in final['tasks']
 return dict(module_sha256=m['sha256'],same_kernel_boot=r['boot_after'],endurance_seconds=summary['duration_s'],counts=dict(counts),max_ms=summary['max_ms'],concurrent_loan_bytes=q['bytes_written_and_verified'],relay_pause_resume=True,relay_death_recovered=True,broker_death_recovered=True,partial_upload_never_executed=True,pristine_reload=True,services_running=True,packet_dma_enabled=False,arbitrary_concurrent_upload=False)
if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))

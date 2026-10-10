#!/usr/bin/env python3
"""Verify preserved dual-stack card runs offline; never accesses hardware."""
import argparse,hashlib,json,struct,tempfile
from pathlib import Path
from verify_artifacts import ROOT,extract,verify_close,validate,packets

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
 artifacts=ROOT/'artifacts/rtems-ipv6-20261011';code=(artifacts/'target/kernel.bin').read_bytes();report={}
 assert hashlib.sha256(code).hexdigest()=='739d896aec015febf8cb81f4dd6f59b7838846ce25a9f31ae884dc1c2e3d076d'
 with tempfile.TemporaryDirectory() as tmp:
  work=Path(tmp)
  for archive in sorted((artifacts/'captures').glob('*.tar.xz')):extract(archive,work)
  for request in sorted(work.rglob('request.json')):
   folder=request.parent;name=folder.relative_to(work).as_posix();meta=json.loads(request.read_text())
   assert meta['payload_sha256']==hashlib.sha256(code).hexdigest()
   assert meta['boot_id']=='a9429ca4-0144-452d-8a80-7189608ce99b'
   if folder.name in ('sigkill','sigterm','invalid-operation'):
    verify_close(folder/('after-kill-close' if folder.name=='sigkill' else 'close'))
    if folder.name=='invalid-operation':assert struct.pack('<I',0xf0050002) in (folder/'failure-000001/dram-hook-a5.bin').read_bytes()
    else:
     clean=json.loads((folder/('manual-cleanup.json' if folder.name=='sigkill' else 'cleanup.json')).read_text())
     assert clean.get('clean',True) and not clean.get('errors') and not clean.get('interface_present',False)
     assert json.loads((folder/'ipv6-cleanup.json').read_text())['clean']
    report[name]=dict(expected_interruption=True,restored=True);continue
   item=validate(folder,code,artifacts/'target/kernel.symbols');packet=packets(folder/'packets.pcap');item['packets']=packet
   assert all(packet['protocols'].get(key,0)>0 for key in ('1','17','6','ipv6_58','ipv6_17','ipv6_6'))
   clean=json.loads((folder/'cleanup.json').read_text());assert not clean['errors'] and not clean['interface_present']
   assert json.loads((folder/'ipv6-cleanup.json').read_text())['clean']
   if (folder/'http-result.json').exists():
    http=json.loads((folder/'http-result.json').read_text());body=(folder/'http-response.bin').read_bytes();assert len(body)==http['bytes'] and hashlib.sha256(body).hexdigest()==http['sha256']
    address='fd96:196:960::2' if http['ip_version']==6 else '10.196.0.2'
    assert any(s['sport']==80 and s['dst']==address and s['sha256']==http['sha256'] and s['bytes']==http['bytes'] for s in packet['streams'])
    qtype=b'\x00\x1c\x00\x01' if http['ip_version']==6 else b'\x00\x01\x00\x01'
    assert any(d['dest_port']==53 and bytes.fromhex(d['payload_hex']).endswith(qtype) for d in packet['dns'])
    item['http']=http
   if (folder/'stress-result.json').exists():
    stress=json.loads((folder/'stress-result.json').read_text());assert stress['elapsed_s']>=180
    assert any(s['src']=='fd96:196:960::2' and s['sport']==9600 and s['bytes']==stress['bytes'] and s['sha256']==stress['sha256'] for s in packet['streams']);item['stress']=stress
   if (folder/'deliberate-loss.json').exists():
    losses=json.loads((folder/'deliberate-loss.json').read_text());assert {x['ip_version'] for x in losses}=={4,6};assert packet['retransmitted_segments']>=2;item['loss_recovery']=True
   report[name]=item
  acceptance=json.loads((work/'cleanup6-tests/acceptance.json').read_text())
  assert all(acceptance[k]['network_restored'] for k in ('sigterm','sigkill'))
  expected={'local-dual','internet6-loss','ipv6-stress','launcher6-smoke','ipv4-regression','cleanup6-tests/sigterm','cleanup6-tests/sigkill','cleanup6-tests/invalid-operation'}
  assert set(report)==expected,(set(report),expected)
 result=dict(valid=True,payload_sha256=hashlib.sha256(code).hexdigest(),runs=report,cleanup_acceptance=acceptance)
 if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('Verified',len(report),'dual-stack experiments, including interrupted-session restoration.')
if __name__=='__main__':main()

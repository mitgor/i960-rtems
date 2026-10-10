#!/usr/bin/env python3
"""Recheck preserved RTEMS hardware evidence offline. Does not contact hardware."""
import argparse,gzip,hashlib,json,struct,sys,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rtems/transport'))
from run import verify_close
from validate_run import validate
from validate_packets import validate as packets
sys.path.insert(0,str(ROOT/'host/loadrun'))
from loadrun import verify as scalar_verify

def extract(archive,destination):
 with tarfile.open(archive) as tar:
  for member in tar.getmembers():
   path=Path(member.name)
   if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):raise ValueError('unexpected archive member '+member.name)
  tar.extractall(destination)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
 artifacts=ROOT/'artifacts/rtems-20261011';report={};payloads={}
 for f in artifacts.rglob('*.bin'):
  if '__pycache__' not in f.parts:payloads[hashlib.sha256(f.read_bytes()).hexdigest()]=f
 negative={'session-smoke','net-local','net-local2','invalid-operation','sigkill','sigterm'}
 with tempfile.TemporaryDirectory() as temp:
  work=Path(temp)
  for archive in sorted((artifacts/'captures').glob('*.tar.xz')):extract(archive,work)
  for req in sorted(work.rglob('request.json')):
   folder=req.parent;name=folder.relative_to(work).as_posix();meta=json.loads(req.read_text())
   assert meta['boot_id']=='a9429ca4-0144-452d-8a80-7189608ce99b'
   if 'image_sha256' not in meta:
    if not (folder/'payload.bin').exists():continue # Other application captures have their own validator.
    code=(folder/'payload.bin').read_bytes();assert hashlib.sha256(code).hexdigest()==meta['payload_sha256']
    result=scalar_verify(folder,code);expected={0:0x46600001,1:0xf0001234,2:0x46600030,3:0x46600003,4:0x46600004,5:0x46600005,6:0x46600006}[meta['argument']]
    assert result==expected and (folder/'unloaded.txt').exists();report[name]=dict(valid=True,result=hex(result),restored=True);continue
   if folder.name in negative:
    close=folder/('after-kill-close' if folder.name=='sigkill' else 'close');verify_close(close)
    detail={}
    if folder.name=='session-smoke':
     trace=gzip.decompress((folder/'trace.bin.gz').read_bytes());n=struct.unpack_from('<I',trace,8)[0];reply=trace[16+n:];assert struct.unpack_from('<3I',reply)==(0x314d5452,1,0);detail['worker_did_not_advance']=True
    if folder.name in ('net-local','invalid-operation'):
     fatal=0xf0060147 if folder.name=='net-local' else 0xf0050002
     source=folder/'close/dram-hook-a5.bin' if folder.name=='net-local' else folder/'failure-000001/dram-hook-a5.bin'
     assert struct.pack('<I',fatal) in source.read_bytes();detail['fatal']=hex(fatal)
    if folder.name=='sigkill':
     cleanup=json.loads((folder/'manual-cleanup.json').read_text());assert cleanup['clean'] and not cleanup['driver_bound'];detail['manual_cleanup']=True
    if folder.name=='sigterm':
     cleanup=json.loads((folder/'cleanup.json').read_text());assert cleanup['errors']==[] and not cleanup['interface_present'];detail['graceful_cleanup']=True
    report[name]=dict(expected_negative_test=True,restored=True,**detail);continue
   code=payloads[meta['payload_sha256']].read_bytes()
   symbols=artifacts/'final-net/kernel.symbols' if meta['payload_sha256']=='a56aedbb32d211dd5dccc2f7a6258c47acf1f11b3fb906f464258abcaf0a504d' else None
   item=validate(folder,code,symbols)
   if (folder/'packets.pcap').exists():
    packet_report=packets(folder/'packets.pcap');item['packet_validation']=packet_report
    if (folder/'http-result.json').exists():
     http=json.loads((folder/'http-result.json').read_text());raw=(folder/'http-response.bin').read_bytes();assert len(raw)==http['bytes'] and hashlib.sha256(raw).hexdigest()==http['sha256']
     assert any(s['sport']==80 and s['dst']=='10.196.0.2' and s['sha256']==http['sha256'] and s['bytes']==http['bytes'] for s in packet_report['streams'])
    if (folder/'stress-result.json').exists():
     stress=json.loads((folder/'stress-result.json').read_text());assert any(s['sport']==9600 and s['bytes']==stress['bytes'] and s['sha256']==stress['sha256'] for s in packet_report['streams'])
   report[name]=item
 result=dict(valid=True,runs=report)
 if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('Verified',len(report),'preserved RTEMS experiments; expected failed/interrupted experiments checked for restoration.')
if __name__=='__main__':main()

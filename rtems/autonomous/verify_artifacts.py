#!/usr/bin/env python3
"""Recheck web/autonomous evidence, preserving failed and interrupted outcomes."""
import argparse,gzip,hashlib,json,struct,sys,tempfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'rtems'));from verify_artifacts import extract
sys.path.insert(0,str(ROOT/'rtems/transport'));from run import verify_close
from validate_packets import validate as packets
import wire

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args();report={};artifacts=ROOT/'artifacts/rtems-web-autonomous-20261011'
 with tempfile.TemporaryDirectory() as tmp:
  for archive in sorted((artifacts/'captures').glob('*.tar.xz')):
   root=Path(tmp)/archive.name;root.mkdir();extract(archive,root)
   payloads={hashlib.sha256(f.read_bytes()).hexdigest():f for f in root.rglob('*.bin') if f.name in ('kernel.bin','payload.bin','inventory.bin')}
   for req in sorted(root.rglob('request.json')):
    folder=req.parent;name=archive.name+'/'+str(folder.relative_to(root));meta=json.loads(req.read_text())
    close=folder/'close'
    if not close.exists():close=folder/'after-kill-close'
    if not close.exists():
     if (folder/'response.bin').exists():
      # Inventory uses scalar BIO1; the baseline verifier owns this framing.
      sys.path.insert(0,str(ROOT/'host/loadrun'));from loadrun import verify
      code=(folder/'payload.bin').read_bytes();assert verify(folder,code)==0
      report[name]=dict(inventory=True,restored=True);continue
     if (folder/'error.json').exists():report[name]=dict(refused_before_session=True);continue
     raise AssertionError('No outcome evidence for '+name)
    log=(close/'result.txt').read_text()
    if 'SESSION FAILED: retained DMA/module' in log:
     assert (close/'stage-before-a5.bin').read_bytes()!=(close/'stage-restored-a5.bin').read_bytes()
     report[name]=dict(expected_failed_trial=True,retained=True,restored=False);continue
    verify_close(close)
    autonomous=meta.get('autonomous',False)
    if autonomous:assert 'AUTONOMOUS STOP verified before any RAM restoration' in log
    code=payloads[meta['payload_sha256']].read_bytes();image=wire.prepare(code);assert hashlib.sha256(image).hexdigest()==meta['image_sha256']
    original=(folder/'open/stage-before-a5.bin').read_bytes();records=[]
    trace=folder/'trace.bin.gz'
    if trace.exists():
     try:raw=gzip.decompress(trace.read_bytes())
     except EOFError:
      assert close.name=='after-kill-close',name
      raw=zlib.decompressobj(31).decompress(trace.read_bytes())
     off=0
     while off<len(raw):
      ns,n=struct.unpack_from('<QI',raw,off);off+=12;incoming=raw[off:off+n];off+=n
      size=struct.unpack_from('<I',raw,off)[0];off+=4;reply=raw[off:off+size];off+=size
      assert ns>0 and len(incoming)==n and len(reply)==size
      assert struct.unpack_from('<I',reply)[0] in (0x314d5452,0x31415452,0x31515249)
      records.append((incoming,reply))
    for audit in folder.glob('audit-*.bin.gz'):
     index=int(audit.name.split('-')[1].split('.')[0]);incoming,reply=records[index-1]
     block=wire.block(incoming,index);before=image[:wire.bio.OFFSET]+block+original[wire.bio.IMAGE_SIZE:]
     after=gzip.decompress(audit.read_bytes());assert wire.response(before,after+original[len(after):])==(0,reply)
    item=dict(restored=True,autonomous_stop=autonomous,trace_records=len(records),boot_id=meta['boot_id'])
    if (folder/'packets.pcap').exists():item['packets']=packets(folder/'packets.pcap')
    if (folder/'acceptance.json').exists():item['acceptance']=json.loads((folder/'acceptance.json').read_text())
    if (folder/'http-result.json').exists():
     result=json.loads((folder/'http-result.json').read_text());data=(folder/'http-response.bin').read_bytes();assert len(data)==result['bytes'] and hashlib.sha256(data).hexdigest()==result['sha256'];item['http']=result
    report[name]=item
 result=dict(valid=True,runs=report)
 if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('Verified',len(report),'web/autonomous captures; failed trials remain explicitly failed.')
if __name__=='__main__':main()

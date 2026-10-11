#!/usr/bin/env python3
"""Validate saved boot transitions and fresh production ownership."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import ROM_SHA
p=argparse.ArgumentParser();p.add_argument('initial',type=Path);p.add_argument('live',type=Path);p.add_argument('recovery',type=Path);p.add_argument('evidence',type=Path);a=p.parse_args()
boots=[(root/f'ownirq-boot-{i}.txt').read_text().strip() for i,root in enumerate([a.initial,a.live,a.recovery],1)]
assert len(set(boots))==3
for root,run,boot in [(a.initial,'ownirq-smoke/run-0',boots[0]),(a.live,'ownirq-refusal',boots[1]),(a.recovery,'ownirq-recovery/run-0',boots[2])]:assert json.loads((root/run/'request.json').read_text())['boot_id']==boot
out=a.recovery/'http-after-ownirq';r=json.loads((out/'request.json').read_text());assert r['autonomous'] and r['boot_id']==boots[2]
one=(out/'open/stage-before-a5.bin').read_bytes();two=(out/'open/stage-before-5a.bin').read_bytes();assert one==two and len(one)==524288 and hashlib.sha256(one).hexdigest()==ROM_SHA
assert 'experiment-result=0 pending=0;' in (out/'preflight/result.txt').read_text()
assert 'SESSION OPEN ready; original saved; no user callback armed' in (out/'open/result.txt').read_text()
state=(a.evidence/'service-state.txt').read_text();assert 'active\n' in state and 'drivers/dac960auto' in state and 'test-module-absent' in state and boots[2] in state
http=(a.evidence/'http-restored.txt').read_text();assert 'HTTP/1.0 200 OK' in http and 'Darth Vader' in http
print('Three distinct boots matching original sessions:',*boots,sep='\n')
print('Fresh autonomous preflight and paired pinned-original 512 KiB OPEN passed. Production active, test module absent, IPv6 HTTP 200 from Mac. Visitor logs excluded.')
print('Production payload SHA256:',r['payload_sha256']);print('Production module SHA256:',r['module_sha256'])

#!/usr/bin/env python3
"""Verify saved recovery boot and the fresh production open (not live traffic)."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import ROM_SHA,verify_close
p=argparse.ArgumentParser();p.add_argument('initial',type=Path);p.add_argument('recovery',type=Path);p.add_argument('evidence',type=Path);a=p.parse_args()
old=(a.initial/'ownership-boot-before.txt').read_text().strip();new=(a.recovery/'ownership-boot-after.txt').read_text().strip();assert old!=new
verify_close(a.initial/'http-after-containment-batch/close')
p=a.recovery/'http-after-ownership';identity=json.loads((p/'request.json').read_text());assert identity['boot_id']==new and identity['autonomous']
# Preflight exports allocated staging slots; only OPEN populates this snapshot.
first=(p/'open/stage-before-a5.bin').read_bytes();second=(p/'open/stage-before-5a.bin').read_bytes();assert first==second and len(first)==524288 and hashlib.sha256(first).hexdigest()==ROM_SHA
assert 'experiment-result=0 pending=0;' in (p/'preflight/result.txt').read_text()
assert 'SESSION OPEN ready; original saved; no user callback armed' in (p/'open/result.txt').read_text()
service=(a.evidence/'service-state.txt').read_text();assert 'active\n' in service and 'drivers/dac960auto' in service and 'test-module-absent' in service and new in service
http=(a.evidence/'http-restored.txt').read_text();assert 'HTTP/1.0 200 OK' in http and 'Darth Vader' in http
print('Pre-test production full close verified. Recovery boot changed:',old,'->',new)
print('Fresh autonomous preflight passed. Production OPEN: paired 512 KiB original snapshots verified; test module absent; production active; HTTP 200 from Mac.')
print('Production payload SHA256:',identity['payload_sha256']);print('Production module SHA256:',identity['module_sha256'])

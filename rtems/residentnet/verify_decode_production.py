#!/usr/bin/env python3
"""Verify saved production restoration and subsequent clean handoff, offline."""
import argparse,sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close,ROM_SHA
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('evidence',type=Path);a=p.parse_args();root=a.root;out=a.evidence
verify_close(root/'http-after-upload/close');verify_close(root/'http-after-decode/close')
id=json.loads((root/'http-after-decode/request.json').read_text())
x=(root/'http-after-decode/open/stage-before-a5.bin').read_bytes();y=(root/'http-after-decode/open/stage-before-5a.bin').read_bytes()
assert x==y and hashlib.sha256(x).hexdigest()==ROM_SHA
assert hashlib.sha256((root/'autonet/kernel.bin').read_bytes()).hexdigest()==id['payload_sha256']
assert hashlib.sha256((root/'autonet-module-system-info/dac960auto.ko').read_bytes()).hexdigest()==id['module_sha256']
assert '200 OK' in (out/'http-restored-headers.txt').read_text() and 'Vader' in (out/'http-restored.html').read_text()
print(json.dumps(dict(previous_close_verified=True,paired_original_RAM=True,payload_and_module_pinned=True,http200=True,vader=True,boot_id=id['boot_id'],subsequent_close_verified=True,current_owner='Separate callback raycaster experiment; do not interrupt it to restart this service'),indent=2))

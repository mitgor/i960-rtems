#!/usr/bin/env python3
"""Check preserved system-info binaries and full normal autonomous cleanup."""
import argparse,hashlib,json,sys,tarfile,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
import wire
from run import verify_close
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
with tarfile.open(a.archive) as t,tempfile.TemporaryDirectory() as tmp:
 def read(n):return t.extractfile(n).read()
 identity=json.loads(read('http-system-info/request.json'))
 code=read('autonet/kernel.bin');module=read('autonet-module-system-info/dac960auto.ko')
 for key,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:assert hashlib.sha256(data).hexdigest()==identity[key]
 assert identity['autonomous']
 close=Path(tmp)
 for member in t.getmembers():
  prefix='http-system-info/close/'
  if member.isfile() and member.name.startswith(prefix):
   name=member.name[len(prefix):];assert name and '/' not in name and name not in ('.','..')
   (close/name).write_bytes(read(member.name))
 verify_close(close)
 assert 'AUTONOMOUS STOP verified before any RAM restoration' in (close/'result.txt').read_text()
 tests=json.loads(read('sysinfo-http-tests.json'));assert tests['passed'] and tests['requests']==24
print('Verified exact kernel/prepared-image/module hashes, 24-request HTTP acceptance and full autonomous stop-before-restoration cleanup')

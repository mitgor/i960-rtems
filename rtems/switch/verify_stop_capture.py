#!/usr/bin/env python3
"""Verify STOP1 raw reports, pending-command evidence, identities and full cleanup."""
import argparse,hashlib,json,struct,sys,tarfile,tempfile
from pathlib import Path
from live_stop import decode_stop
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
import wire
from run import verify_close
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
with tarfile.open(a.archive) as t,tempfile.TemporaryDirectory() as tmp:
 def read(n):return t.extractfile(n).read()
 code=read('mustop/kernel.bin');module=read('mustop-module/dac960rtems.ko')
 rows=json.loads(read('mustop-live1/acceptance.json'));assert len(rows)==3
 for i,row in enumerate(rows):
  prefix=f'mustop-live1/run-{i}/';identity=json.loads(read(prefix+'request.json'))
  for key,data in [('payload_sha256',code),('module_sha256',module),('image_sha256',wire.prepare(code))]:
   assert hashlib.sha256(data).hexdigest()==identity[key],key
  raw=read(prefix+'stop.bin');assert decode_stop(raw)==row
  for index,value in ((1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,6)):
   bad=bytearray(raw);struct.pack_into('<I',bad,736+index*4,value)
   try:decode_stop(bad)
   except AssertionError:pass
   else:raise AssertionError(('accepted corrupt field',index))
  log=read(prefix+'stop-log.txt').decode()
  assert f'callback pending=1 sequence=1 delay_ms={(120,150,200)[i]} epoch={row["stop"]["epoch"]}' in log
  assert 'STOP1 DRAINED; callback pending=1 sequence=1; sending RELEASE' in log
  assert 'STOP1 callback returned; MU words/masks restored, host OISR acknowledged' in log
  before=json.loads(read(prefix+'mu-before.json'));after=json.loads(read(prefix+'mu-after.json'))
  for sample in after['samples']:
   for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
   for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
  close=Path(tmp)/str(i);close.mkdir()
  for m in t.getmembers():
   if m.isfile() and m.name.startswith(prefix+'close/'):
    name=m.name[len(prefix+'close/'):];assert name and '/' not in name and name not in ('.','..')
    (close/name).write_bytes(read(m.name))
  verify_close(close)
  summary=json.loads(read(prefix+'summary.json'));assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
print('Three STOP1 runs verified: pending callback, both ISR contexts live at STOP, drained before RELEASE, exact images, full RAM/MU restoration; 42 corrupted reports rejected')

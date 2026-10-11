#!/usr/bin/env python3
"""Verify nested STOP/deadline captures against exact images and full restoration."""
import argparse,hashlib,json,struct,sys,tarfile,tempfile
from pathlib import Path
from live_cases import decode_cases,check_log
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
import wire
from run import verify_close
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args();rejected=0
with tarfile.open(a.archive) as t,tempfile.TemporaryDirectory() as tmp:
 def read(n):return t.extractfile(n).read()
 code=read('stopcases/kernel.bin');module=read('stopcases-module/dac960rtems.ko')
 rows=json.loads(read('stopcases-live1/acceptance.json'));assert len(rows)==12
 assert {(r['repetition'],r['case']) for r in rows}=={(r,c) for r in range(3) for c in range(1,5)}
 for row in rows:
  mode=row['case'];rep=row['repetition'];prefix=f'stopcases-live1/run-{rep}-{mode}/'
  identity=json.loads(read(prefix+'request.json'))
  for key,data in [('payload_sha256',code),('module_sha256',module),('image_sha256',wire.prepare(code))]:assert hashlib.sha256(data).hexdigest()==identity[key]
  raw=read(prefix+'cases.bin');decoded=decode_cases(raw);decoded['repetition']=rep;assert decoded==row
  mutations=[(4,1),(736+13*4,0),(736+12*4,1 if mode==4 else 0),(736+14*4,0 if mode==3 else 6),(816+11*4,0),(816+12*4,1)]
  if mode<=2:mutations += [(816+5*4,0),(816+6*4,0),(816+10*4,0),(816+15*4,1),(816+17*4,0)]
  for offset,value in mutations:
   bad=bytearray(raw);struct.pack_into('<I',bad,offset,value)
   try:decode_cases(bad)
   except AssertionError:rejected+=1
   else:raise AssertionError(('accepted corruption',mode,offset))
  check_log(read(prefix+'stop-log.txt').decode(),mode,row['stop_words'][1])
  before=json.loads(read(prefix+'mu-before.json'));after=json.loads(read(prefix+'mu-after.json'))
  for sample in after['samples']:
   for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
   for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
  close=Path(tmp)/f'{rep}-{mode}';close.mkdir()
  for m in t.getmembers():
   if m.isfile() and m.name.startswith(prefix+'close/'):
    name=m.name[len(prefix+'close/'):];assert name and '/' not in name and name not in ('.','..')
    (close/name).write_bytes(read(m.name))
  verify_close(close)
  summary=json.loads(read(prefix+'summary.json'));assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
print(f'12 nested STOP/deadline runs verified; exact payload/module identity, deferred dispatch, expected timeout outcomes, full RAM/MU restoration; {rejected} corrupt reports rejected')

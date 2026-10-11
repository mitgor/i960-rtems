#!/usr/bin/env python3
import argparse,hashlib,json,sys,tarfile,tempfile
from pathlib import Path
from live_lifecycle import check_order
from live_stop import decode_stop
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close
import wire
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--initial',type=Path);a=p.parse_args()
with tarfile.open(a.archive) as t,tempfile.TemporaryDirectory() as tmp:
 def read(n):return t.extractfile(n).read()
 code=read('mustop/kernel.bin');module=read('lifecycle-module-v3/dac960rtems.ko')
 rows=json.loads(read('lifecycle-live2/acceptance.json'));assert len(rows)==6
 assert {(r['mode'],r['repetition']) for r in rows}=={(m,i) for m in ('close','unbind') for i in range(3)}
 for r in rows:
  mode=r['mode'];prefix=f"lifecycle-live2/run-{r['repetition']}-{mode}/"
  identity=json.loads(read(prefix+'request.json'))
  for k,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:assert hashlib.sha256(data).hexdigest()==identity[k]
  e=json.loads(read(prefix+'lifecycle.json'));assert e['restored'] and e['unloaded']
  check_order(mode,e['events']);assert e['events']==r['events']
  assert e['injection_events'][1]>0 and e['injection_events'][4]==0
  if mode=='close':assert e['fd_closed'] and e['after_injection'][3]==0
  else:
   assert e['after_injection'][2]>0 and e['after_injection'][6]==0
   f=e['final_events'];assert f[10]<f[3]<=f[11]<f[12] and f[7:9]==e['events'][7:9]
   assert e['late_ioctl']==11 and e['late_read']==5
  assert e['stop'][2]==1 and e['stop'][7]==1 and not(e['stop'][3]&1) and not(e['stop'][5]&1)
  assert e['stop'][6]==0x73000000|e['epoch']
  close=Path(tmp)/f"{r['repetition']}-{mode}";close.mkdir()
  for m in t.getmembers():
   if m.isfile() and m.name.startswith(prefix+'close/'):
    n=m.name[len(prefix+'close/'):];assert n and '/' not in n and n not in ('.','..');(close/n).write_bytes(read(m.name))
  verify_close(close)
  req=read(prefix+'input.bin');original=(close/'stage-before-a5.bin').read_bytes()
  after=(close/'payload-after-a5.bin').read_bytes();assert after==(close/'payload-after-5a.bin').read_bytes()
  status,data=wire.response(wire.prepare(code)[:wire.bio.OFFSET]+req+original[wire.bio.IMAGE_SIZE:],after+original[len(after):])
  assert status==0 and data==read(prefix+'stop.bin') and decode_stop(data)==r['report']
  assert r['report']['stop']['epoch']==e['epoch']
  before=json.loads(read(prefix+'mu-before.json'));after=json.loads(read(prefix+'mu-after.json'))
  for sample in after['samples']:
   for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
   for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
print('Six lifecycle runs verified: actual final user-fd close / driver unbind during active calls; ordered join/restore/unmap/free; paired target reports; exact images; full RAM/MU restoration')

if a.initial:
 with tarfile.open(a.initial) as t,tempfile.TemporaryDirectory() as tmp:
  prefix='lifecycle-live1/run-0-unbind/'
  def initial_read(n):return t.extractfile(n).read()
  close=Path(tmp)
  for m in t.getmembers():
   if m.isfile() and m.name.startswith(prefix+'close/'):
    n=m.name[len(prefix+'close/'):];assert n and '/' not in n and n not in ('.','..');(close/n).write_bytes(initial_read(m.name))
  log=(close/'result.txt').read_text();line=initial_read(prefix+'kernel-close.txt').decode()
  marker='SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0'
  assert marker not in log and marker in line
  (close/'result.txt').write_text(log+'\n'+line);verify_close(close)
  e=[int(x) for x in initial_read(prefix+'final-events.txt').decode().strip().split(',')]
  assert e[4]<e[5]<e[6]<e[7]<e[8]<e[9]<e[10]<e[3]<e[11]<e[12]
  print('Initial rejected unbind capture: original truncated log confirmed; paired restoration independently passes with separately saved kernel close line (temporary copy only)')

#!/usr/bin/env python3
"""Recheck original paired reports, C reclaim gate, exact builds and restoration."""
import argparse,gzip,hashlib,json,os,struct,subprocess,sys,tarfile,tempfile
from pathlib import Path
from live_contain import decode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close
import wire
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--critical',action='store_true');p.add_argument('--initial',action='store_true');a=p.parse_args()
profile='containcases' if a.critical else 'contain'
module_dir='containcases-module'+('' if a.initial else '-v2') if a.critical else 'contain-module'
live_dir='containcases-live'+('1' if a.initial else '2') if a.critical else 'contain-live1'
count=6 if a.critical else 3;words=256 if a.critical else 236
if a.critical:
 from live_contain_cases import decode
 from build_contain_cases import report_header
with tarfile.open(a.archive) as t,tempfile.TemporaryDirectory() as tmp:
 def read(n):return t.extractfile(n).read()
 code=read(profile+'/kernel.bin');module=read(module_dir+'/dac960rtems.ko')
 rows=json.loads(read(live_dir+'/acceptance.json'));assert len(rows)==count
 d=Path(tmp);raws=[]
 dis=read(profile+'/kernel.dis').decode();loop=dis[dis.index('<switch_loop>:'):dis.index('<switch_ac_bad>:')]
 assert '_switch_stop' not in loop and 'st\tr3,0x114(r4)' in loop and 'switch_loop' in loop
 assert '-DI960_CONTAIN_TEST' in json.loads(read(profile+'/build.json'))['flags']
 if a.critical:
  assert '-DI960_STOP_CASES' in json.loads(read(profile+'/build.json'))['flags']
  if not a.initial:
   assert 'frame size' not in read('containcases-v2-build.log').decode()
   assert 'words=kmalloc(256*sizeof(*words),GFP_KERNEL)' in read(module_dir+'/stage_rehearsal.h').decode()
 for i,row in enumerate(rows):
  prefix=f'{live_dir}/run-{i}/';identity=json.loads(read(prefix+'request.json'))
  for key,v in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:assert identity[key]==hashlib.sha256(v).hexdigest()
  raw=read(prefix+profile+'.bin');assert decode(raw)==row;raws.append(raw)
  trace=gzip.decompress(read(prefix+'trace.bin.gz'));elapsed,n=struct.unpack_from('<QI',trace);incoming=trace[12:12+n]
  assert n==12 and struct.unpack('<3I',incoming)==(0x31505453,row['epoch'],((1,2,1,2,1,2) if a.critical else (120,150,200))[i])
  size=struct.unpack_from('<I',trace,12+n)[0];assert size==words*4 and trace[16+n:]==raw
  original=read(prefix+'open/stage-before-a5.bin');before=wire.prepare(code,incoming)+original[wire.bio.IMAGE_SIZE:]
  first=read(prefix+'close/payload-after-a5.bin');second=read(prefix+'close/payload-after-5a.bin');assert first==second
  assert wire.response(before,first+original[len(first):])==(0,raw)
  assert gzip.decompress(read(prefix+'audit-000001.bin.gz'))==first
  e=json.loads(read(prefix+'control.json'));assert e['pending'] and e['status'][2]==e['reply'][2]==1
  assert not(e['status'][3]&1) and not(e['reply'][3]&1) and not(e['reply'][5]&1)
  assert e['status'][4]==0x71000000|row['epoch'] and e['reply'][6]==0x75000000|row['epoch'] and e['reply'][7]==1
  log=read(prefix+'control-log.txt').decode()
  assert log.count('CONCURRENT QUIESCED ioctl')==1 and 'CONCURRENT window closed/joined rc=0 done=1' in log
  assert log.index('CONTAIN verified suspended workers')<log.index('SESSION STEP sequence=1')
  close=d/str(i);close.mkdir()
  for m in t.getmembers():
   if m.isfile() and m.name.startswith(prefix+'close/'):
    name=m.name[len(prefix+'close/'):];assert name and '/' not in name and name not in ('.','..');(close/name).write_bytes(read(m.name))
  verify_close(close)
  summary=json.loads(read(prefix+'summary.json'));assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
  before_mu=json.loads(read(prefix+'mu-before.json'));after_mu=json.loads(read(prefix+'mu-after.json'))
  for sample in after_mu['samples']:
   for name in ('IMR1','OMR1','IIMR','OIMR'):assert sample[name]==before_mu['samples'][0][name]
   for name in ('IISR','OISR'):assert int(sample[name],16)&2==int(before_mu['samples'][0][name],16)&2
 # Also verify the production session was fully restored before these tests.
 production=d/'production-close';production.mkdir()
 production_prefix=('http-after-containment' if a.critical else 'http-after-failed-teardown')+'/close/'
 for m in t.getmembers():
  if m.isfile() and m.name.startswith(production_prefix):
   name=m.name.removeprefix(production_prefix);assert '/' not in name and name not in ('.','..');(production/name).write_bytes(read(m.name))
 verify_close(production)
 # Run the same C gate used by the Linux driver on original hardware reports.
 c=d/'gate.c';exe=d/'gate'
 if a.critical:(d/'contain_report.h').write_text(report_header())
 c.write_text('#include <stdio.h>\n#include "contain_report.h"\nint main(void){unsigned int w[236];while(fread(w,sizeof(w),1,stdin)==1)putchar(contain_report_valid(w,w[185])?\'1\':\'0\');return 0;}\n'.replace('236',str(words)).replace('contain_report_valid(w,w[185])','contain_cases_valid(w,w[185],w[236])' if a.critical else 'contain_report_valid(w,w[185])'))
 subprocess.run([os.environ.get('CC','cc'),'-fsanitize=address,undefined','-I'+str(Path(__file__).resolve().parent),str(c),'-o',str(exe)],check=True)
 assert subprocess.check_output([str(exe)],input=b''.join(raws))==b'1'*count
 # Critical negative cases applied to actual reports, not just a model fixture.
 bads=[]
 for raw in raws:
  for index,value in ([(1,1),(7,0),(8,0),(19,1),(27,0),(109,0),(197,0),(207,0),(215,0),(216,0),(217,0),(218,0),(221,0),(224,0),(225,0),(228,0),(229,0),(230,0),(231,0),(234,1)]+([(j,0 if struct.unpack_from('<I',raw,j*4)[0] else 1) for j in range(236,256)] if a.critical else [])):
   b=bytearray(raw);struct.pack_into('<I',b,index*4,value)
   try:decode(b)
   except AssertionError:pass
   else:raise AssertionError(('damaged actual report accepted',index))
   bads.append(bytes(b))
 assert subprocess.check_output([str(exe)],input=b''.join(bads))==b'0'*len(bads)
print(f'{count} original paired {profile} reports, exact binaries, pre-test production close, full RAM/MU restoration and unload verified; C ASan/UBSan and Python reject {len(bads)} damaged actual reports.')

#!/usr/bin/env python3
"""Replay archived physical captures, never execute archived source."""
import hashlib,json,struct,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'rtems/accele160/fault'))
from host import validate
sha=lambda b:hashlib.sha256(b).hexdigest()
STOCK='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
reports=[]
for mode in (1,2):
 archive=HERE/f'mode{mode}.tar.xz'
 if not archive.exists():continue
 with tarfile.open(archive) as t:
  def read(n):return t.extractfile(n).read()
  def js(n):return json.loads(read(n))
  names=set(t.getnames());count=0
  for name,digest in js('bundle/bundle.json')['files'].items():
   if 'bundle/'+name in names:assert sha(read('bundle/'+name))==digest,name;count+=1
   else:assert name=='inputs/freedoom1.wad'
  run,={n[:-len('/terminal/result.json')] for n in names if n.endswith('/run/terminal/result.json')}
  r=js(run+'/terminal/result.json');outer=js(run+'/result.json')
  manifest=js('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
  assert manifest['terminal_schema']==1 and manifest['terminal_test']==mode
  assert sha(read('bundle/kernel/kernel.bin'))==manifest['kernel_sha256']==outer['kernel_sha256']
  before=read(run+'/terminal/ready.bin');nonce=r['nonce'];validate(before,nonce,mode,False)
  assert read(run+'/terminal/stale.bin')[64:]==before[64:]
  b=read(run+'/terminal/terminal.bin');w=validate(b,nonce,mode,True)
  assert b==read(run+'/terminal/stable.bin')==read(run+'/terminal/after-stop.bin')
  assert r['retained'] and r['admission']['done']=='0' and r['admission']['released']=='0'
  assert r['pin']['guard_changes']=='0' and r['pin']['retained']=='1'
  ready=read(run+'/persist/ready-page.bin');bank=struct.unpack_from('<16I',ready,0xb00)
  assert bank[:3]==(0x314b4e42,0,2048) and bank[3]==0x800000
  assert bank[4]==bank[5]==bank[6] and bank[7:11]==(2048,0,2048,0)
  assert bank[12:14]==(0,0) and bank[14]==bank[15]
  claim=struct.unpack_from('<16I',ready,0xb40)
  assert claim[:4]==(0x314d5241,2048,0x833aedc5,0) and claim[6]==0
  for i in (0,1):
   d=run.rsplit('/run',1)[0]+f'/pre-{i}'
   assert sha(read(d+'/data.bin'))==STOCK
   status=dict(x.split('=') for x in read(d+'/status.txt').decode().split())
   assert all(status[k]=='0' for k in ('status','residual','guard_changes'))
   assert js(d+'/request.json')['boot_id']==outer['boot_id']
  for idx in (16,17,20,24,25,26,28,31,32,38,48,64):
   bad=bytearray(b);bad[idx*4]^=1
   try:validate(bad,nonce,mode,True)
   except AssertionError:pass
   else:raise AssertionError('tamper accepted')
  reports.append(dict(mode=mode,boot_id=outer['boot_id'],kernel_sha256=outer['kernel_sha256'],
   bundle_files_verified=count,ticks=w[27],code=hex(w[20]),guards_intact=bool(w[26]),
   original_fp=hex(w[21]),original_sp=hex(w[22]),nmi=hex(w[34]),isp=hex(w[33]),
   fault_table_entries=[hex(x) for x in w[80:144]],stable=True,retained=True,
   firmware_prechecks=True,post_reset_verified=False))
# Close the preceding service using final raw QUIE/ACK and mode-1 fresh reads.
with tarfile.open(HERE/'previous-service-final.tar.xz') as t:
 name,=[n for n in t.getnames() if n.endswith('/persist/quiescent-page.bin')]
 b=t.extractfile(name).read()
 assert struct.unpack_from('<2I',b,0xb54)==(0x45495551,0)
 assert struct.unpack_from('<I',b,0xa54)[0]==0x214b4341
 previous=json.loads((HERE/'previous-service-shutdown.json').read_text())
 assert previous['boot_id']!=reports[0]['boot_id'] and previous['grant_retained']
if len(reports)==2:
 assert reports[0]['boot_id']!=reports[1]['boot_id'];reports[0]['post_reset_verified']=True
prepared=None
if (HERE/'mode0-prepared.tar.xz').exists():
 with tarfile.open(HERE/'mode0-prepared.tar.xz') as t:
  names=set(t.getnames());inventory=json.load(t.extractfile('bundle/bundle.json'));count=0
  for name,digest in inventory['files'].items():
   if 'bundle/'+name in names:assert sha(t.extractfile('bundle/'+name).read())==digest;count+=1
   else:assert name=='inputs/freedoom1.wad'
  m=json.load(t.extractfile('manifest-mode0.json'))
  assert m['terminal_schema']==1 and m['terminal_test']==0
  assert sha(t.extractfile('bundle/kernel/kernel.bin').read())==m['kernel_sha256']
  prepared=dict(kernel_sha256=m['kernel_sha256'],bundle_files_verified=count,full_shutdown_qualification=False)
if (HERE/'mode0-live.tar.xz').exists():
 with tarfile.open(HERE/'mode0-live.tar.xz') as t:
  names=t.getnames();runs={n.rsplit('/pre-0/',1)[0] for n in names if n.endswith('/pre-0/data.bin')}
  assert len(runs)==1;session=runs.pop();boots=[]
  for i in (0,1):
   d=session+f'/pre-{i}'
   assert sha(t.extractfile(d+'/data.bin').read())==STOCK
   status=dict(x.split('=') for x in t.extractfile(d+'/status.txt').read().decode().split())
   assert all(status[k]=='0' for k in ('status','residual','guard_changes'))
   boots.append(json.load(t.extractfile(d+'/request.json'))['boot_id'])
  assert boots[0]==boots[1] and boots[0]!=reports[1]['boot_id']
  reports[1]['post_reset_verified']=True;reports[1]['post_reset_boot_id']=boots[0]
  assert sha(t.extractfile('bundle/kernel/kernel.bin').read())==prepared['kernel_sha256']
  prepared['normal_runtime_capture']='mode0-live.tar.xz; verify_normal.py'
  prepared['full_shutdown_qualification']=False # complete qualification still needs global STOP/reset
print(json.dumps(dict(previous_service_shutdown_and_reset_verified=True,runs=reports,prepared_mode0=prepared),indent=2))

#!/usr/bin/env python3
"""Verify immutable new-card frame evidence and summarize disjoint delays."""
import hashlib,json,statistics,struct,tarfile,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def fnv(b):
 h=2166136261
 for v in b:h=((h^v)*16777619)&0xffffffff
 return h
def summary(v):
 v=sorted(v);return dict(count=len(v),mean=statistics.mean(v),p50=statistics.median(v),p95=v[int((len(v)-1)*.95)],min=v[0],max=v[-1])
with tempfile.TemporaryDirectory(prefix='i960-delay-replay-') as d:
 with tarfile.open(root/'new-card-evidence.tar.gz') as t:t.extractall(d,filter='data')
 d=Path(d);run=d/'i960-card-delay-20261017-run';p=run/'persist';http=d/'i960-card-delay-20261017-http-static'
 result=json.loads((run/'result.json').read_text());m=json.loads((root/'source/profile-manifest.json').read_text())
 assert sha((root/'source/app.c').read_bytes())==m['source_sha256']
 for name,key in [('image.bin','image_sha256'),('kernel.bin','kernel_sha256')]:
  assert sha((d/'i960-card-delay-20261017-build'/name).read_bytes())==m[key]==result[key]
 receipts=json.loads((p/'live-frame-receipts.json').read_text());web=json.loads((http/'result.json').read_text())
 assert len(receipts)==len(web['frames'])==32 and not web['key_down'] and not web['key_up']
 by={r['generation']:r for r in receipts};assert sorted(by)==list(range(1,33))
 for gen,r in by.items():
  b=(p/'live-frames'/f'frame-{gen:04d}.bin').read_bytes()
  assert len(b)==65536 and sha(b)==r['sha256'] and f'0x{fnv(b):08x}'==r['fnv']
  assert r['slot']==((gen-1)&1)
  ref=root.parent/'accele160-doom-live-20261017/accepted-1/persist/live-frames'/f'frame-{gen:04d}.bin'
  assert b[:64768]==ref.read_bytes()[:64768],f'pixel/palette change at {gen}'
 for r in web['frames']:
  b=(http/f"http-frame-{r['generation']:04d}.bin").read_bytes()
  assert len(b)==65568 and struct.unpack_from('<8I',b)==(0x31424644,1,r['epoch'],r['generation'],320,200,65536,0)
  assert sha(b[32:])==r['sha256']==by[r['generation']]['sha256']
 reads=json.loads((p/'engine-reads.json').read_text());assert len(reads)==5045
 oracle=(root.parent/'accele160-doom-first-frame-20261017/native-requests.bin').read_bytes()
 for i,r in enumerate(reads[:5043]):assert (r['offset'],r['n'])==struct.unpack_from('<II',oracle,8*i)
 f=(p/'game-frame.bin').read_bytes();assert f==(p/'live-frames/frame-0032.bin').read_bytes()
 assert struct.unpack_from('<4I',f,64896)==(0x31464f50,1,31,100)
 entries=struct.unpack_from('<32I',f,64768)
 phases=list(struct.iter_unpack('<4I',f[64912:64912+31*16]))
 stats={}
 for j,name in enumerate(('slot_wait','contiguous_copy','odd_page_staging','card_fnv')):
  values=[10*(row[j]-(entries[i] if j==0 else row[j-1])) for i,row in enumerate(phases)]
  assert min(values)>=0;stats[name+'_ms']=summary(values)
 stats['engine_between_callbacks_ms']=summary([10*(entries[i+1]-row[3]) for i,row in enumerate(phases)])
 stats['card_frame_interval_ms']=summary([10*(entries[i]-entries[i-1]) for i in range(1,32)])
 for key in ('pci_read_ns','host_fnv_ns','save_and_http_ns','observed_to_http_ns','ack_write_ns'):
  stats[key.replace('_ns','_ms')]=summary([r[key]/1e6 for r in receipts])
 stats['observer_poll_and_fetch_ms']=summary([(r['received_monotonic_ns']-by[r['generation']]['observed_ns'])/1e6 for r in web['frames']])
 stats['http_observer_fps']=31e9/(web['frames'][-1]['received_monotonic_ns']-web['frames'][0]['received_monotonic_ns'])
 stats['card_fps']=result['frame_timing']['render_fps'];stats['engine_entry_to_first_http_s']=receipts[0]['engine_elapsed_s']
 page=(p/'quiescent-page.bin').read_bytes();assert struct.unpack_from('<II',page,0xb54)==(0x45495551,0)
 assert result['old']['driver'] is None and struct.unpack_from('<I',page,0xcc0+56)[0]==0
 stats['evidence']=dict(frames=32,phase_samples=31,native_requests=5043,total_requests=5045,
                       identical_baseline_pixels_and_palette=True,full_runtime_audits=True,boot_id=result['boot_id'])
 stock='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
 for stage in ('pre','post'):
  boots=[]
  for i in (0,1):
   audit=root/'new-card'/f'{stage}-{i}'
   req=json.loads((audit/'request.json').read_text());check=json.loads((audit/'result.json').read_text())
   assert req['selector']==9 and req['length']==1048576
   assert check['bytes']==1048576 and check['sha256']==stock
   assert check['old_after']['driver'] is None
   assert (audit/'status.txt').read_text().strip()=='done=1 status=0 residual=0 selector=9 length=1048576 released=0 guard_changes=0'
   boots.append(req['boot_id'])
  assert boots[0]==boots[1]
  if stage=='pre':assert boots[0]==result['boot_id']
  else:assert boots[0]!=result['boot_id']
 inventory=json.loads((root/'final-inventory.json').read_text())
 assert inventory['old']['driver'] is None and inventory['new']['driver'] is None
 assert inventory['boot_id']==boots[0]
 stats['evidence']['paired_pre_post_flash_audits']=True
 (root/'new-card-measurements.json').write_text(json.dumps(stats,indent=2)+'\n')
 print(json.dumps(stats,indent=2))

#!/usr/bin/env python3
"""Replay frozen service kernel, console, frame/WAD and terminal ownership proof."""
import hashlib,json,struct,tarfile,zipfile,sys,copy
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'rtems/accele160/service'))
STOCK='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
sha=lambda b:hashlib.sha256(b).hexdigest()
def fnv(b):
 h=2166136261
 for x in b:h=((h^x)*16777619)&0xffffffff
 return h

def frame(row,b):
 n=row['generation'];slot=row['slot']
 assert slot==(row['local_frame']-1)&1
 assert len(b)==77824 and b[:4096]==b'\xa5'*4096 and b[69664:]==b'\xa5'*8160
 assert struct.unpack_from('<8I',b,69632)==(0x31505044,0x161610e1,n,slot,65536,row['source'],row['card_tick'],(~n)&0xffffffff)
 image=b[4096:69632];assert sha(image)==row['sha256'] and fnv(image)==int(row['fnv'],16)
 return image

def console(r):
 b=bytes.fromhex(r['wire']);assert len(b)==896
 w=struct.unpack_from('<32I',b)
 assert w[16]==r['seq'] and w[24]==0x31435653 and 0<w[19]<=768
 assert w[17]==r.get('expected',r.get('status'))
 text=b[128:128+w[19]].decode('ascii')
 if r['event']=='reply':assert w[18]==r['epoch'] and text==r['text']
 if w[17]:assert text==f'error={w[17]}\n'
 elif r.get('opcode')==2:assert text=='RTEMS 4.6.6 / AcceleRAID160 / SVC1\n'
 elif r.get('opcode')==3:assert text==f'ticks={w[20]}\ntick_ms=10\n'

with zipfile.ZipFile(ROOT/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as z:
 name,=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];wad=z.read(name)
assert sha(wad)=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
with tarfile.open(HERE/'acceptance-1.tar.xz') as t:
 def read(n):return t.extractfile(n).read()
 def js(n):return json.loads(read(n))
 def lines(n):return [json.loads(x) for x in read(n).splitlines()]
 inventory=js('bundle/bundle.json');available=set(t.getnames());verified=0
 for name,digest in inventory['files'].items():
  member='bundle/'+name
  if member in available:assert sha(read(member))==digest,name;verified+=1
  else:assert name=='inputs/freedoom1.wad'
 manifest=js('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
 assert manifest['service_schema']==1 and manifest['persistent'] and manifest['reusable']
 assert sha(read('bundle/kernel/kernel.bin'))==manifest['kernel_sha256']
 session,={n.split('/run/')[0] for n in available if n.endswith('/run/result.json')}
 run=session+'/run';r=js(run+'/result.json')
 assert r['kernel_sha256']==manifest['kernel_sha256'] and r['release']=='reboot-only'
 assert r['frames']==r['dma_frames']==128 and len(r['games'])==2
 assert r['card']['ids']==[4201,80,4201,84] and r['old']['driver'] is None
 for i in (0,1):
  d=session+f'/pre-{i}';assert sha(read(d+'/data.bin'))==STOCK
  assert js(d+'/request.json')['boot_id']==r['boot_id']
  s=dict(x.split('=') for x in read(d+'/status.txt').decode().split())
  assert all(s[k]=='0' for k in ('status','residual','guard_changes'))
 oracle=list(struct.iter_unpack('<II',read('bundle/inputs/native-requests.bin')))
 total=0;reads_total=0;pio=0;frames_first=[]
 for game in (1,2):
  d=run+f'/persist/game-{game:04d}';g=js(d+'/game-result.json')
  assert g['idle_verified'] and g['frames']==64 and g['reason']=='frame limit'
  rows=lines(d+'/live-frame-receipts.jsonl');assert len(rows)==64
  for local,row in enumerate(rows,1):
   assert row['generation']==total+local and row['local_frame']==local and row['game_run']==game
   b=read(d+f'/dma-frame-{row["generation"]:04d}.bin');image=frame(row,b)
   assert image==read(d+f'/live-frames/frame-{row["generation"]:04d}.bin')
   if game==1:frames_first.append(image[:64768])
   else:assert image[:64768]==frames_first[local-1],f'deterministic repeat frame {local}'
   if local<=32:assert row['paired_pio'];pio+=1
   if local==1:
    for offset in (0,4096,69632,77823):
     bad=bytearray(b);bad[offset]^=1
     try:frame(row,bad)
     except AssertionError:pass
     else:raise AssertionError('frame tamper accepted')
  reads=lines(d+'/engine-reads.jsonl');assert len(reads)==g['wad_reads']
  assert [(x['offset'],x['n']) for x in reads[:len(oracle)]]==oracle
  for row in reads:
   block=wad[row['offset']:row['offset']+row['n']]
   assert sha(block)==row['source_sha256'] and fnv(block)==int(row['source_fnv'],16)
  idle=read(d+'/idle-verified.bin');b=struct.unpack_from('<32I',idle,0xb80)
  assert b[17]==1 and b[20]==game and b[21]==1 and b[25]==b[26] and not b[27]&1
  dma=struct.unpack_from('<32I',idle,0xd80)
  assert dma[:3]==(0x31464d44,0x161610e1,0) and dma[11]==total+64 and dma[14:16]==(0,0)
  er=struct.unpack_from('<16I',idle,0xc40);assert er[9:11]==(0,1) and er[11]==er[12]
  total+=64;reads_total+=len(reads)
 final=read(run+'/persist/quiescent-page.bin')
 assert struct.unpack_from('<2I',final,0xb54)==(0x45495551,0)
 assert struct.unpack_from('<I',final,0xa54)[0]==0x214b4341
 receipts=js(run+'/persist/bridge-receipts.json')
 assert sum(x['op']==8 and x['status']==0 for x in receipts)==1
 for code in (40,42,43,44,45):assert sum(x['op']==8 and x['status']==code for x in receipts)==2
 rows=lines(run+'/console.jsonl');lat=[];commands=set()
 for row in rows:
  if row['event'] in ('reply','selftest'):console(row)
  if row['event']=='reply':lat.append(row['latency_ms']);commands.add(row['command'])
 assert len([x for x in rows if x['event']=='selftest_pass'])==3
 assert commands=={'help','version','uptime','tasks','mem','apps','stats'}
 sample=next(x for x in rows if x['event']=='reply')
 for offset in (64,72,76,96,128):
  bad=copy.deepcopy(sample);b=bytearray.fromhex(bad['wire']);b[offset]^=1;bad['wire']=b.hex()
  try:console(bad)
  except (AssertionError,UnicodeError):pass
  else:raise AssertionError('console tamper accepted')
 report=dict(boot_id=r['boot_id'],bundle_files_verified=verified,kernel_sha256=r['kernel_sha256'],frames=total,
  repeat_pixels_palette_exact=True,paired_pio_frames=pio,wad_reads_replayed=reads_total,
  console_replies=len(lat),console_selftest_gates=3,console_latency_ms=dict(min=min(lat),median=sorted(lat)[len(lat)//2],max=max(lat)),
  final_global_stop=True,post_reset_flash_pair=False,host_oversize_close_issue_fixed_in_followup=True)
 if (HERE/'post-0/data.bin').exists():
  boots=[]
  for i in (0,1):
   d=HERE/f'post-{i}';assert sha((d/'data.bin').read_bytes())==STOCK
   s=dict(x.split('=') for x in (d/'status.txt').read_text().split())
   assert all(s[k]=='0' for k in ('status','residual','guard_changes'))
   boot=json.loads((d/'request.json').read_text())['boot_id'];assert boot!=r['boot_id'];boots.append(boot)
  assert boots[0]==boots[1];report['post_reset_flash_pair']=True;report['post_reset_boot_id']=boots[0]
 print(json.dumps(report,indent=2))

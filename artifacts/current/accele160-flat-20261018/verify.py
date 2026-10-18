#!/usr/bin/env python3
"""Replay the full four-game flat-plane acceptance and predeclared FPS windows."""
import argparse,hashlib,json,struct,sys,tarfile,zipfile,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'rtems/residentnet'))
from presentation_profile import decode
sha=lambda b:hashlib.sha256(b).hexdigest()
STOCK='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
def fnv(b):
 h=2166136261
 for v in b:h=((h^v)*16777619)&0xffffffff
 return h
def frame(row,b,source):
 n=row['generation'];slot=row['slot']
 assert len(b)==77824 and b[:4096]==b'\xa5'*4096 and b[69664:]==b'\xa5'*8160
 assert slot==(row['local_frame']-1)&1 and row['source']==source+slot*65536
 assert struct.unpack_from('<8I',b,69632)==(0x31505044,0x161610e1,n,slot,65536,row['source'],row['card_tick'],(~n)&0xffffffff)
 raw=b[4096:69632];assert sha(raw)==row['sha256'] and fnv(raw)==int(row['fnv'],16)
 return raw
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=HERE/'acceptance-pre-reset.tar.xz');a=p.parse_args()
with zipfile.ZipFile(ROOT/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as z:
 name,=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];wad=z.read(name)
assert sha(wad)=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
with tarfile.open(a.archive) as t:
 contents={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
 def read(n):return contents[n]
 def js(n):return json.loads(read(n))
 def lines(n):return [json.loads(x) for x in read(n).splitlines()]
 session,={n.split('/run/')[0] for n in t.getnames() if n.endswith('/run/result.json')};run=session+'/run'
 result=js(run+'/result.json');options=js('bundle/engine/manifest.json')
 inventory=js('bundle/bundle.json');covered=0
 for name,digest in inventory['files'].items():
  member='bundle/'+name
  if member in contents:assert sha(read(member))==digest,name;covered+=1
 assert sha(read('bundle/kernel/kernel.bin'))==result['kernel_sha256']
 assert sha(read('bundle/kernel/image.bin'))==result['image_sha256']
 assert sha(read('bundle/engine/template.bin'))==options['template_sha256']
 assert result['reusable'] and result['frames']==result['dma_frames']==512 and len(result['games'])==4
 assert options['runtime_flat'] and options['low_detail'] and not options['runtime_half_height']
 for i in (0,1):
  d=session+f'/pre-{i}';assert sha(read(d+'/data.bin'))==STOCK
  state=dict(x.split('=') for x in read(d+'/status.txt').decode().split());assert all(state[k]=='0' for k in ('status','residual','guard_changes'))
  assert js(d+'/request.json')['boot_id']==result['boot_id']
 oracle=list(struct.iter_unpack('<II',read('bundle/inputs/native-requests.bin')))
 ready=read(run+'/persist/ready-page.bin');claim=struct.unpack_from('<16I',ready,0xb40)
 allrows=[];samples=[];allreads=0;last_request=None
 for game in range(1,5):
  d=run+f'/persist/game-{game:04d}';rows=lines(d+'/live-frame-receipts.jsonl');g=js(d+'/game-result.json')
  assert len(rows)==g['frames']==128 and g['idle_verified'] and g['reason']=='frame limit'
  for local,row in enumerate(rows,1):
   assert row['local_frame']==local and row['generation']==len(allrows)+local and row['game_run']==game
   blob=read(d+f'/dma-frame-{row["generation"]:04d}.bin');raw=frame(row,blob,claim[7]+options['play_offset'])
   assert raw==read(d+f'/live-frames/frame-{row["generation"]:04d}.bin')
   profile=decode(raw,local,options=options);assert profile==row['profile']
   if local<=32:assert row['paired_pio']
   if local<=8:assert profile['flat_planes']==0
   if local>=32:assert profile['flat_planes']==int(game in (2,3)) and profile['flat_switches']==(2 if game==1 else 1 if game in (2,3) else 0)
  if game==1:
   assert {r['profile']['flat_planes'] for r in rows[:32]}=={0,1}
   first=read(d+'/dma-frame-0001.bin')
   for off in (0,4096,69632,77823):
    changed=bytearray(first);changed[off]^=1
    try:frame(rows[0],changed,claim[7]+options['play_offset'])
    except AssertionError:pass
    else:raise AssertionError('mutated capture accepted')
  idle=read(d+'/idle-verified.bin');c=struct.unpack_from('<16I',idle,0xb40);b=struct.unpack_from('<32I',idle,0xb80)
  assert c[:4]==claim[:4] and c[7:]==claim[7:] and c[6]==0 and b[17]==1 and b[25]==b[26] and not b[27]&1
  er=struct.unpack_from('<16I',idle,0xc40);assert er[9:11]==(0,1) and er[11]==er[12]
  assert sha(read(d+'/game-frame.bin'))==rows[-1]['sha256']
  if game in (1,2):
   native='native-transition' if game==1 else 'native-flat'
   proof=js(native+'/verification.json');assert proof['repeated_frames']==52 and proof['stop_and_heap_drain']
   for local in range(1,53):
    raw=read(d+f'/live-frames/frame-{rows[local-1]["generation"]:04d}.bin')
    reference=read(native+f'/frame-{local}.bin')
    assert [i for i in range(64768) if raw[i]!=reference[i]]==[29260,29261,29580,29581]
    assert proof['mode_sequence'][local-1]==rows[local-1]['profile']['flat_planes']
  reads=lines(d+'/engine-reads.jsonl');assert len(reads)==g['wad_reads']
  assert [(r['offset'],r['n']) for r in reads[:len(oracle)]]==oracle
  for row in reads:
   if last_request is not None:assert row['request_seq']==last_request+1
   last_request=row['request_seq'];data=wad[row['offset']:row['offset']+row['n']]
   assert sha(data)==row['source_sha256'] and fnv(data)==int(row['source_fnv'],16)
  allreads+=len(reads)
  window=rows[39:119];assert len(window)==80
  dt=window[-1]['card_tick']-window[0]['card_tick']
  sample=dict(game=game,mode='flat' if game in (2,3) else 'textured',frames=len(window),fps=7900/dt,
   render_ms=statistics.mean(r['profile']['render_ms'] for r in window),planes_ms=statistics.mean(r['profile']['planes_ms'] for r in window),
   cpu_render_ms=10*statistics.mean(r['profile']['cpu_samples']['render'] for r in window),
   cpu_planes_ms=10*statistics.mean(r['profile']['cpu_samples']['planes'] for r in window),
   startup_s=(rows[0]['card_tick']-er[2])/100)
  samples.append(sample);allrows.extend(rows)
 receipts=js(run+'/persist/bridge-receipts.json')
 assert sum(r['op']==8 and r['status']==0 for r in receipts)==3
 for code in (40,42,43,44,45):assert sum(r['op']==8 and r['status']==code for r in receipts)==4
 assert sum(r['op']==7 and r['status']==20 for r in receipts)==4
 final=read(run+'/persist/quiescent-page.bin');assert struct.unpack_from('<2I',final,0xb54)==(0x45495551,0)
 assert final[0xb00:0xb40]==ready[0xb00:0xb40] and result['wad_good']==38+allreads and result['wad_bad']==4
 http=json.loads((HERE/'http/observations.json').read_text())
 for row in http['frames']:assert row['sha256']==allrows[row['generation']-1]['sha256'] and row['flat_planes']==allrows[row['generation']-1]['profile']['flat_planes']
 aggregate={mode:{key:statistics.mean(x[key] for x in samples if x['mode']==mode) for key in ('fps','render_ms','planes_ms','cpu_render_ms','cpu_planes_ms')} for mode in ('textured','flat')}
 report=dict(boot_id=result['boot_id'],frames=len(allrows),paired_pio_frames=128,rearms=3,stale_rearm_rejections=20,
  wad_reads=allreads,http_samples=len(http['frames']),native_oracle_reads_per_game=len(oracle),samples=samples,aggregate=aggregate,
  fps_gain_percent=(aggregate['flat']['fps']/aggregate['textured']['fps']-1)*100,
  full_ownership_and_system_audits=True,mode_switch_back_tested=True,verified_bundle_members=covered,native_card_frames=104,known_native_pixel_differences=[29260,29261,29580,29581],tamper_rejections=4,post_reset_flash_pair=False)
 if all((HERE/f'post-{n}/result.json').exists() for n in (0,1)):
  boots=[]
  for n in (0,1):
   d=HERE/f'post-{n}';assert sha((d/'data.bin').read_bytes())==STOCK
   s=dict(x.split('=') for x in (d/'status.txt').read_text().split());assert all(s[k]=='0' for k in ('status','residual','guard_changes'))
   boots.append(json.loads((d/'request.json').read_text())['boot_id']);assert boots[-1]!=result['boot_id']
  assert boots[0]==boots[1];report['post_reset_flash_pair']=True
 print(json.dumps(report,indent=2))

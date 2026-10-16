#!/usr/bin/env python3
"""Full byte reconstruction of two-buffer CRC on/off A/B/B/A; checks remain mandatory. Also run verify.py."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
from frame_client import png

def verify(out):
 out=Path(out);frames=[json.loads(l) for l in (out/'play-frames.jsonl').read_text().splitlines()]
 pingpong=(out/'doom-pingpong-result.json').exists()
 limit=json.loads((out/'doom-pingpong-result.json').read_text())['frames'] if pingpong else 52
 options=json.loads((out/'test-options.json').read_text())
 expected_limit=options.get('play_frame_limit',0)
 assert limit==(expected_limit or (100 if pingpong and options.get('wad_load_test') else 52))
 assert limit in (52,100) or (pingpong and options.get('wad_load_test') and 100<=limit<=1000 and limit%2==0)
 profile=json.loads((out/'presentation-options.json').read_text()) if (out/'presentation-options.json').exists() else {}
 presentation_test=profile.get('presentation_test',False) or profile.get('detail_test',False) or profile.get('column_test',False)
 dma=[json.loads(l) for l in (out/'frame-dma-journal.jsonl').read_text().splitlines()]
 mailbox=[json.loads(l) for l in (out/'frame-journal.jsonl').read_text().splitlines()]
 reports=[json.loads(l) for l in (out/'frame-dma-results.jsonl').read_text().splitlines()]
 assert len(frames)==limit and len(mailbox)==260 and len(reports)==(16 if pingpong else 52)
 cursor=mc=ri=0;epoch=None;source=desc=base=None;pending=0;times={11:[],12:[]};compared=[]
 def dcall(op,g,off=0,error=None):
  nonlocal cursor,epoch
  row=dma[cursor];cursor+=1;q=bytes.fromhex(row['request']);assert len(q)==1056 and q[32:]==bytes(1024) and row['ns']>0
  h=struct.unpack_from('<8I',q);assert h[0]==op and h[2:]==(g,off,0,0,0,0) and 0<h[1]<=65535
  if epoch is None:epoch=h[1]
  assert h[1]==epoch
  if error is not None:assert row['errno']==error and 'response' not in row;return
  assert 'errno' not in row;b=bytes.fromhex(row['response']);assert len(b)==1056 and b[:32]==q[:32];return b[32:]
 def mcall(g,off):
  nonlocal mc
  row=mailbox[mc];mc+=1;q=bytes.fromhex(row['request']);b=bytes.fromhex(row['response'])
  assert row['op']==11 and row['ns']>0 and 'errno' not in row and len(q)==len(b)==1056
  assert struct.unpack_from('<8I',q)==(11,epoch,8,0,0,0,0,0) and struct.unpack_from('<2I',q,32)==(g,off) and not any(q[40:])
  h=struct.unpack_from('<8I',b);assert h[:4]==(11,epoch,1024,1) and not h[4]&1 and h[5:]==(0,0,0)
  return b[32:]
 def mread(g):
  b=b''.join(mcall(g,i) for i in range(0,65536,1024));assert mcall(g,0)==b[:1024];return b
 dcall(1,2,error=116);dcall(3,1,73728,error=22);dcall(3,1,4,error=22)
 for g,f in enumerate(frames,1):
  method=12
  crc=False if pingpong or presentation_test else g<=2 or 5<=g<=16 or g>=41
  assert f['crc']==crc and f['binary']
  assert f['frame']==g and f['session']==0 and f['method']==method
  if pingpong and g>16:
   data=(out/f'pingpong-{g:03}.bin').read_bytes()[4096:69632]
  elif method==12:
   assert dcall(1,g,0 if crc else 1)==bytes(1024)
   while 'errno' in dma[cursor]:dcall(2,g,error=11);pending+=1
   b=dcall(2,g);r=list(struct.unpack_from('<16I',b));assert b[64:]==bytes(960)
   assert r[:3]==[0x314d4446,2,g] and r[5]==r[6] and r[7]==r[9]==r[10]==r[13]==0 and r[14]==int(not crc) and r[8]==r[15] and r[11]==7 and r[12]<200000
   if source is None:source,desc,base=r[4],r[15],r[3]-4096
   assert r[4]==source+((g-1)&1)*65536 and 0xc0240000<=r[4]<=0xc0e30000
   assert r[15]==desc and not desc&31 and 0xc0f4c010<=desc<=0xc0f8bfe0
   assert r[3]==base+4096 and 0<base<=0xffffffff-73728
   capture=b''.join(dcall(3,g,i) for i in range(0,73728,1024));assert capture==(out/f'frame-dma-{g:03}.bin').read_bytes()
   assert capture[:4096]==capture[69632:]==b'\xa5'*4096
   data=capture[4096:69632];assert dcall(3,g,4096)==data[:1024]
   if crc:assert zlib.crc32(data)==r[5]
   else:assert r[5]==r[6]==0
   assert reports[ri]['frame']==g and reports[ri]['report']==r and reports[ri]['seconds']>0;ri+=1
  else:data=mread(g)
  assert data==(out/f'play-0-{g}.bin').read_bytes() and (struct.pack('<8I',0x31424644,1,0,g,320,200,65536,int(crc))+data)==(out/f'play-0-{g}.dfb').read_bytes()
  if profile:
   from presentation_profile import decode
   decoded=decode(data,g,profile.get('presentation_test',False),profile);assert all(f['profile'][k]==v for k,v in decoded.items())
  assert hashlib.sha256(data).hexdigest()==f['sha256'] and f['transfer_seconds']>0 and f['png_seconds']>0
  if g<=4:
   assert mread(g)==data
   c=f['comparison'];assert c['bytes']==65536 and c['mailbox_seconds']>0 and c['dma_seconds']>0;compared.append(c)
  else:assert f['comparison'] is None;times[method].append(f['transfer_seconds'])
 assert cursor==len(dma) and mc==len(mailbox) and ri==len(reports)
 controls=[];timing_words=[]
 for line in (out/'upload-journal.jsonl').read_text().splitlines():
  r=json.loads(line)
  if r['op']!=10:continue
  assert 'errno' not in r;q=bytes.fromhex(r['request']);s=bytes.fromhex(r['response']);assert len(q)==len(s)==1056
  assert struct.unpack_from('<8I',q)==(10,epoch,8,0,0,0,0,0) and not any(q[40:])
  h=struct.unpack_from('<8I',s);assert h[:4]==(10,epoch,4,1) and not h[4]&1 and h[5:]==(0,0,0) and not any(s[36:])
  i,v=struct.unpack_from('<2I',q,32);result=struct.unpack_from('<I',s,32)[0];assert i in ((0,1,2,7) if profile else (0,1,2))
  if i==7:
   assert 0<=v<5 and result!=0xffffffff;timing_words.append((v,result));continue
  if i==0:assert v==0 and result!=0xffffffff
  else:assert result==0;controls.append((i,v))
 load_test=json.loads((out/'test-options.json').read_text()).get('wad_load_test',False) if (out/'test-options.json').exists() else False
 expected=[]
 for g in range(1,limit+1):
  if load_test and g in ((60,62,64,66) if pingpong else (10,12,14,16)):
   k=27 if g==(60 if pingpong else 10) else 13;expected.extend([(2,256+k),(2,k)])
  if profile.get('runtime_flat') and g in (20,32,220,420):expected.extend([(2,256+192),(2,192)])
  if profile.get('runtime_detail') and g in (20,32):expected.extend([(2,256+191),(2,191)])
  if not pingpong or g<=16:expected.append((1,g))
 if pingpong:
  assert [x for x in controls if x[0]==1]==[x for x in expected if x[0]==1]
  assert all((v&255) in (173,175,172,174,163,162,182,191,192,13,27,9,121,110,49,50,51,52,53,54,55) and 0<=v<=511 for i,v in controls if i==2)
  if load_test or profile.get('runtime_detail') or profile.get('runtime_flat'):assert [x for x in controls if x[0]==2]==[x for x in expected if x[0]==2]
 else:assert controls==expected
 if profile.get('runtime_flat'):
  for g in (10,28,40,200,300,400,500):
   if g<=limit:assert frames[g-1]['profile']['flat_planes']==int(g in (28,300,400))
 if profile.get('runtime_detail'):
  for g in (10,28,40):assert frames[g-1]['profile']['detail']==(int(bool(profile.get('low_detail'))) ^ int(g==28))
 if profile and not pingpong:
  assert len(timing_words)==260
  for n,f in enumerate(frames):
   w=timing_words[n*5:n*5+5];assert [x for x,y in w]==list(range(5))
   v=[y for x,y in w];assert v[0]==n+1 and v[4]==sum(v[1:4])
   assert f['profile']['dma']==dict(zip(('frame','prepare_ms','hardware_ms','cleanup_ms','total_ms'),v))
 sessions=[json.loads(l) for l in (out/'play-sessions.jsonl').read_text().splitlines()];assert len(sessions)==1 and sessions[0]['result'][9:]==[2,1,210]
 blocks=[]
 for a,b in ((5,16),(17,28),(29,40),(41,52)):
  f=frames[a-1:b];elapsed=f[-1]['seconds']-f[0]['seconds'];assert elapsed>0
  blocks.append(dict(crc=f[0]['crc'],first=a,last=b,fps=11/elapsed,mean_transfer_seconds=sum(x['transfer_seconds'] for x in f)/12))
 fps={str(crc):22/sum(11/b['fps'] for b in blocks if b['crc']==crc) for crc in (True,False)} if not (presentation_test or pingpong) else {}
 if pingpong:
  from verify_play_pingpong import verify_transport
  return verify_transport(out,frames,epoch,source,compared,controls)
 return dict(full_frames=52,paired_comparisons=4,refusals=3,dma_frames=52,full_guarded_bytes=52*73728,pending_polls=pending,mailbox_reads=260,blocks=blocks,paired_seconds=compared,fps=fps,fps_comparison_valid=not (load_test or presentation_test),fps_speedup=None if (load_test or presentation_test) else fps['False']/fps['True'],epoch=epoch,source=hex(source),descriptor=hex(desc),dma_base=hex(base))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();print(json.dumps(verify(a.capture),indent=2))

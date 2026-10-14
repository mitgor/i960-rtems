#!/usr/bin/env python3
"""Independent full stress replay. Also require residentnet/verify.py."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path

def verify(out):
 out=Path(out)
 rows=lambda n:[json.loads(l) for l in (out/n).read_text().splitlines()]
 frames=rows('stress-frames.jsonl');d=rows('frame-dma-journal.jsonl');reports=rows('frame-dma-results.jsonl');mail=rows('frame-journal.jsonl');events=rows('upload-journal.jsonl')
 final=json.loads((out/'stress-result.json').read_text());n=final['frames'];assert 1<=n<=2048 and len(frames)==len(reports)==n
 assert final['zero_wad_reads'] and not (out/'wad-journal.jsonl').exists() and final['manifest']['dma_stress']==1
 assert final['result']==[0x454e4750,3,65536,0,0,n,0,0,0,2,1,210] and final['reply'][5]==0x454e4702
 dc=mc=0;epoch=source=desc=bus=None;pending=0
 def call(op,g,off=0):
  nonlocal dc,epoch
  e=d[dc];dc+=1;q=bytes.fromhex(e['request']);assert len(q)==1056 and q[32:]==bytes(1024) and e['ns']>0
  h=struct.unpack_from('<8I',q);assert h[0]==op and 0<h[1]<=65535 and h[2:]==(g,off,0,0,0,0)
  if epoch is None:epoch=h[1]
  assert epoch==h[1]
  if 'errno' in e:assert op==2 and e['errno']==11 and 'response' not in e;return None
  r=bytes.fromhex(e['response']);assert len(r)==1056 and r[:32]==q[:32];return r[32:]
 paired=0
 for g,f in enumerate(frames,1):
  assert f['frame']==g and f['transfer_seconds']>0 and f['seconds']>0
  assert call(1,g)==bytes(1024)
  r=call(2,g)
  while r is None:pending+=1;r=call(2,g)
  w=list(struct.unpack_from('<16I',r));assert r[64:]==bytes(960)
  assert w[:3]==[0x314d4446,2,g] and w[5]==w[6] and w[7]==w[9]==w[10]==w[13]==w[14]==0 and w[8]==w[15] and w[11]==7 and w[12]<200000
  assert 0xc0240000<=w[4]<=0xc0e30000 and 0xc0f4c010<=w[15]<=0xc0f8bfe0 and not w[15]&31 and 4096<w[3]<=0xffffffff-65536
  if source is None:source,desc,bus=w[4],w[15],w[3]
  assert (source,desc,bus)==(w[4],w[15],w[3])
  capture=b''.join(call(3,g,i) for i in range(0,73728,1024));assert capture==(out/f'frame-dma-{g:03}.bin').read_bytes()
  assert capture[:4096]==capture[69632:]==b'\xa5'*4096
  raw=capture[4096:69632];assert call(3,g,4096)==raw[:1024] and zlib.crc32(raw)==w[5]
  expected=bytes(((13*i)^(i//256)^(37*g))%256 for i in range(65536));assert raw==expected
  assert reports[g-1]['report']==w and reports[g-1]['frame']==g and reports[g-1]['seconds']>0
  assert f['sha256']==hashlib.sha256(raw).hexdigest() and f['paired']==(g<=4 or g%32==0 or g==n)
  if f['paired']:
   paired+=1
   for off in list(range(0,65536,1024))+[0]:
    e=mail[mc];mc+=1;q=bytes.fromhex(e['request']);r=bytes.fromhex(e['response'])
    assert e['op']==11 and e['ns']>0 and 'errno' not in e and len(q)==len(r)==1056
    assert struct.unpack_from('<10I',q)==(11,epoch,8,0,0,0,0,0,g,off) and q[40:]==bytes(1016)
    assert struct.unpack_from('<8I',r)[:4]==(11,epoch,1024,1) and not struct.unpack_from('<I',r,16)[0]&1 and r[20:32]==bytes(12) and r[32:]==raw[off:off+1024]
 assert dc==len(d) and mc==len(mail)
 acks=[];isolation=[]
 for e in events:
  if e['op']!=10:continue
  assert 'errno' not in e and e['ns']>0
  q=bytes.fromhex(e['request']);r=bytes.fromhex(e['response']);assert len(q)==len(r)==1056
  assert struct.unpack_from('<8I',q)==(10,epoch,8,0,0,0,0,0) and not any(q[40:])
  assert struct.unpack_from('<8I',r)[:4]==(10,epoch,4,1) and not struct.unpack_from('<I',r,16)[0]&1 and not any(r[20:32]) and not any(r[36:])
  i,v=struct.unpack_from('<2I',q,32);value=struct.unpack_from('<I',r,32)[0]
  if i==1:assert value==0;acks.append(v)
  elif i==5:assert v==16 and 0<=value<0xffffffff;isolation.append(value)
  else:assert i==0 and v==0 and value!=0xffffffff
 assert acks==list(range(1,n+1))
 assert final['isolation_checks']>0 and isolation==[0,final['isolation_checks']]
 owned=rows('owned-journal.jsonl');stops=0;active=None
 for e in owned:
  q=bytes.fromhex(e['request']);r=bytes.fromhex(e['response']);op=e['op']
  assert op in (5,6) and 'errno' not in e and e['ns']>0 and len(q)==len(r)==1056
  assert struct.unpack_from('<8I',q)==(op,epoch,32 if op==6 else 0,0,0,0,0,0)
  assert struct.unpack_from('<8I',r)[:4]==(op,epoch,32,1) and not struct.unpack_from('<I',r,16)[0]&1 and not any(r[20:32]) and not any(r[64:])
  if op==5:
   assert not any(q[32:]);w=struct.unpack_from('<8I',r,32);assert w[0]==0x3252444f
   active=w[1] if w[2] else None
  else:
   assert active is not None and active>0 and struct.unpack_from('<8I',q,32)==(0x3252444f,active,0,0,0,0,0,0) and not any(q[64:]) and r[32:]==q[32:]
   stops+=1
 assert stops==1
 return dict(isolation_checks=final['isolation_checks'],frames=n,paired=paired,pending_polls=pending,full_guarded_bytes=n*73728,mailbox_reads=mc,exact_pattern_bytes=n*65536,owned_stop=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();print(json.dumps(verify(a.capture),indent=2))

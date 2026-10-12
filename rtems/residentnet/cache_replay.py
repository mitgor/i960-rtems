"""Independent cache-line request oracle, byte/error checks and native support."""
import hashlib,json,struct,zlib

def prepare(capture,wad,build,requests,responses):
 data=wad.read_bytes();r=json.loads((capture/'cache-results.json').read_text());m=json.loads((build/'manifest.json').read_text());b=(build/'template.bin').read_bytes()
 assert r['manifest']==m and (capture/'cache-template.bin').read_bytes()==b and hashlib.sha256(b).hexdigest()==m['sha256'] and hashlib.sha256(data).hexdigest()==r['wad_sha256']
 directory=struct.unpack_from('<I',data,8)[0];oracle=2166136261
 for byte in data[:12]+data[499:1610]+data[directory:directory+512]+data[-37:]:oracle=((oracle^byte)*16777619)&0xffffffff
 assert r['oracle']==oracle
 # Independent direct-mapped cache model for the exact reviewed access sequence.
 tags={};normal=[]
 for off,n in ((0,12),(0,12),(499,1111),(499,1111),(directory,512),(len(data)-37,37)):
  for block in range(off//512,(off+n-1)//512+1):
   slot=block%32
   if tags.get(slot)!=block:normal.append((block*512,min(512,len(data)-block*512)));tags[slot]=block
 expected=[(o,n,'normal') for o,n in normal]+[(0,512,mode) for mode in ('crc','short','host-error','timeout')]+[(o,n,'normal') for o,n in normal]
 records=r['requests'];assert len(records)==len(expected)
 assert records==[dict(sequence=11+i,offset=o,wanted=n,mode=mode) for i,(o,n,mode) in enumerate(expected)]
 byseq={record['sequence']:record for record in records};seen={};replies=[];last=None
 for row in map(json.loads,(capture/'wad-journal.jsonl').read_text().splitlines()):
  req=bytes.fromhex(row['request']);res=bytes.fromhex(row['response']);op,epoch,n,*zero=struct.unpack_from('<8I',req);h=struct.unpack_from('<8I',res)
  assert len(req)==len(res)==1056 and op in (3,4) and epoch and not any(zero) and h[:2]==(op,epoch) and h[3]==1 and not h[4]&1 and h[5:]==(0,0,0)
  if op==3:
   last=struct.unpack_from('<8I',res,32)
   if last[1]<=10 or last[2]!=1:continue
   record=byseq[last[1]];assert last[3:7]==(1,record['offset'],record['wanted'],len(data));seen[last[1]]=last[3:7]
  else:
   w=struct.unpack_from('<8I',req,32)
   if w[1]<=10:continue
   assert last and last[2]==1 and last[1]==w[1]
   record=byseq[w[1]];mode=record['mode'];packet=req[32:32+n];payload=packet[32:32+w[4]];expected_data=data[record['offset']:record['offset']+record['wanted']]
   assert mode!='timeout' and w[:4]==(0x31444157,record['sequence'],1,record['offset']) and w[7]==0 and n==32+((w[4]+3)&~3) and not any(packet[32+w[4]:]) and res[32:32+n]==packet and h[2]==n
   if mode=='host-error':assert w[4:7]==(0,1,0)
   else:
    if mode=='short':expected_data=expected_data[:-1]
    assert w[5]==0 and payload==expected_data and w[4]==len(expected_data) and w[6]==(zlib.crc32(expected_data)^(mode=='crc'))
   assert not any(seq==w[1] for seq,p in replies);replies.append((w[1],packet))
 assert list(seen)==list(byseq) and [seq for seq,p in replies]==[seq for seq in byseq if byseq[seq]['mode']!='timeout']
 runs=[w for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==15]
 assert [w[2] for w in runs]==[1,2,1]+[0]*6 and [w[5] for w in runs]==[0,0,0,oracle,3,3,3,3,oracle]
 assert [row['mode'] for row in r['runs']]==['normal','crc','short','host-error','timeout','normal'] and [row['result'] for row in r['runs']]==[oracle,3,3,3,3,oracle] and r['runs'][4]['seconds']>=4.9
 report=[w[5] for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==12][-8:]
 assert r['report']==report==[0x31444157,10+len(expected),6+2*len(normal),4,2,0,0,len(data)]
 bases=[w[5] for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==14]
 if (capture/'batch-results.json').exists():bases=bases[:-1]
 if (capture/'engine-results.json').exists():bases=bases[:-3]
 if (capture/'owned-results.json').exists():bases=bases[:-1]
 base=bases[-1]
 assert r['base']==0xc02d0040+base and base%16==0
 return replies,dict(oracle=oracle,normal_wire_requests=len(normal),requests=len(records),replies=len(replies),cache_bytes=16384,bounce_bytes=512,probe_bytes=len(b),relocations=len(m['relocations']))

def native(prefix,t,build):
 (t/'cache_probe_bytes.h').write_bytes((build/'cache_probe_bytes.h').read_bytes())
 prefix='#define I960_DOOM_CACHE 1\n'+prefix
 return prefix.replace('#include "doom_runtime.c"','#include "doom_runtime.c"\n#include "../../game/doom/runtime/cache/cache.c"\n#include "../../game/doom/runtime/cache/probe.c"')

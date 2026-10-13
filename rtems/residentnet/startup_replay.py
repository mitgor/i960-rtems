"""Independent first-frame oracle and complete WAB1/STOP journal validation."""
import hashlib,json,struct,zlib

def prepare(capture,build,data,r,m,runs,report,bases):
 if m['startup'].get('checkpoints_sha256'):
  from checkpoint_replay import check
  cp=check(capture,build);assert cp['uncertain_errno'] is None and cp['pending_ack'] is None
  assert [g['generation'] for g in cp['comparisons']]==[4,5,6]
  for g in (cp['comparisons'][0],cp['comparisons'][2]):assert g['matching_prefix']==g['records']==cp['oracle_records'] and g['first_difference'] is None
  rows=[json.loads(line) for line in (capture/'startup-checkpoints.jsonl').open()]
  stopped=[w for w in rows if w[2]==5];assert [w[3] for w in stopped]==[1,2,60,61,62]
  assert [w[4] for w in stopped]==[0,0,210,210,0] and all(w[5:7]==[0,0] for w in stopped) and [w[7] for w in stopped]==[0,0,2,2,2]
 oracle=m['startup'];raw=(build/'startup-requests.bin').read_bytes();assert hashlib.sha256(raw).hexdigest()==oracle['requests_sha256']
 trace=list(struct.iter_unpack('<2I',raw));assert len(trace)==4747 and r['startup'] and r['diagnostic_only'] is False
 expected=[];last=0
 for i,row in enumerate(r['runs']):
  v=report[i*12:i*12+12];assert row['result']==v and v[:3]==[0x454e4750,2,6291456]
  assert row['stop']==(i==1) and row['value']==runs[i] and row['base']==0xc02d0040+bases[i] and bases[i]%16==0 and row['seconds']>0
  if i==1:assert v[3:7]==[0]*4 and v[9:]==[2,1,210]
  else:assert v[3:7]==[oracle['frame_fnv'],oracle['palette_fnv'],1,1] and v[9:]==[0,1,213]
  assert 0<v[7]<7*1048576 and 0<v[8]<=128
  ctl=row['control'];assert ctl[:4]==[0x3252444f,4+i,0,int(i==1)] and ctl[5]==4+i and ctl[7]==1+int(i>=1)
  wanted=[]
  for off,n in trace:
   mode='stop' if i==1 and n==4096 else 'normal';wanted.append(dict(sequence=len(expected)+len(wanted)+1,offset=off,wanted=n,mode=mode))
   if mode=='stop':break
  assert row['requests']==wanted;expected+=wanted
 assert r['requests']==expected
 records={e['sequence']:e for e in expected};seen={};parts={};last_query=None;epochs=set();fragment_count=0
 for line in (capture/'engine-wad-journal.jsonl').open():
  e=json.loads(line);assert 'errno' not in e;q=bytes.fromhex(e['request']);s=bytes.fromhex(e['response']);assert len(q)==len(s)==1056
  op,epoch,n,*zero=struct.unpack_from('<8I',q);h=struct.unpack_from('<8I',s);assert not any(zero) and epoch and h[:2]==(op,epoch) and h[3:]==(1,0,0,0,0);epochs.add(epoch)
  if op==3:
   assert n==0 and h[2]==32;last_query=struct.unpack_from('<8I',s,32)
   if last_query[0]!=0x31424157:assert last_query[0]==0x31444157 and last_query[2]==0;continue
   if last_query[2]!=1:continue
   seq=last_query[1];assert seq in records;row=records[seq];assert last_query[3:7]==(1,row['offset'],row['wanted'],len(data));seen[seq]=1
  else:
   assert op==4 and 32<=n<=544 and not n%4 and h[2]==n and s[32:32+n]==q[32:32+n]
   w=struct.unpack_from('<8I',q,32);seq=w[1];assert seq in records and seq in seen;row=records[seq];index=parts.get(seq,0);off=row['offset']+index*512
   assert last_query[:3]==(0x31424157,seq,1) and w[:4]==(0x31424157,seq,1,off) and w[7]==row['wanted']
   want=min(512,row['wanted']-index*512,len(data)-off);assert want>0;payload=data[off:off+want]
   assert w[4:7]==(want,0,zlib.crc32(payload)) and q[64:64+want]==payload and n==32+((want+3)&~3) and not any(q[64+want:32+n])
   parts[seq]=index+1;fragment_count+=1
 assert list(seen)==list(records) and len(epochs)==1
 if m['startup'].get('checkpoints_sha256'):assert cp['epoch'] in epochs
 for seq,row in records.items():assert parts.get(seq,0)==(3 if row['mode']=='stop' else (row['wanted']+511)//512)
 accepted=[];refused=[];states=[]
 for e in map(json.loads,(capture/'engine-owned-journal.jsonl').open()):
  q=bytes.fromhex(e['request']);op,epoch,n,*pad=struct.unpack_from('<8I',q);assert len(q)==1056 and epoch in epochs and not any(pad)
  if op==5:
   assert n==0;res=bytes.fromhex(e['response']);assert struct.unpack_from('<8I',res)==(5,epoch,32,1,0,0,0,0);v=struct.unpack_from('<8I',res,32);assert v[0]==0x3252444f;states.append(v)
  else:
   assert op==6 and n==32;w=struct.unpack_from('<8I',q,32);assert w[0]==0x3252444f and not any(w[2:]) and not any(q[64:])
   if 'errno' in e:assert e['errno']==116;refused.append(w[1])
   else:
    res=bytes.fromhex(e['response']);assert struct.unpack_from('<8I',res)==(6,epoch,32,1,0,0,0,0) and res[32:64]==q[32:64];accepted.append(w[1])
 assert accepted==[5] and refused==[4,4,5,6] and states[-1]==tuple(r['runs'][-1]['control'])
 return dict(startup=True,file_bytes=m['file_bytes'],span=m['memory_bytes'],admission_bytes=m['admission_bytes'],relocations=len(m['relocations']),frame_hash=oracle['frame_fnv'],palette_hash=oracle['palette_fnv'],runs=r['runs'],wad_requests=len(expected),fragments=fragment_count,metadata_sha256=m['metadata_sha256']),[]

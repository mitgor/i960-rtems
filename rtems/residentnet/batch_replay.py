"""Independent logical-cache / fragment / STOP oracle for WAB1 captures."""
import hashlib,json,struct,zlib
MAGIC=0x31424157

def prepare(capture,wad,build,requests,responses):
 r=json.loads((capture/'batch-results.json').read_text());data=wad.read_bytes();m=json.loads((build/'manifest.json').read_text());assert r['manifest']==m and hashlib.sha256(data).hexdigest()==r['wad_sha256']
 directory=struct.unpack_from('<I',data,8)[0];oracle=2166136261
 for b in data[:12]+data[499:1610]+data[directory:directory+512]+data[4099:12291]+data[-37:]:oracle=((oracle^b)*16777619)&0xffffffff
 assert r['oracle']==oracle
 assert (capture/'cache-template.bin').read_bytes()==(build/'template.bin').read_bytes()
 assert hashlib.sha256((build/'template.bin').read_bytes()).hexdigest()==m['sha256']
 assert r['stop_generation']==json.loads((capture/'engine-results.json').read_text())['runs'][-1]['control'][1]+7
 # Independent model: enumerate the original 512-byte misses, group adjacent
 # misses only within a logical read, stopping at a hit or eight lines.
 def model(limit):
  tags={};normal=[]
  for off,n in [(0,12),(0,12),(499,1111),(499,1111),(directory,512),(4099,8192),(len(data)-37,37)]:
   pending=[]
   def flush():
    if pending:
     start=pending[0]*512;normal.append((start,min(len(pending)*512,len(data)-start)));pending.clear()
   for block in range(off//512,(off+n+511)//512):
    slot=block%32
    if tags.get(slot)==block:flush()
    else:
     if pending and (len(pending)==limit//512 or block!=pending[-1]+1):flush()
     pending.append(block);tags[slot]=block
   flush()
  return normal
 cases=[(512,'normal'),(4096,'normal'),(4096,'crc'),(4096,'short'),(4096,'host-error'),(4096,'timeout'),(4096,'stop'),(4096,'normal'),(512,'normal')]
 expected=[];reports=[];accepted=rejected=cancelled=0
 for limit,mode in cases:
  for off,n in model(limit):
   actual=mode if n==4096 and mode!='normal' else 'normal';expected.append(dict(sequence=len(expected)+1,offset=off,wanted=n,mode=actual))
   if actual=='normal':accepted+=1
   else:
    rejected+=actual in ('crc','short');cancelled+=actual in ('timeout','stop');break
  reports.append([MAGIC,len(expected),accepted,rejected,cancelled,0,0,len(data)])
 assert r['requests']==expected
 assert [(x['limit'],x['mode']) for x in r['runs']]==cases
 values=[oracle if mode=='normal' else 3 for limit,mode in cases]
 assert [x['result'] for x in r['runs']]==values
 assert [x['report'] for x in r['runs']]==reports and r['runs'][5]['seconds']>=4.9
 command_rows=[w for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0] in (20,22)]
 assert [w[2] for w in command_rows]==[1]+[0]*9 and [w[5] for w in command_rows]==[0]+values
 report_words=[w[5] for p,w in zip(requests,responses) if struct.unpack_from('<I',p,8)[0]==21];assert report_words==sum(reports,[])
 records={x['sequence']:x for x in expected};seen={};parts={};replies=[];last=None;epochs=set()
 for e in map(json.loads,(capture/'batch-wad-journal.jsonl').read_text().splitlines()):
  q=bytes.fromhex(e['request']);res=bytes.fromhex(e['response']);assert len(q)==len(res)==1056
  op,epoch,n,*pad=struct.unpack_from('<8I',q);h=struct.unpack_from('<8I',res);epochs.add(epoch);assert epoch and not any(pad) and h[:2]==(op,epoch) and h[3:]==(1,0,0,0,0)
  if op==3:
   assert n==0 and h[2]==32;last=struct.unpack_from('<8I',res,32)
   if last[0]!=MAGIC:assert last[0]==0x31444157 and last[2]==0;continue
   if last[2]!=1:continue
   row=records[last[1]];assert last[3:7]==(1,row['offset'],row['wanted'],len(data));seen[last[1]]=last
  else:
   assert op==4 and 32<=n<=544 and not n%4 and h[2]==n and res[32:32+n]==q[32:32+n]
   packet=q[32:32+n];w=struct.unpack_from('<8I',packet);row=records[w[1]];index=parts.get(w[1],0);off=row['offset']+512*index
   assert last and last[0:3]==(MAGIC,w[1],1) and w[:4]==(MAGIC,w[1],1,off) and w[7]==row['wanted']
   want=min(512,row['wanted']-512*index,len(data)-off);block=data[off:off+want];final=512*(index+1)>=min(row['wanted'],len(data)-row['offset']);mode=row['mode'] if final else 'normal'
   if mode=='short':block=block[:-1]
   if mode=='host-error':block=b''
   assert w[4]==len(block) and w[5]==int(mode=='host-error') and packet[32:32+w[4]]==block and w[6]==(zlib.crc32(block)^(mode=='crc'))
   assert n==32+((len(block)+3)&~3) and not any(packet[32+len(block):]);parts[w[1]]=index+1;replies.append((w[1],packet))
 assert len(epochs)==1 and list(seen)==list(records)
 for seq,row in records.items():assert parts.get(seq,0)==(3 if row['mode'] in ('timeout','stop') else (min(row['wanted'],len(data)-row['offset'])+511)//512)
 controls=[json.loads(s) for s in (capture/'batch-owned-journal.jsonl').read_text().splitlines()];stops=[];stale=[];state=None
 for e in controls:
  q=bytes.fromhex(e['request']);op,epoch,n,*pad=struct.unpack_from('<8I',q);assert len(q)==1056 and epoch in epochs and not any(pad)
  if op==5:
   assert n==0;res=bytes.fromhex(e['response']);assert struct.unpack_from('<8I',res)==(5,epoch,32,1,0,0,0,0);state=struct.unpack_from('<8I',res,32);assert state[0]==0x3252444f and state[2]==1
  else:
   assert op==6 and n==32;w=struct.unpack_from('<8I',q,32);assert state and w[0]==0x3252444f and not any(w[2:]) and not any(q[64:])
   if 'errno' in e:assert e['errno']==116 and w[1]==state[1]-1;stale.append(w[1])
   else:
    res=bytes.fromhex(e['response']);assert struct.unpack_from('<8I',res)==(6,epoch,32,1,0,0,0,0) and res[32:64]==q[32:64] and w[1]==state[1];stops.append(w[1])
 assert stops==[r['stop_generation']] and stale==[stops[0]-1]
 return dict(oracle=oracle,logical_requests=len(expected),fragments=len(replies),normal_requests={str(limit):len(model(limit)) for limit in (512,4096)},stop_generation=stops[0],stop_sequence=next(x['sequence'] for x in expected if x['mode']=='stop'),reports=reports),replies

def native(prefix,info,replies):
 rows=','.join('{'+str(len(p)//4)+',{'+','.join(map(str,struct.unpack('<'+'I'*(len(p)//4),p)))+'}}' for seq,p in replies)
 code='''
#include "../../game/doom/runtime/batch/wire.c"
static const struct {unsigned n,w[136];} batch_recorded[]={'''+rows+'''};
static unsigned batch_replayed,batch_stop_sent;
static void batch_replay_service(void){unsigned i;
 if(batch.state!=WAD_REQUEST)return;
 if(batch.sequence=='''+str(info['stop_sequence'])+'''&&batch.fragments==3&&!batch_stop_sent){assert(owned_generation=='''+str(info['stop_generation'])+''');assert(!doom_runtime_owned_control(0x7a,0,owned_generation,1));batch_stop_sent=1;return;}
 if(batch_replayed>=sizeof(batch_recorded)/sizeof(*batch_recorded)||batch_recorded[batch_replayed].w[1]>batch.sequence)return;
 assert(batch_recorded[batch_replayed].w[1]==batch.sequence);
 assert(!doom_runtime_control(0x77,0,batch_recorded[batch_replayed].n*4,1));
 for(i=0;i<batch_recorded[batch_replayed].n;i++)assert(!doom_runtime_control(0x78,i,batch_recorded[batch_replayed].w[i],1));
 assert(!doom_runtime_control(0x79,0,0,1));batch_replayed++;
}
'''
 prefix='#define I960_WAD_BATCH 1\n'+prefix
 prefix=prefix.replace('static void runtime_service(void){unsigned i;', 'static void batch_replay_service(void);\nstatic void runtime_service(void){unsigned i;batch_replay_service();')
 return prefix+code

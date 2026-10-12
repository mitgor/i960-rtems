"""Independent WAD wire validation and native replay support."""
import hashlib,json,struct,zlib

def prepare(capture,wad_path,requests,responses):
 data=wad_path.read_bytes();sha=hashlib.sha256(data).hexdigest();result=json.loads((capture/'runtime-results.json').read_text())
 assert sha==result['wad_sha256'] and len(data)==result['file_bytes']
 probe=(capture/'runtime-probe.bin').read_bytes();assert hashlib.sha256(probe).hexdigest()==result['probe_sha256'] and len(probe)==result['probe_bytes']
 events=[json.loads(s) for s in (capture/'wad-journal.jsonl').read_text().splitlines()];last=None;replies=[];seen={};epochs=set()
 for e in events:
  req=bytes.fromhex(e['request']);res=bytes.fromhex(e['response']);assert len(req)==len(res)==1056
  op,epoch,n,*zero=struct.unpack_from('<8I',req);assert op in (3,4) and epoch and not any(zero);epochs.add(epoch)
  h=struct.unpack_from('<8I',res);assert h[:2]==(op,epoch) and h[3]==1 and not h[4]&1 and h[5:]==(0,0,0)
  if op==3:
   assert n==0 and h[2]==32;last=struct.unpack_from('<8I',res,32);assert last[0]==0x31444157 and last[2] in range(4)
   if last[1]>10:
    assert (capture/'cache-results.json').exists(), 'unvalidated later WAD query'
    continue
   if last[2]==1:
    assert last[3]==1 and 0<last[5]<=512 and last[4]<=len(data) and last[6]==len(data)
    if last[1] in seen:assert seen[last[1]]==last[3:7]
    seen[last[1]]=last[3:7]
  else:
   if struct.unpack_from('<I',req,36)[0]>10:
    assert (capture/'cache-results.json').exists(), 'unvalidated later WAD reply'
    continue
   assert last and last[2]==1 and h[2]==n and 32<=n<=544 and n%4==0
   packet=req[32:32+n];w=struct.unpack_from('<8I',packet);assert w[:4]==(0x31444157,last[1],1,last[4]) and not w[7] and w[4]<=512 and n==32+((w[4]+3)&~3)
   assert res[32:32+n]==packet and not any(packet[32+w[4]:]);assert not any(seq==w[1] for seq,_ in replies)
   expected=data[last[4]:last[4]+last[5]];seq=w[1]
   if seq in (1,2,3,8,9,10):assert w[5]==0 and packet[32:32+w[4]]==expected and w[6]==zlib.crc32(expected)
   elif seq==4:assert w[5]==0 and packet[32:32+w[4]]==expected and w[6]==(zlib.crc32(expected)^1)
   elif seq==5:assert w[5]==0 and packet[32:32+w[4]]==expected[:-1] and w[6]==zlib.crc32(expected[:-1])
   elif seq==6:assert w[4:7]==(0,1,0)
   else:raise AssertionError(('unexpected reply',seq))
   replies.append((seq,packet))
 assert len(epochs)==1 and list(seen)==list(range(1,11)) and [s for s,p in replies]==[1,2,3,4,5,6,8,9,10]
 binds=[req for req in requests if struct.unpack_from('<I',req,8)[0]==10];assert len(binds)==2
 binding=struct.pack('<3I',0x31444157,1,len(data))+bytes.fromhex(sha);assert all(p[32:]==binding for p in binds)
 offset=struct.unpack_from('<I',data,8)[0];oracle=2166136261
 for b in data[:12]+data[offset:offset+512]+data[-37:]:oracle=((oracle^b)*16777619)&0xffffffff
 runs=[w for req,w in zip(requests,responses) if struct.unpack_from('<I',req,8)[0]==11]
 assert len(runs)==7 and runs[0][2]==1 and all(w[2]==0 for w in runs[1:]) and [w[5] for w in runs[1:]]==[oracle,3,3,3,3,oracle]
 assert [r['mode'] for r in result['runs']]==['normal','crc','short','host-error','timeout','normal'] and [r['result'] for r in result['runs']]==[oracle,3,3,3,3,oracle]
 assert result['oracle']==oracle and result['runs'][4]['seconds']>=4.9
 report=[w[5] for req,w in zip(requests,responses) if struct.unpack_from('<I',req,8)[0]==12]
 assert len(report)==(16 if (capture/'cache-results.json').exists() else 8)
 report=report[:8]
 assert report==result['report']==[0x31444157,10,6,2,1,0,0,len(data)]
 assert result['requests']==[dict(sequence=i,offset=seen[i][1],wanted=seen[i][2],mode=('normal' if i in (1,2,3,8,9,10) else {4:'crc',5:'short',6:'host-error',7:'timeout'}[i])) for i in range(1,11)]
 return probe,replies,dict(wad_sha256=sha,bytes=len(data),requests=len(seen),replies=len(replies),oracle=oracle)

def native(prefix,tmp,probe,replies):
 (tmp/'runtime_probe_bytes.h').write_text('static const unsigned char runtime_probe_bytes[]={'+','.join(map(str,probe))+'};\n')
 (tmp/'runtime_native.h').write_text('static unsigned int runtime_lock(void){return 0;}\nstatic void runtime_unlock(unsigned int v){(void)v;}\n')
 prefix=prefix.replace('#define I960_DOOM_SHARED 1','#define I960_DOOM_SHARED 1\n#define I960_DOOM_RUNTIME 1')
 prefix=prefix.replace('void doom_shared_yield(void){struct timespec','static void runtime_service(void);\nvoid doom_shared_yield(void){if(identity==2)runtime_service();struct timespec')
 prefix=prefix.replace('#include "doom_heap_proof.c"','#include "doom_heap_proof.c"\n#include "doom_runtime.c"\n#include "../../game/doom/runtime/entry/probe.c"\n'+service(replies))
 return prefix

def service(replies):
 rows=[]
 for seq,p in replies:rows.append('{'+str(len(p)//4)+',{'+','.join(map(str,struct.unpack('<'+'I'*(len(p)//4),p)))+'}}')
 return '''static const struct {unsigned n,w[136];} recorded[]={'''+','.join(rows)+'''};
static unsigned replayed;
static void runtime_service(void){unsigned i; if(wad.state!=WAD_REQUEST||replayed>=sizeof(recorded)/sizeof(recorded[0]))return;
 if(recorded[replayed].w[1]>wad.sequence)return;
 assert(recorded[replayed].w[1]==wad.sequence);
 assert(!doom_runtime_control(0x77,0,recorded[replayed].n*4,1));
 for(i=0;i<recorded[replayed].n;i++)assert(!doom_runtime_control(0x78,i,recorded[replayed].w[i],1));
 assert(!doom_runtime_control(0x79,0,0,1));replayed++;
}
'''

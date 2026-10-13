"""Independent wire admission, output, WAD and control evidence for engine preflight."""
import hashlib,json,struct,zlib
from pathlib import Path

def fnv(b):
 h=2166136261
 for x in b:h=((h^x)*16777619)&0xffffffff
 return h

def prepare(capture,build,wad,requests,responses,partial=False):
 r={} if partial else json.loads((capture/'engine-results.json').read_text());m=json.loads((build/'manifest.json').read_text());blob=(build/'template.bin').read_bytes();meta=(build/'relocations.bin').read_bytes();data=Path(wad).read_bytes();assert partial or (r['manifest']==m and r['diagnostic_only'] is (not bool(m.get('startup'))))
 assert hashlib.sha256(blob).hexdigest()==m['template_sha256'] and hashlib.sha256(meta).hexdigest()==m['metadata_sha256']
 if not partial:
  assert (capture/'engine-template.bin').read_bytes()==blob and (capture/'engine-relocations.bin').read_bytes()==meta and hashlib.sha256(blob).hexdigest()==m['template_sha256'] and hashlib.sha256(meta).hexdigest()==m['metadata_sha256'] and r['wad_sha256']==hashlib.sha256(data).hexdigest()
 sections=m['sections']+[dict(offset=m['metadata_offset'],file_bytes=len(meta),memory_bytes=len(meta),flags=2)]
 current=None;candidates=[];runs=[];report=[];bases=[]
 for p,w in zip(requests,responses):
  cmd=struct.unpack_from('<I',p,8)[0]
  if cmd==1 and struct.unpack_from('<I',p,36)[0]==4:
   header=struct.unpack_from('<43I',p,32);assert header[:3]==(1,4,m['entry']);assert not any(header[23:]);current=[bytearray() for _ in sections]
   for i,s in enumerate(sections):assert header[3+i*5:7+i*5]==tuple(s[k] for k in ('offset','file_bytes','memory_bytes','flags'))
   crcs=[header[7+i*5] for i in range(4)]
  elif cmd==2 and current is not None:
   i,off,n=struct.unpack_from('<3I',p,12);assert i<4 and off==len(current[i]) and n==len(p)-32-((-n)%4);current[i]+=p[32:32+n]
  elif cmd==14 and current is not None:bases.append(w[5])
  elif cmd==18:
   if current is None:assert w[2:3]==[1] or w[2]==1;continue
   for s,b,c in zip(sections,current,crcs):assert len(b)==s['file_bytes'] and zlib.crc32(b)==c
   uploaded=bytearray(m['file_bytes'])
   for s,b in zip(sections,current):
    if s['offset']<len(uploaded):uploaded[s['offset']:s['offset']+len(b)]=b
   identity=hashlib.sha256(uploaded).hexdigest()==m['template_sha256'] and hashlib.sha256(current[3]).hexdigest()==m['metadata_sha256'];assert w[2]==(0 if identity else 2)
   candidates.append(dict(identity=identity,rc=w[2]));
   if identity:assert w[4]==0 and w[15]==0;runs.append(w[5])
   current=None
  elif cmd==19:assert w[2]==0;report.append(w[5])
 if partial:
  assert [c['identity'] for c in candidates]==[False,False] and not runs and not bases and not report and current is not None
  assert any(current) and not (capture/'engine-results.json').exists()
  w=json.loads((capture/'snapshots.json').read_text())[-1]['words'];assert w[0]==0x31525845 and w[11]==64 and w[2]==1 and w[3]==0
  return dict(partial=True,admission_refusals=2,engine_entries=0,span=m['memory_bytes'],admission_bytes=m['admission_bytes'],relocations=len(m['relocations']),known_partial_file_bytes=sum(map(len,current)),interrupt_drain_fault_bit=w[11],runs=[]),[]
 assert [c['identity'] for c in candidates]==[False,False,True,True,True] and runs==[0x454e4700,0x454e4702,0x454e4700] and len(bases)==3 and len(report)==36
 if m.get('startup'):
  from startup_replay import prepare as startup_prepare
  return startup_prepare(capture,build,data,r,m,runs,report,bases)
 frame=fnv(bytes(i%239 for i in range(64000)));palette=fnv(bytes(x for i in range(256) for x in (i,255-i,i^85)))
 for i,run in enumerate(r['runs']):
  v=report[12*i:12*i+12];assert run['result']==v and v[:7]==[0x454e4750,1,6291456,frame,palette,1,int(i!=1)] and v[9:]==[2 if i==1 else 0,1,0] and 6356480<=v[7]<7*1048576 and 3<=v[8]<=128
  assert run['stop']==(i==1) and run['value']==runs[i] and run['base']==0xc02d0040+bases[i] and bases[i]%16==0 and run['seconds']>0
  ctl=run['control'];assert ctl[0:4]==[0x3252444f,4+i,0,int(i==1)] and ctl[5]==4+i and ctl[7]==1+int(i>=1)
 records=[json.loads(s) for s in (capture/'engine-owned-journal.jsonl').read_text().splitlines()];accepted=[];refused=[];states=[];epochs=set()
 for e in records:
  q=bytes.fromhex(e['request']);op,epoch,n,*pad=struct.unpack_from('<8I',q);assert len(q)==1056 and op in (5,6) and not any(pad);epochs.add(epoch)
  if op==6:
   magic,g,*zero=struct.unpack_from('<8I',q,32);assert magic==0x3252444f and n==32 and not any(zero) and not any(q[64:])
   if 'errno' in e:assert e['errno']==116;refused.append(g)
   else:
    res=bytes.fromhex(e['response']);h=struct.unpack_from('<8I',res);assert h[:4]==(6,epoch,32,1) and not any(h[4:]) and res[32:64]==q[32:64];accepted.append(g)
  else:
   assert not n and not any(q[32:]);res=bytes.fromhex(e['response']);h=struct.unpack_from('<8I',res);assert h[:4]==(5,epoch,32,1) and not any(h[4:]);v=struct.unpack_from('<8I',res,32);assert v[0]==0x3252444f;states.append(v)
 assert len(epochs)==1 and accepted==[5] and refused==[4,6,5,6] and states[-1]==tuple(r['runs'][-1]['control'])
 baseline=json.loads((capture/'cache-results.json').read_text())['report'];assert baseline[0]==0x31444157 and baseline[5:7]==[0,0]
 replies=[];seen={};last=None
 for e in map(json.loads,(capture/'engine-wad-journal.jsonl').read_text().splitlines()):
  q=bytes.fromhex(e['request']);res=bytes.fromhex(e['response']);op,epoch,n,*pad=struct.unpack_from('<8I',q);h=struct.unpack_from('<8I',res);assert op in (3,4) and len(q)==len(res)==1056 and not any(pad) and h[0:2]==(op,epoch) and h[3:]==(1,0,0,0,0)
  if op==3:
   assert not n;last=struct.unpack_from('<8I',res,32);assert last[0]==0x31444157
   if last[2]==1:
    assert last[3]==1 and last[6]==len(data) and last[7]==baseline[3] and 0<last[5]<=512;seen[last[1]]=last
  else:
   p=q[32:32+n];w=struct.unpack_from('<8I',p);assert last and last[2]==1 and w[0:4]==(0x31444157,last[1],1,last[4]) and w[4:6]==(last[5],0) and not w[7]
   b=data[last[4]:last[4]+last[5]];assert p[32:32+w[4]]==b and w[6]==zlib.crc32(b) and res[32:32+n]==p and not any(p[32+w[4]:]);replies.append((w[1],p))
 assert list(seen)==list(range(baseline[1]+1,baseline[1]+4))
 assert len(seen)==len(replies)==3 and [x['sequence'] for x in r['requests']]==list(seen) and all(x['mode']=='normal' and x['wanted']==512 and x['offset']==seen[x['sequence']][4] for x in r['requests'])
 return dict(file_bytes=m['file_bytes'],span=m['memory_bytes'],admission_bytes=m['admission_bytes'],relocations=len(m['relocations']),frame_hash=frame,palette_hash=palette,runs=r['runs'],wad_requests=len(replies),metadata_sha256=m['metadata_sha256']),replies

def native(prefix,t,build,info):
 (t/'engine_identity.h').write_bytes((build/'engine_identity.h').read_bytes());rows=','.join('{'+','.join(map(str,r['result']))+'}' for r in info['runs']);values=','.join(str(r['value']) for r in info['runs'])
 if info.get('partial'):
  return '#define I960_DOOM_ENGINE 1\n#define ENGINE_GATE_NATIVE 1\n'+prefix+'\n#include "engine_gate.c"\n#include "../../loader/digest/sha256.c"\nunsigned engine_native_call(struct seg_image*s,const struct doom_runtime_owned*a){assert(0);return 0;}\n'
 prefix='#define I960_DOOM_ENGINE 1\n#define ENGINE_GATE_NATIVE 1\n'+prefix
 # Actual authentication, relocation, text verification and arena lifetime are
 # replayed. ISA/frame/libc execution is modeled from independently checked
 # physical fields; actual private libc preflight has its own native test.
 prefix+='\n#include "engine_gate.c"\n#include "../../loader/digest/sha256.c"\n'
 prefix+='static const unsigned engine_recorded[3][12]={'+rows+'};\nstatic const unsigned engine_values[3]={'+values+'};\n'
 if info.get('startup'):
  return '#define I960_WAD_BATCH 1\n'+prefix+'\n#include "../../game/doom/runtime/batch/wire.c"\n'+'''unsigned engine_native_call(struct seg_image*s,const struct doom_runtime_owned*a){static unsigned row;unsigned i;assert(row<3);if(row==1)assert(!doom_runtime_owned_control(0x7a,0,owned_generation,1));for(i=0;i<12;i++)store(s->base+ENGINE_RESULT+4*i,engine_recorded[row][i]);return engine_values[row++];}\n'''
 prefix+='''unsigned engine_native_call(struct seg_image*s,const struct doom_runtime_owned*a){static unsigned row;unsigned i;unsigned char*p=a->io.allocate(1024);assert(p&&row<3);assert(a->io.read(1,0,p,512)==512);a->io.release(p);
 if(row==1)assert(!doom_runtime_owned_control(0x7a,0,owned_generation,1));
 for(i=0;i<12;i++)store(s->base+ENGINE_RESULT+4*i,engine_recorded[row][i]);return engine_values[row++];}
'''
 return prefix

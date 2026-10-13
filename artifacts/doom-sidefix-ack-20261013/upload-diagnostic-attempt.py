#!/usr/bin/env python3
"""Replay a completed resident upload journal through the actual C core.
Also reconstruct and CRC-check the two uploaded files independently in Python.
"""
import ast,argparse,errno,hashlib,json,struct,subprocess,tempfile,zlib
from pathlib import Path
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--doom-heap',action='store_true');p.add_argument('--doom-shared',action='store_true');p.add_argument('--doom-runtime',action='store_true');p.add_argument('--wad',type=Path);p.add_argument('--entry',type=Path);p.add_argument('--partial-engine',action='store_true');p.add_argument('--wad-poll',action='store_true');p.add_argument('--unparked-diagnostic',action='store_true',help='Replay completed commands after a captured terminal abort; never accept physical drain');a=p.parse_args()
assert not (a.unparked_diagnostic and a.partial_engine)
if a.unparked_diagnostic:
 assert (a.capture/'error.txt').exists() and not (a.capture/'upload-parked.json').exists()
 terminal=json.loads((a.capture/'failure-snapshot.json').read_text())
 assert len(terminal)==64 and terminal[0]==0x31464d4e and terminal[2]==4
 assert terminal[16:20]==[1,1,1,0] and terminal[48]==0x31504548 and terminal[52]==10
 assert (a.capture/'engine-results.json').exists()
assert not a.doom_runtime or (a.doom_shared and a.wad)
assert not a.doom_shared or a.doom_heap
events=[json.loads(l) for l in (a.capture/'upload-journal.jsonl').read_text().splitlines()]
requests=[];responses=[];current=None;sent=bytearray();files=[bytearray(),bytearray()];manifest=None;first_image=True;stale=0;latencies=[]
for e in events:
 req=bytes.fromhex(e['request']);assert len(req)==1056
 head=struct.unpack_from('<8I',req);op,epoch,n,*unused=head;assert not any(unused) and epoch and op in (1,2)
 if 'errno' in e and a.partial_engine and op==1:
  assert e['errno']==71 and e is events[-1];continue
 if 'errno' in e:
  assert op==2 and e['errno']==116 # Linux ESTALE, independent of replay host OS
  stale+=1;continue
 res=bytes.fromhex(e['response']);assert len(res)==1056
 h=struct.unpack_from('<8I',res);assert h[0:2]==head[0:2] and h[3]==1 and not h[4]&1 and h[5:]==(0,0,0)
 latencies.append(e['ns']/1e6)
 if op==1:
  assert current is None and 32<=n<=1024 and not n%4
  packet=req[32:32+n];w=struct.unpack_from('<8I',packet);assert w[0]==0x314c5055 and not any(w[6:])
  current=w;requests.append(packet);sent+=struct.pack('<I',n)+packet
  if w[2]==1 and len(packet)==204:
   candidate=struct.unpack_from('<43I',packet,32)
   if candidate[3:8][0]==0 and candidate[8]==0x20000 and manifest is None:manifest=candidate
  if manifest and first_image and w[2]==2 and w[3]<2 and w[4]==len(files[w[3]]):
   # The deliberately invalid offset/duplicate request is not appended.
   files[w[3]]+=packet[32:32+w[5]]
  if manifest and w[2]==5:first_image=False
 else:
  assert n==0 and h[2]==64;w=struct.unpack_from('<16I',res,32)
  if current and not w[3] and w[1]==current[1]:
   responses.append(w);current=None
assert current is None and stale==1 and len(requests)==len(responses)
assert manifest and manifest[10] in (196608,917504) and len(files[0])==98304 and len(files[1])==98309
for i in (0,1):
 desc=manifest[3+5*i:8+5*i];assert zlib.crc32(files[i])==desc[4]
 if a.partial_engine:
  assert hashlib.sha256(files[i]).hexdigest()==('8e5668cf13b7917fcd4a8d805a222eaf754a3be9e4d820dcee97796bebf7da41','96967a12e7b8024eb2e20ca15d114b5966f08c8941785fa250a295c7fdac83df')[i]
 else:assert bytes(files[i])==(a.capture/('uploaded-code.bin' if i==0 else 'uploaded-data.bin')).read_bytes()
expected=struct.unpack_from('<I',files[1])[0]^0xa5a5a5a5
assert expected==0xe4f1e4e1
prefix=r'''
#include <assert.h>
#include <stdio.h>
static unsigned char memory[8*1048576+128] __attribute__((aligned(16)));
#define UPLOAD_GUARD_LO ((unsigned long)memory)
#define I960_RESIDENT_UPLOAD 1
#define UPLOAD_NATIVE 1
#include "upload.c"
int main(void){unsigned int packet[256],n,i;assert(upload_init());
 while(fread(&n,4,1,stdin)==1){assert(n>=32&&n<=1024&&n%4==0);assert(fread(packet,1,n,stdin)==n);
  assert(!upload_control(0x70,0,n,1));for(i=0;i<n/4;i++)assert(!upload_control(0x71,i,packet[i],1));
  assert(!upload_control(0x72,0,0,1));upload_step();assert(!pending);assert(fwrite(reply,4,16,stdout)==16);
 }assert(upload_finish());return 0;}
'''
if a.doom_heap:
 prefix=prefix.replace('#include "upload.c"','#define I960_DOOM_HEAP 1\n#include "upload.c"\n#include "doom_heap_proof.c"')
if a.doom_shared:
 tree=ast.parse((r/'test_doom_shared.py').read_text())
 source=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source' for t in n.targets))
 prefix=source.split('int main(void)')[0]+'int main(void)'+prefix.split('int main(void)',1)[1]
 prefix=prefix.replace('assert(upload_init());','identity=2;pthread_t task;doom_shared_init();assert(upload_init());assert(!pthread_create(&task,0,peer,0));')
 prefix=prefix.replace('}assert(upload_finish());','}atomic_store(&halted,1);assert(!pthread_join(task,0));identity=3;doom_shared_quiesce(1);assert(upload_finish());')
runtime_info=None
if a.doom_runtime:
 from runtime_replay import prepare,native
 probe,wad_replies,runtime_info=prepare(a.capture,a.wad,requests,responses)
 entry=a.entry or a.capture.parent/"residentnet/entry/runtime-probe.bin"
 assert probe==entry.read_bytes(), "captured probe differs from accepted build"
cache_info=None
if (a.capture/'cache-results.json').exists():
 assert a.doom_runtime
 from cache_replay import prepare as prepare_cache,native as cache_native
 cache_replies,cache_info=prepare_cache(a.capture,a.wad,entry.parent/'cache',requests,responses)
 wad_replies+=cache_replies
engine_info=None
if a.partial_engine or (a.capture/'engine-results.json').exists():
 from engine_replay import prepare as engine_prepare,native as engine_native
 engine_info,engine_replies=engine_prepare(a.capture,entry.parent/'engine',a.wad,requests,responses,partial=a.partial_engine)
 wad_replies+=engine_replies
batch_info=None
if (a.capture/'batch-results.json').exists():
 assert a.wad_poll
 from batch_replay import prepare as batch_prepare,native as batch_native
 batch_info,batch_replies=batch_prepare(a.capture,a.wad,entry.parent/'cache',requests,responses)
owned_info=None
if (a.capture/'owned-results.json').exists():
 assert a.doom_runtime
 from owned_replay import prepare as owned_prepare,native as owned_native
 owned_info=owned_prepare(a.capture,entry.parent/'owned',requests,responses)
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp)
 if a.doom_runtime:prefix=native(prefix,t,probe,wad_replies)
 if cache_info:prefix=cache_native(prefix,t,entry.parent/'cache')
 if owned_info:prefix=owned_native(prefix,t,entry.parent/'owned',owned_info)
 if engine_info:prefix=engine_native(prefix,t,entry.parent/'engine',engine_info)
 if batch_info:prefix=batch_native(prefix,batch_info,batch_replies)
 if (a.capture/'relocate-results.json').exists():
  from relocate_replay import prepare_relocated
  relocation_info=prepare_relocated(a.capture,entry.parent/'relocate',requests,responses)
  (t/'relocated_probe_bytes.h').write_bytes((entry.parent/'relocate/relocated_probe_bytes.h').read_bytes())
  prefix='#define I960_DOOM_RELOCATE 1\n'+prefix
 if a.wad_poll:
  # Physical PIO replies take nonzero time. Instant native replies can finish
  # all three reads in one 10 ms tick, correctly failing probe.c's clock check.
  # Delay only supplied replies; the actual C timeout/error/CRC paths remain.
  from runtime_replay import polled_service
  prefix='#define I960_WAD_POLL 1\n'+prefix+polled_service()
 (t/'test.c').write_text(prefix)
 (t/'upload_native.h').write_text('''#define R(a) (*(unsigned int*)(unsigned long)(a))
static unsigned int upload_stopping(void){return 0;}
static unsigned int upload_time(void){return 1;}
static void barrier(void){}
static int sync_code(void*p,unsigned int n){return 1;}
#include <execinfo.h>
static void exclusive_abort(void){void *p[32];int n=backtrace(p,32);backtrace_symbols_fd(p,n,2);assert(0);}
unsigned int upload_protect_step(void){return 1;}
unsigned int upload_protect_finish(void){return 1;}
''')
 if a.doom_shared:
  f=t/'upload_native.h';s=f.read_text().replace('return 0;}\nstatic unsigned int upload_time(void){return 1;', 'return atomic_load(&halted);}\nstatic unsigned int upload_time(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (unsigned int)(t.tv_sec*100+t.tv_nsec/10000000);')
  f.write_text(s)
 core=r.parents[1]/'loader/segmented'
 subprocess.run(['cc','-std=c11','-pthread','-fsanitize=address,undefined','-I'+str(t),'-I'+str(r),str(t/'test.c'),str(core/'arena.c'),str(core/'image.c'),*([str(r.parents[1]/'game/doom/runtime/wad.c')] if a.doom_runtime else []),*([str(r.parents[1]/'game/doom/runtime/heap.c'),str(r.parents[1]/'game/doom/runtime/libc.c')] if a.doom_heap else []),'-o',str(t/'replay')],check=True)
 raw=subprocess.run([str(t/'replay')],input=sent,stdout=subprocess.PIPE,check=True).stdout
 assert len(raw)==64*len(responses)
 for i,w in enumerate(responses):
  actual=struct.unpack_from('<16I',raw,i*64)
  if owned_info and struct.unpack_from('<2I',requests[i],8) in ((17,3),(17,4)):
   assert w[:5]==actual[:5] and w[6:12]==actual[6:12] and w[13:]==actual[13:],(i,w,actual)
  elif a.doom_shared and struct.unpack_from('<I',requests[i],8)[0]==9:
   assert w[:5]==actual[:5] and w[6:12]==actual[6:12] and w[13:]==actual[13:],(i,w,actual)
  else:assert w[0:12]==actual[0:12] and w[13:]==actual[13:],(i,w,actual)
  assert w[12]==0xc02d0040
if a.doom_heap:
 proof_rows=[w for request,w in zip(requests,responses) if struct.unpack_from('<I',request,8)[0]==8]
 assert len(proof_rows)==1 and proof_rows[0][2]==0 and proof_rows[0][5]==0x444c4942
if a.doom_shared:
 rows=[(req,w) for req,w in zip(requests,responses) if struct.unpack_from('<I',req,8)[0]==9]
 assert [struct.unpack_from('<I',req,12)[0] for req,w in rows]==list(range(10))
 stats=[w[5] for req,w in rows]
 assert len(stats)==10 and stats[0]==0x53484152 and stats[1]==4 and min(stats[2:6])>0 and stats[8:]==[1,1]
 assert stats[2]==stats[3] and 2*stats[2]<=stats[4]<=2*stats[2]+10
 assert stats[6]<=2 and stats[7]>=5
 observed=json.loads((a.capture/'doom-shared.json').read_text())
 assert observed['magic']=='0x53484152' and observed['peer_retained_bytes']==98304
 assert [observed[k] for k in ('phase','peer_checks','wrong_task_rejections','peer_enters','owner_enters','max_wait_ticks','max_hold_ticks','timeout_rejections','recursive_rejections')]==stats[1:]
if not a.partial_engine and not a.unparked_diagnostic:
 parked=json.loads((a.capture/'upload-parked.json').read_text());assert parked[3]==parked[4]==parked[15]==0 and parked[9]==(15 if batch_info else 14 if (a.capture/"engine-results.json").exists() else 12 if (a.capture/"owned-results.json").exists() else 10 if (a.capture/"cache-results.json").exists() else 8 if (a.capture/"relocate-results.json").exists() else 4 if a.doom_runtime else 3)
proof=[w for w in responses if w[10]==6291456];assert proof
result=dict(commands=len(requests),pio_ioctls=len(latencies),stale_epochs_rejected=stale,code_bytes=len(files[0]),data_bytes=len(files[1]),zero_fill_bytes=manifest[10]-len(files[1]),result=hex(expected),simultaneous_allocation_bytes=6291456+327680,stop_cancelled_partial_image=not a.partial_engine,native_cleanup_modeled=a.partial_engine,latency_ms=dict(max=max(latencies),mean=sum(latencies)/len(latencies)),files_sha256=[hashlib.sha256(b).hexdigest() for b in files])
if a.unparked_diagnostic:result.update(accepted=False,diagnostic_only=True,physical_final_drain=False,native_cleanup_modeled=True,stop_cancelled_partial_image=False,terminal_kind=terminal[2],terminal_heap_error=terminal[52])
if runtime_info:result['runtime']=runtime_info
if cache_info:result['cache']=cache_info
if batch_info:result['batch']=batch_info
if owned_info:result['owned']=owned_info
if engine_info:result['engine']=engine_info
if (a.capture/'relocate-results.json').exists():result['relocation']=relocation_info
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

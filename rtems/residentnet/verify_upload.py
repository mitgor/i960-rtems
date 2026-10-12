#!/usr/bin/env python3
"""Replay a completed resident upload journal through the actual C core.
Also reconstruct and CRC-check the two uploaded files independently in Python.
"""
import argparse,errno,hashlib,json,struct,subprocess,tempfile,zlib
from pathlib import Path
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--doom-heap',action='store_true');a=p.parse_args()
events=[json.loads(l) for l in (a.capture/'upload-journal.jsonl').read_text().splitlines()]
requests=[];responses=[];current=None;sent=bytearray();files=[bytearray(),bytearray()];manifest=None;first_image=True;stale=0;latencies=[]
for e in events:
 req=bytes.fromhex(e['request']);assert len(req)==1056
 head=struct.unpack_from('<8I',req);op,epoch,n,*unused=head;assert not any(unused) and epoch and op in (1,2)
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
assert manifest and len(files[0])==98304 and len(files[1])==98309
for i in (0,1):
 desc=manifest[3+5*i:8+5*i];assert zlib.crc32(files[i])==desc[4]
 assert bytes(files[i])==(a.capture/('uploaded-code.bin' if i==0 else 'uploaded-data.bin')).read_bytes()
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
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);(t/'test.c').write_text(prefix)
 (t/'upload_native.h').write_text('''#define R(a) (*(unsigned int*)(unsigned long)(a))
static unsigned int upload_stopping(void){return 0;}
static unsigned int upload_time(void){return 1;}
static void barrier(void){}
static int sync_code(void*p,unsigned int n){return 1;}
static void exclusive_abort(void){assert(0);}
unsigned int upload_protect_step(void){return 1;}
unsigned int upload_protect_finish(void){return 1;}
''')
 core=r.parents[1]/'loader/segmented'
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-I'+str(t),'-I'+str(r),str(t/'test.c'),str(core/'arena.c'),str(core/'image.c'),*([str(r.parents[1]/'game/doom/runtime/heap.c'),str(r.parents[1]/'game/doom/runtime/libc.c')] if a.doom_heap else []),'-o',str(t/'replay')],check=True)
 raw=subprocess.run([str(t/'replay')],input=sent,stdout=subprocess.PIPE,check=True).stdout
 assert len(raw)==64*len(responses)
 for i,w in enumerate(responses):
  actual=struct.unpack_from('<16I',raw,i*64)
  assert w[0:12]==actual[0:12] and w[13:]==actual[13:],(i,w,actual)
  assert w[12]==0xc02d0040
if a.doom_heap:
 proof_rows=[w for request,w in zip(requests,responses) if struct.unpack_from('<I',request,8)[0]==8]
 assert len(proof_rows)==1 and proof_rows[0][2]==0 and proof_rows[0][5]==0x444c4942
parked=json.loads((a.capture/'upload-parked.json').read_text());assert parked[3]==parked[4]==parked[15]==0 and parked[9]==3
proof=[w for w in responses if w[10]==6291456];assert proof
result=dict(commands=len(requests),pio_ioctls=len(latencies),stale_epochs_rejected=stale,code_bytes=len(files[0]),data_bytes=len(files[1]),zero_fill_bytes=196608-len(files[1]),result=hex(expected),simultaneous_allocation_bytes=6291456+327680,stop_cancelled_partial_image=True,latency_ms=dict(max=max(latencies),mean=sum(latencies)/len(latencies)),files_sha256=[hashlib.sha256(b).hexdigest() for b in files])
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

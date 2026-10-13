#!/usr/bin/env python3
"""Exercise actual barrier runtime and host protocol; no hardware acceptance."""
import json,struct,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=r'''
#include <assert.h>
#include <stdlib.h>
#include <errno.h>
#define I960_DOOM_CHECKPOINTS 1
#define I960_DOOM_CHECKPOINT_BARRIERS 1
static unsigned owned_generation=4,owned_running=1,held,clock_value,stop,mode,calls;
static struct {unsigned sequence;} batch;
static void*doom_malloc(unsigned n){return malloc(n);}
static unsigned owned_owner(void){return owned_running;}
static unsigned owned_stopping(void){return stop;}
static unsigned upload_stopping(void){return 0;}
static unsigned upload_time(void){return clock_value;}
static unsigned runtime_lock(void){assert(!held);held=1;return 0;}
static void runtime_unlock(unsigned v){assert(held&&!v);held=0;}
void doom_shared_service(void);
static void doom_shared_yield(void){assert(!held);}
#include "rtems/residentnet/doom_checkpoint_runtime.h"
static unsigned wire_running;
static int packet_exchange(void*d,unsigned token,unsigned value,unsigned*v,unsigned deadline){
 assert((token&65535)==42);*v=doom_runtime_checkpoint_control(token>>24,(token>>16)&255,value,wire_running);return 0;}
static unsigned acknowledge(unsigned n,unsigned gen,unsigned running){unsigned w[10]={0},epoch=42,v,deadline=1,op=8;int rc=0;void*d=0;
 w[8]=n;w[9]=gen;wire_running=running;
 /*HOST_ACK_BODY*/
 return 0;
 uncertain:unlock:return ~0u;}
void doom_shared_service(void){unsigned i,n=checkpoint_pending;assert(!held);calls++;
 if(mode==1){clock_value+=1000;return;}
 if(mode==2){stop=1;return;}
 if(mode==3)return; /* stalled clock: iteration bound still terminates */
 assert(acknowledge(n,4,1)==~0u); /* not read */
 assert(!doom_runtime_checkpoint_control(0x7d,0,n,1));
 for(i=0;i<7;i++)doom_runtime_checkpoint_control(0x7e,i,0,1);
 assert(acknowledge(n,4,1)==~0u); /* partial read */
 doom_runtime_checkpoint_control(0x7e,7,0,1);
 assert(doom_runtime_checkpoint_control(0x7f,1,4,1)==~0u); /* no staged index */
 assert(doom_runtime_checkpoint_control(0x7f,2,n,1)==~0u); /* invalid phase */
 assert(acknowledge(n,3,1)==~0u);
 assert(acknowledge(n+1,4,1)==~0u);
 assert(acknowledge(n,4,0)==~0u);
 assert(!acknowledge(n,4,1));
 assert(acknowledge(n,4,1)==~0u);
}
int main(void){assert(checkpoint_init());
 assert(checkpoint_mark(1,0,0,0)==1&&!calls);
 assert(checkpoint_mark(63,0,0,0)==1&&calls==1&&!checkpoint_pending);
 mode=1;assert(!checkpoint_mark(42,0,0,0)&&calls==4&&!checkpoint_pending);
 mode=2;assert(checkpoint_mark(43,0,0,0)==-1&&!checkpoint_pending);stop=0;
 mode=3;assert(!checkpoint_mark(44,0,0,0)&&!checkpoint_pending);
 assert(acknowledge(checkpoints->count,4,1)==~0u);
 mode=0;
 /* Exercise records on both sides of the actual eight-bit token boundary. */
 while(checkpoints->count<253)assert(checkpoint_mark(1,0,0,0)==1);
 while(checkpoints->count<512)assert(checkpoint_mark(80,0,0,0)==1);
 free(checkpoints);checkpoint_retire();return 0;}
'''
host=(root/'rtems/residentnet/upload_host.h').read_text()
begin=host.index(' if(op==8){\n  rc=packet_exchange');end=host.index('\n else\n#endif',begin)
source=source.replace('/*HOST_ACK_BODY*/',host[begin:end])
from checkpoint_client import Checkpoints,MAGIC
from checkpoint_replay import check
with tempfile.TemporaryDirectory() as d:
 t=Path(d);(t/'test.c').write_text(source)
 subprocess.run(['cc','-std=c11','-fsanitize=address,undefined','-I'+str(root),str(t/'test.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test')],check=True)
 rows=[[MAGIC,1,4,1,0,0,0,0],[MAGIC,2,4,63,226,0,0,4670]]
 events=[]
 class Fake:
  out=t
  def io(self,op,data):
   n=struct.unpack_from('<I',data)[0]
   if op==7:result=struct.pack('<8I',*(rows[n-1] if n<=2 else [MAGIC,0,2,0,0,0,0,0]))
   else:
    assert op==8 and data==struct.pack('<2I',2,4)
    assert len((t/'startup-checkpoints.jsonl').read_text().splitlines())==2
    result=data
   q=struct.pack('<8I',op,42,len(data),0,0,0,0,0)+data.ljust(1024,b'\0')
   s=struct.pack('<8I',op,42,len(result),1,0,0,0,0)+result.ljust(1024,b'\0')
   events.append(dict(op=op,request=q.hex(),response=s.hex()));return result
 cp=Checkpoints(Fake(),barriers=True);cp.pump(True)
 b=t/'build';b.mkdir();raw=b''.join(struct.pack('<8I',*r) for r in rows)
 import hashlib,copy
 (b/'startup-checkpoints.bin').write_bytes(raw)
 (b/'manifest.json').write_text(json.dumps(dict(startup=dict(checkpoints_sha256=hashlib.sha256(raw).hexdigest(),checkpoint_barriers=1))))
 def replay(es):
  (t/'engine-checkpoint-journal.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in es));return check(t,b)
 r=replay(events);assert r['acknowledged_records']==1 and r['pending_ack'] is None
 bads=[events[:2]+events[3:],events[:3]+events[2:],events[:1]+[events[2]]+events[1:]]
 for key,offset in [('request',32),('request',36),('request',40),('request',4),('response',32),('response',40),('response',12)]:
  e=copy.deepcopy(events);v=bytearray.fromhex(e[2][key]);v[offset]^=1;e[2][key]=v.hex();bads.append(e)
 for e in bads:
  try:replay(e)
  except AssertionError:pass
  else:raise AssertionError('invalid ACK accepted')
print('PASS actual barrier ACK/read/epoch-generation discipline, STOP, time and stalled-clock bounds, actual host packet encoding through record 512; durable host rows and 10 replay mutations')

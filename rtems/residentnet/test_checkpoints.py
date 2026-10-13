#!/usr/bin/env python3
"""Bounded log publication, generation/sequence binding and no-overwrite tests."""
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parents[2]
s=r'''
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include "game/doom/runtime/startup/checkpoint_log.h"
#define I960_DOOM_CHECKPOINTS 1
#define UPLOAD_NATIVE 1
static void *doom_malloc(unsigned n){return malloc(n);}
static unsigned active,held,owned_generation=4;
static struct {unsigned sequence;} batch;
static unsigned owned_owner(void){return active;}
static unsigned runtime_lock(void){assert(!held);held=1;return 0;}
static void runtime_unlock(unsigned saved){assert(held&&!saved);held=0;}
#include "rtems/residentnet/doom_checkpoint_runtime.h"
int main(void){struct doom_checkpoint_log l={0};unsigned w[8],first[8],i;
 assert(!doom_checkpoint_get(&l,0,w)&&!doom_checkpoint_get(&l,513,w));
 assert(!doom_checkpoint_put(&l,0,0,1,0,0,0));
 assert(doom_checkpoint_get(&l,1,w)&&w[0]==DOOM_CHECKPOINT_MAGIC&&!w[1]&&!w[3]);
 assert(doom_checkpoint_put(&l,4,100,1,0,0,0));
 assert(doom_checkpoint_put(&l,4,101,100,1,8,2)&&l.count==1);
 assert(doom_checkpoint_put(&l,4,101,100,64,8,2)&&l.count==2);
 assert(doom_checkpoint_put(&l,4,4700,101,9,10,11)&&l.count==3);
 assert(doom_checkpoint_get(&l,3,w)&&w[2]==4&&w[3]==101&&w[7]==4600);
 assert(doom_checkpoint_put(&l,5,4701,1,0,0,0));
 assert(doom_checkpoint_put(&l,5,4702,101,9,10,11)&&l.count==4);
 memcpy(first,l.rows[0],sizeof first);
 for(i=l.count;i<512;i++)assert(doom_checkpoint_put(&l,5,4800,50,1,2,3));
 assert(!doom_checkpoint_put(&l,5,4800,50,4,5,6)&&l.overflow&&l.count==512);
 assert(!memcmp(first,l.rows[0],sizeof first));
 assert(!checkpoint_mark(1,0,0,0)&&!checkpoints);
 active=1;assert(checkpoint_init());batch.sequence=50;assert(checkpoint_mark(1,2,3,4)&&!held);
 assert(!doom_runtime_checkpoint_control(0x7d,0,1,1));
 assert(doom_runtime_checkpoint_control(0x7e,2,0,1)==4);
 assert(checkpoint_mark(50,9,8,7)); /* prior frozen record stays immutable */
 assert(doom_runtime_checkpoint_control(0x7e,1,0,1)==1);
 assert(doom_runtime_checkpoint_control(0x7d,1,1,1)==~0u);
 assert(doom_runtime_checkpoint_control(0x7d,0,513,1)==~0u);
 assert(doom_runtime_checkpoint_control(0x7e,8,0,1)==~0u);
 assert(doom_runtime_checkpoint_control(0x7e,0,1,1)==~0u);
 free(checkpoints);checkpoint_retire();assert(!checkpoints);return 0;}
'''
with tempfile.TemporaryDirectory() as d:
 t=Path(d);(t/'test.c').write_text(s)
 subprocess.run(['cc','-std=c11','-fsanitize=address,undefined','-I'+str(r),str(t/'test.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test')],check=True)
print('PASS checkpoint selection, invocation-relative reads, immutable records, invalid indexes and overflow refusal')

# Exercise the actual host drain, including its bounded 32-record batches.
import json,struct
from checkpoint_client import Checkpoints,MAGIC
class Fake:
 def __init__(self,out):self.out=out;self.mode=0;self.calls=[]
 def io(self,op,data):
  index=struct.unpack('<I',data)[0];assert op==7;self.calls.append(index)
  if self.mode==1:return struct.pack('<8I',MAGIC,0,70,1,0,0,0,0)
  if self.mode==2:return struct.pack('<8I',MAGIC,index+1,4,50,0,0,0,0)
  return struct.pack('<8I',MAGIC,index,4,50,index,0,0,index) if index<=70 else struct.pack('<8I',MAGIC,0,70,0,0,0,0,0)
with tempfile.TemporaryDirectory() as d:
 t=Path(d);u=Fake(t);cp=Checkpoints(u);cp.pump(True)
 assert len(cp.rows)==70 and u.calls==list(range(1,72))
 assert len((t/'startup-checkpoints.jsonl').read_text().splitlines())==70
 for mode in (1,2):
  u.mode=mode
  try:cp.pump(True)
  except AssertionError:pass
  else:raise AssertionError('bad checkpoint stream accepted')
 assert len(cp.rows)==70
print('PASS host bounded checkpoint draining, persistent rows, overflow and sequence refusal')

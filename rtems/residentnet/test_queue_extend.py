#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define NETWORK_FRAME_BYTES 1500
static unsigned char internal[68][1500] __attribute__((aligned(16))),external[128][1500],(*frames)[1500]=internal;
#define internal_frames internal
static unsigned int queue_slots=68,head,queued,tail;
static unsigned short lengths[128];
static void*address(unsigned int a){assert(a>=0xc0200040u&&a<0xc0200040u+sizeof(external));return (char*)external+(a-0xc0200040u);}
#define QUEUE_ADDRESS address
#define I960_QUEUE_RECLAIM 1
#define RESIDENT_RAM_H
static unsigned int native_owned=1;
static unsigned int ram_owned(unsigned int b,unsigned int n){return native_owned&&b==(unsigned int)internal&&n==sizeof(internal);}
#include "queue_extend.h"
int main(void){unsigned int i,j,n;
 for(n=0;n<=68;n++){
  fallback_ready=0;frames=internal;queue_slots=68;head=0;queued=n;tail=n%68;
  assert(resident_fallback_prepare()==1&&!resident_fallback_valid());
  memset(external,0,sizeof(external));
  for(i=0;i<n;i++){lengths[i]=i%2?1500:64;memset(internal[i],i+1,lengths[i]);}
  assert(resident_queue_extend(0xc0200044u)==1&&frames==internal);
  assert(!resident_queue_extend(0xc0200040u)&&frames==external&&queue_slots==128&&tail==n&&resident_queue_external_valid());
  for(i=0;i<n;i++)for(j=0;j<lengths[i];j++)assert(external[i][j]==i+1);
  assert(resident_queue_extend(0xc0200040u)==1);
  native_owned=0;assert(resident_fallback_prepare()==1&&!fallback_ready);native_owned=1;
  assert(!resident_fallback_prepare()&&resident_fallback_valid()&&resident_fallback_prepare()==1);
  memset((char*)internal+64,0xe7,sizeof(internal)-128);assert(resident_fallback_valid());
  for(i=0;i<n;i++)for(j=0;j<lengths[i];j++)assert(external[i][j]==i+1);
  for(i=0;i<32;i++){unsigned int*p=(unsigned int*)internal+(i<16?i:sizeof(internal)/4-32+i);
   for(j=0;j<32;j++){*p^=1u<<j;assert(!resident_fallback_valid());*p^=1u<<j;assert(resident_fallback_valid());}
  }
 }
 frames=external;queue_slots=68;head=0;queued=1;tail=1;
 assert(resident_queue_extend(0xc0200040u)==1);frames=internal;tail=2;
 assert(resident_queue_extend(0xc0200040u)==1);tail=1;lengths[0]=1501;
 assert(resident_queue_extend(0xc0200040u)==1&&frames==internal);lengths[0]=64;
 frames=internal;queue_slots=68;head=1;assert(resident_queue_extend(0xc0200040u)==1);head=0;queued=69;assert(resident_queue_extend(0xc0200040u)==1);
 queue_slots=128;frames=external;head=tail=queued=0;assert(resident_queue_external_valid());
 head=128;assert(!resident_queue_external_valid());head=0;tail=128;assert(!resident_queue_external_valid());tail=0;queued=129;assert(!resident_queue_external_valid());
 puts("Guarded reclaim: 69 migrations, 70656 guard bit flips and external data isolation passed. Actual queue migration: all 0..68 occupancies preserved, repeated migration/wrong base/active head/overflow rejected");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'queue.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-Wno-pointer-to-int-cast','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

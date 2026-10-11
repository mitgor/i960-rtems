#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define NETWORK_FRAME_BYTES 1500
static unsigned char internal[68][1500],external[128][1500],(*frames)[1500]=internal;
static unsigned int queue_slots=68,head,queued,tail;
static unsigned short lengths[128];
static void*address(unsigned int a){assert(a>=0xc0200040u&&a<0xc0200040u+sizeof(external));return (char*)external+(a-0xc0200040u);}
#define QUEUE_ADDRESS address
#include "queue_extend.h"
int main(void){unsigned int i,j,n;
 for(n=0;n<=68;n++){
  frames=internal;queue_slots=68;head=0;queued=n;tail=n%68;
  memset(external,0,sizeof(external));
  for(i=0;i<n;i++){lengths[i]=i%2?1500:64;memset(internal[i],i+1,lengths[i]);}
  assert(resident_queue_extend(0xc0200044u)==1&&frames==internal);
  assert(!resident_queue_extend(0xc0200040u)&&frames==external&&queue_slots==128&&tail==n&&resident_queue_external_valid());
  for(i=0;i<n;i++)for(j=0;j<lengths[i];j++)assert(external[i][j]==i+1);
  assert(resident_queue_extend(0xc0200040u)==1);
 }
 frames=internal;queue_slots=68;head=1;assert(resident_queue_extend(0xc0200040u)==1);head=0;queued=69;assert(resident_queue_extend(0xc0200040u)==1);
 queue_slots=128;frames=external;head=tail=queued=0;assert(resident_queue_external_valid());
 head=128;assert(!resident_queue_external_valid());head=0;tail=128;assert(!resident_queue_external_valid());tail=0;queued=129;assert(!resident_queue_external_valid());
 puts("Actual queue migration: all 0..68 occupancies preserved, repeated migration/wrong base/active head/overflow rejected");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'queue.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

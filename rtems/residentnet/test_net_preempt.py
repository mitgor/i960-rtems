#!/usr/bin/env python3
"""Exercise the actual worker handoff with simulated ISR commands at each lease."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#define I960_QUEUE_RECLAIM 1
static volatile unsigned int ticks;
static unsigned int resident_state=1,masked,elapsed_seen,calls;
static unsigned int registers[2048];
#define R(a) registers[((a)>>2)&2047]
static void mask(void){assert(!masked);masked=1;}
static void enable(void){assert(masked);masked=0;}
void bounded_fatal(unsigned int code){assert(!code);}
#include "net_runtime.h"
void network_step(unsigned int ms,const unsigned char*p,unsigned int n){unsigned int i;
 assert(!masked);elapsed_seen=ms;calls++;
 if(n){assert(n==20&&p==netlink.rx&&netlink.ready);
  for(i=0;i<n;i++)assert(p[i]==0x53);
  assert(packet_command(&netlink,10,0,20,1)==0xffffffffu);
  assert(packet_command(&netlink,11,0,0,1)==0xffffffffu);
  assert(packet_command(&netlink,12,0,0,1)==0xffffffffu);
 }
 ticks+=2; /* ISR ticks must remain due for the next network step. */
}
unsigned int network_output(unsigned char*out,unsigned int cap){unsigned int i;
 assert(!masked&&out==netlink.tx&&cap==1536&&!netlink.txlen);
 for(i=0;i<24;i++){
  out[i]=(unsigned char)(0x70+i);
  assert(packet_command(&netlink,13,0,0,1)==0);
  assert(packet_command(&netlink,14,0,0,1)==0xffffffffu);
  assert(packet_command(&netlink,15,0,0,1)==0xffffffffu);
 }
 /* A new RX may arrive while TX is being built; it belongs to the next step. */
 assert(!packet_command(&netlink,10,0,20,1));
 for(i=0;i<5;i++)assert(!packet_command(&netlink,11,i,0x53535353u,1));
 assert(!packet_command(&netlink,12,0,0,1));return 24;
}
int main(void){unsigned int i,v;
 net_ready=1;ticks=10;resident_net_step();assert(!masked&&elapsed_seen==100&&net_tick==10&&ticks==12&&netlink.ready&&netlink.txlen==24&&net_irq_spans[0]==1);
 for(i=0;i<6;i++)assert(packet_command(&netlink,14,i,0,1)==packet_word(netlink.tx+i*4));
 resident_net_step();assert(elapsed_seen==20&&net_tick==12&&!netlink.ready&&netlink.txlen==24);
 assert(packet_command(&netlink,15,0,0,1)==24);resident_net_step();assert(netlink.ready&&netlink.txlen==24);
 resident_state=2;v=calls;resident_net_step();assert(calls==v&&netlink.ready&&netlink.txlen==24);
 puts("Actual network worker: preemptible processing/copy, RX lease, unpublished TX, elapsed ticks, pending RX and STOP retention passed");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-O2','-fsanitize=address,undefined','-Wno-int-to-pointer-cast','-Wno-pointer-to-int-cast','-I'+str(root),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)

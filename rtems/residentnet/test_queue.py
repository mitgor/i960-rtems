#!/usr/bin/env python3
"""Exercise the actual shared queue functions at all supported capacities."""
from pathlib import Path
import subprocess,tempfile
source=(Path(__file__).resolve().parents[1]/'net/network.c').read_text()
functions=source[source.index('static err_t enqueue('):source.index('static err_t output(')]
functions+=source[source.index('unsigned int network_output('):source.index('unsigned int network_report(')]
for capacity in (8,32,64):
 code='''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int err_t;
#define ERR_MEM -1
#define ERR_OK 0
#define NETWORK_QUEUE_SLOTS CAPACITY
#define RESIDENT_QUEUE_STATS 1
static unsigned int queue_highwater;
struct pbuf {unsigned int tot_len;unsigned char *payload;};
static unsigned short lengths[NETWORK_QUEUE_SLOTS];
static unsigned char frames[NETWORK_QUEUE_SLOTS][1536];
static unsigned int head,tail,queued,drops,tx_count;
static void pbuf_copy_partial(struct pbuf*p,void*d,unsigned int n,unsigned int off){memcpy(d,p->payload+off,n);}
static void bio_put(unsigned char*p,unsigned int n){p[0]=n;p[1]=n>>8;p[2]=n>>16;p[3]=n>>24;}
'''.replace('CAPACITY',str(capacity))+functions+'''
int main(void){unsigned int i,j;unsigned char bytes[1537],out[1536];struct pbuf p={1500,bytes};
 for(i=0;i<NETWORK_QUEUE_SLOTS;i++){memset(bytes,i,sizeof(bytes));assert(enqueue(&p)==0);}
 assert(queued==NETWORK_QUEUE_SLOTS&&enqueue(&p)==ERR_MEM);
 assert(queue_highwater==NETWORK_QUEUE_SLOTS);
 assert(network_output(out,1503)==0&&queued==NETWORK_QUEUE_SLOTS);
 for(i=0;i<NETWORK_QUEUE_SLOTS*4;i++){
  assert(network_output(out,sizeof(out))==1504);
  assert(out[0]==0xdc&&out[1]==5);
  for(j=4;j<1504;j++)assert(out[j]==(unsigned char)i);
  memset(bytes,i+NETWORK_QUEUE_SLOTS,sizeof(bytes));assert(enqueue(&p)==0);
 }
 for(i=0;i<NETWORK_QUEUE_SLOTS;i++)assert(network_output(out,sizeof(out))==1504);
 assert(!queued&&network_output(out,sizeof(out))==0);
 p.tot_len=1537;assert(enqueue(&p)==ERR_MEM&&drops==2);
 printf("%u-slot actual queue: full rejection, backpressure, wrap, drain, oversize passed\\n",NETWORK_QUEUE_SLOTS);
}
'''
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'queue.c';p.write_text(code);exe=p.with_suffix('')
  subprocess.run(['cc','-Wall','-Wextra','-fsanitize=address,undefined',str(p),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)

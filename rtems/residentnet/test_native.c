#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "packet.h"
#include "ram.h"
int main(void){struct packet_link p;unsigned int n,i,j,v;
 memset(&p,0,sizeof(p));
 assert(!ram_owned(0,1)&&!ram_owned(0xc0f4c00f,1)&&!ram_owned(0xc0f9bff0,1));
 assert(!ram_owned(0xc0f4c010,0xffffffff)&&!ram_owned(0xc0f4c010,0));
 assert(ram_owned(0xc0f4c010,0x4ffe0)&&!ram_owned(0xc0f4c010,0x4ffe1));
 assert(!ram_reclaim(0xc0120000,0xe00000));
 for(n=20;n<=1500;n++){
  assert(packet_command(&p,10,0,n,1)==0);
  assert(packet_command(&p,12,0,0,1)==0xffffffff);
  assert(packet_command(&p,11,1,0,1)==0xffffffff);
  for(i=0;i<(n+3)/4;i++)assert(!packet_command(&p,11,i,0x12345678u^i,1));
  assert(packet_command(&p,11,i,0,1)==0xffffffff);
  assert(!packet_command(&p,12,0,0,1)&&p.ready);
  assert(packet_command(&p,10,0,20,1)==0xffffffff);
  for(i=0;i<(n+3)/4;i++)assert(packet_word(p.rx+i*4)==(0x12345678u^i));
  /* ISR command attempts while the worker holds its immutable RX lease. */
  assert(packet_command(&p,11,0,0,1)==0xffffffff);
  assert(packet_command(&p,12,0,0,1)==0xffffffff);
  assert(p.ready&&p.length==n);
  for(i=0;i<(n+3)/4;i++)assert(packet_word(p.rx+i*4)==(0x12345678u^i));
  p.length=0;p.words=0;p.ready=0;
 }
 for(n=0;n<1600;n++)if(n<20||n>1500)assert(packet_command(&p,10,0,n,1)==0xffffffff);
 for(i=0;i<1536;i++){
  p.tx[i]=(unsigned char)i;
  assert(packet_command(&p,13,0,0,1)==0);
  assert(packet_command(&p,14,i/4,0,1)==0xffffffff);
  assert(packet_command(&p,15,0,0,1)==0xffffffff);
 }
 p.txlen=1536;
 for(i=0;i<384;i++)assert(packet_command(&p,14,i,0,1)==packet_word(p.tx+4*i));
 assert(packet_command(&p,14,384,0,1)==0xffffffff);
 for(i=10;i<=15;i++)assert(packet_command(&p,i,0,0,0)==0xfffffffe);
 assert(packet_command(&p,15,0,0,1)==1536&&!p.txlen);
 puts("packet boundaries/order/commit/STOP, 1481 payload lengths, RAM overflow and reclaim denial passed");return 0;
}

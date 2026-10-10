#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "network.h"
void bounded_fatal(unsigned int c){fprintf(stderr,"fatal %x\n",c);abort();}
static unsigned int sum(const unsigned char*b,unsigned int n){unsigned int x=0;while(n>1){x+=b[0]*256+b[1];b+=2;n-=2;}if(n)x+=b[0]*256;while(x>>16)x=(x&65535)+(x>>16);return (~x)&65535;}
static void put16(unsigned char*p,unsigned int x){p[0]=x>>8;p[1]=x;}
static unsigned int get32(unsigned char*p){return p[0]|p[1]<<8|p[2]<<16|(unsigned int)p[3]<<24;}
static void ip(unsigned char*b,unsigned int n,unsigned int proto){memset(b,0,20);b[0]=0x45;put16(b+2,n);b[8]=64;b[9]=proto;b[12]=10;b[13]=196;b[15]=1;b[16]=10;b[17]=196;b[19]=2;put16(b+10,sum(b,20));}
int main(void){
 unsigned char packet[1600],out[8192];unsigned int n,size,i,j;
 network_init();
 for(j=0;j<5;j++){
  size=(unsigned int[]){0,1,31,500,1400}[j];memset(packet,0,sizeof(packet));ip(packet,28+size,17);
  put16(packet+20,12345);put16(packet+22,9601);put16(packet+24,8+size);
  for(i=0;i<size;i++)packet[28+i]=i%251;
  network_step(10,packet,28+size);n=network_output(out,sizeof(out));assert(n==32+size&&get32(out)==28+size);
  assert(out[16]==10&&out[19]==2&&out[20]==10&&out[23]==1);assert(sum(out+4,20)==0);assert(!memcmp(out+32,packet+28,size));
 }
 memset(packet,0,40);ip(packet,40,1);packet[20]=8;put16(packet+22,sum(packet+20,20));network_step(10,packet,40);n=network_output(out,sizeof(out));assert(n==44&&out[24]==0&&sum(out+24,20)==0);
 /* Bad IPv4 checksum is discarded, as are short and oversized inputs. */
 packet[10]^=1;network_step(10,packet,40);assert(network_output(out,sizeof(out))==0);
 network_step(10,packet,8);assert(network_output(out,sizeof(out))==0);
 network_step(10,packet,1501);assert(network_output(out,sizeof(out))==0);
 /* Bounded TX ring: input can continue while the host is not draining output. */
 for(i=0;i<12;i++){memset(packet,0,28);ip(packet,28,17);put16(packet+20,12345);put16(packet+22,9601);put16(packet+24,8);network_step(10,packet,28);}
 n=network_report(out);assert(n==24&&get32(out+8)>=5);
 assert(network_output(out,1)==0);n=network_output(out,sizeof(out));assert(n==8*32);
 for(j=0;j<10000;j++){
  unsigned int x=j*1664525u+1013904223u;size=x%1501;
  for(i=0;i<size;i++){x=x*1664525u+1013904223u;packet[i]=x>>24;}
  if(j%2==0&&size>=28){ip(packet,size,17);put16(packet+20,12345);put16(packet+22,9601);put16(packet+24,size-20);put16(packet+26,0);}
  network_step(1,packet,size);network_output(out,sizeof(out));
 }
 puts("lwIP native: 10,000 mixed malformed/UDP packets; UDP 0/1/31/500/1400, ICMP, malformed IP, oversize and TX backpressure passed");return 0;
}

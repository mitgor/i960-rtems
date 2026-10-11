#include "lwip/sys.h"
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
static void ip6(unsigned char*b,unsigned int n,unsigned int proto){
 static const unsigned char prefix[16]={0xfd,0x96,1,0x96,9,0x60,0,0,0,0,0,0,0,0,0,1};
 memset(b,0,40);b[0]=0x60;put16(b+4,n-40);b[6]=proto;b[7]=64;memcpy(b+8,prefix,16);memcpy(b+24,prefix,16);b[39]=2;
}
static unsigned int sum6(const unsigned char*b,unsigned int n){
 unsigned char pseudo[1640];memcpy(pseudo,b+8,32);memset(pseudo+32,0,8);put16(pseudo+34,n-40);pseudo[39]=b[6];memcpy(pseudo+40,b+40,n-40);return sum(pseudo,n);
}
static void test_ipv6(void){
 unsigned char packet[1600],out[8192];unsigned int i,j,n,size;
 for(j=0;j<6;j++){
  size=(unsigned int[]){0,1,31,500,1400,1452}[j];memset(packet,0,sizeof(packet));ip6(packet,48+size,17);
  put16(packet+40,12345);put16(packet+42,9601);put16(packet+44,8+size);
  for(i=0;i<size;i++)packet[48+i]=i%251;
  put16(packet+46,sum6(packet,48+size));network_step(10,packet,48+size);n=network_output(out,sizeof(out));
  assert(n==52+size&&get32(out)==48+size&&out[4]>>4==6);assert(!memcmp(out+12,packet+24,16)&&!memcmp(out+28,packet+8,16));
  assert(sum6(out+4,n-4)==0&&!memcmp(out+52,packet+48,size));
  packet[46]^=1;network_step(0,packet,48+size);assert(network_output(out,sizeof(out))==0);
  put16(packet+46,0);network_step(0,packet,48+size);assert(network_output(out,sizeof(out))==0);
 }
 memset(packet,0,56);ip6(packet,56,58);packet[40]=128;put16(packet+42,sum6(packet,56));network_step(10,packet,56);
 n=network_output(out,sizeof(out));assert(n==60&&out[44]==129&&sum6(out+4,56)==0);
 packet[4]=1;network_step(0,packet,56);assert(network_output(out,sizeof(out))==0);
 network_step(0,packet,39);assert(network_output(out,sizeof(out))==0);
 puts("IPv6 native: UDP 0/1/31/500/1400/1452, mandatory checksums, ICMPv6 and truncated inputs passed");
}
int main(void){
 unsigned char packet[1600],out[8192];unsigned int n,size,i,j;
 network_init();test_ipv6();
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

/* Native network harness clock; production obtains this from RTEMS ticks. */
unsigned int http_uptime_seconds(void){return sys_now()/1000;}

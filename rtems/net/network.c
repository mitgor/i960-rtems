#include <string.h>
#include "lwip/init.h"
#include "lwip/netif.h"
#include "lwip/ip.h"
#include "lwip/ip6.h"
#include "lwip/udp.h"
#include "lwip/tcp.h"
#include "lwip/dns.h"
#include "lwip/timeouts.h"
#include "buffer_io.h"
#include "network.h"
#include "http.h"
static struct netif cardif;
static unsigned int now_ms,random_state=0x1960466,tx_count,rx_count,drops;
/* Resident profile may use more of its separately audited owned RAM. */
#ifndef NETWORK_QUEUE_SLOTS
#define NETWORK_QUEUE_SLOTS 8
#endif
#ifndef NETWORK_LENGTH_SLOTS
#define NETWORK_LENGTH_SLOTS NETWORK_QUEUE_SLOTS
#endif
static unsigned short lengths[NETWORK_LENGTH_SLOTS];
#ifndef NETWORK_FRAME_BYTES
#define NETWORK_FRAME_BYTES 1536
#endif
#ifdef NETWORK_EXTERNAL_QUEUE
static unsigned char internal_frames[68][NETWORK_FRAME_BYTES] __attribute__((aligned(16)));
static unsigned char (*frames)[NETWORK_FRAME_BYTES]=internal_frames;
#else
static unsigned char frames[NETWORK_QUEUE_SLOTS][NETWORK_FRAME_BYTES];
#endif
static unsigned int head,tail,queued;
#ifdef RESIDENT_QUEUE_STATS
static unsigned int queue_highwater;
unsigned int resident_queue_drops(void){return drops;}
unsigned int resident_queue_peak(void){return queue_highwater;}
#endif
static unsigned char fetch_bytes[8192];
static unsigned int fetch_length,fetch_hash,fetch_state,fetch_port;
static char fetch_name[128];
static struct tcp_pcb *fetch_pcb;
unsigned int card_rand(void){random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;return random_state;}
u32_t sys_now(void){return now_ms;}
static err_t enqueue(struct pbuf*p){
 if(p->tot_len>NETWORK_FRAME_BYTES||queued==NETWORK_QUEUE_SLOTS){drops++;return ERR_MEM;}
 lengths[tail]=p->tot_len;pbuf_copy_partial(p,frames[tail],p->tot_len,0);tail=(tail+1)%NETWORK_QUEUE_SLOTS;queued++;tx_count++;
#ifdef RESIDENT_QUEUE_STATS
 if(queued>queue_highwater)queue_highwater=queued;
#endif
 return ERR_OK;
}
static err_t output(struct netif*n,struct pbuf*p,const ip4_addr_t*addr){return enqueue(p);}
static err_t output6(struct netif*n,struct pbuf*p,const ip6_addr_t*addr){return enqueue(p);}
static err_t netinit(struct netif*n){n->name[0]='i';n->name[1]='9';n->mtu=1500;n->output=output;n->output_ip6=output6;n->flags=NETIF_FLAG_LINK_UP;return ERR_OK;}
static void udp_recv_cb(void*a,struct udp_pcb*pcb,struct pbuf*p,const ip_addr_t*addr,u16_t port){if(p){udp_sendto(pcb,p,addr,port);pbuf_free(p);}}
static err_t echo_recv(void*a,struct tcp_pcb*pcb,struct pbuf*p,err_t e){
 static unsigned char bytes[TCP_WND];err_t result;
 if(!p)return tcp_close(pcb);
 if(e!=ERR_OK){pbuf_free(p);return e;}
 if(p->tot_len>sizeof(bytes)||p->tot_len>tcp_sndbuf(pcb))return ERR_MEM;
 pbuf_copy_partial(p,bytes,p->tot_len,0);result=tcp_write(pcb,bytes,p->tot_len,TCP_WRITE_FLAG_COPY);if(result!=ERR_OK)return result;
 tcp_recved(pcb,p->tot_len);pbuf_free(p);tcp_output(pcb);return ERR_OK;
}
static err_t accepted(void*a,struct tcp_pcb*pcb,err_t e){tcp_nagle_disable(pcb);tcp_recv(pcb,echo_recv);return ERR_OK;}
static void fetch_error(void*a,err_t e){fetch_pcb=0;fetch_state=0x80000000u|(unsigned int)(unsigned char)(-e);}
static err_t fetched(void*a,struct tcp_pcb*pcb,struct pbuf*p,err_t e){
 unsigned int n,i;unsigned char temp[256];
 if(!p){fetch_state=4;fetch_pcb=0;return tcp_close(pcb);}
 if(e!=ERR_OK){pbuf_free(p);return e;}
 for(n=0;n<p->tot_len;n+=i){i=p->tot_len-n;if(i>sizeof(temp))i=sizeof(temp);pbuf_copy_partial(p,temp,i,n);
  {unsigned int j;for(j=0;j<i;j++){fetch_hash=(fetch_hash^temp[j])*16777619u;if(fetch_length<sizeof(fetch_bytes))fetch_bytes[fetch_length]=temp[j];fetch_length++;}}}
 tcp_recved(pcb,p->tot_len);pbuf_free(p);return ERR_OK;
}
static err_t connected(void*a,struct tcp_pcb*pcb,err_t e){
 char request[256];unsigned int n;
 if(e!=ERR_OK){fetch_error(0,e);return e;}
 memcpy(request,"GET / HTTP/1.0\r\nHost: ",22);n=22;
 memcpy(request+n,fetch_name,strlen(fetch_name));n+=strlen(fetch_name);
 memcpy(request+n,"\r\nConnection: close\r\n\r\n",23);n+=23;
 tcp_recv(pcb,fetched);fetch_state=3;
 e=tcp_write(pcb,request,n,TCP_WRITE_FLAG_COPY);if(e!=ERR_OK){fetch_state=0x81000000|(unsigned char)(-e);return e;}
 return tcp_output(pcb);
}
static void resolved(const char*name,const ip_addr_t*ip,void*a){
 err_t e;if(!ip){fetch_state=0x80000100;return;}
 fetch_pcb=tcp_new_ip_type(IP_GET_TYPE(ip));if(!fetch_pcb){fetch_state=0x80000200;return;}
 tcp_err(fetch_pcb,fetch_error);fetch_state=2;e=tcp_connect(fetch_pcb,ip,fetch_port,connected);
 if(e!=ERR_OK){tcp_abort(fetch_pcb);fetch_pcb=0;fetch_state=0x82000000|(unsigned char)(-e);}
}
void network_fetch(const char*name,unsigned int port,unsigned int ipv6){
 ip_addr_t ip;err_t e;unsigned int n=strlen(name);
 if(fetch_pcb||fetch_state==1||n==0||n>=sizeof(fetch_name))return;
 memcpy(fetch_name,name,n+1);fetch_port=port;fetch_length=0;fetch_hash=2166136261u;fetch_state=1;
 e=dns_gethostbyname_addrtype(fetch_name,&ip,resolved,0,ipv6?LWIP_DNS_ADDRTYPE_IPV6:LWIP_DNS_ADDRTYPE_IPV4);
 if(e==ERR_OK)resolved(fetch_name,&ip,0);else if(e!=ERR_INPROGRESS)fetch_state=0x83000000|(unsigned char)(-e);
}
void network_init(void){
 ip4_addr_t ip,mask,gw;ip6_addr_t ip6;ip_addr_t dns;struct udp_pcb*u;struct tcp_pcb*t;
 lwip_init();IP4_ADDR(&ip,10,196,0,2);IP4_ADDR(&mask,255,255,255,252);IP4_ADDR(&gw,10,196,0,1);
 netif_add(&cardif,&ip,&mask,&gw,0,netinit,ip_input);netif_set_default(&cardif);netif_set_up(&cardif);netif_set_link_up(&cardif);
 /* Static addresses on a point-to-point IP link; no ND/MAC resolution. */
 ip6addr_aton("fe80::960:2",&ip6);netif_ip6_addr_set(&cardif,0,&ip6);netif_ip6_addr_set_state(&cardif,0,IP6_ADDR_PREFERRED);
 ip6addr_aton("fd96:196:960::2",&ip6);netif_ip6_addr_set(&cardif,1,&ip6);netif_ip6_addr_set_state(&cardif,1,IP6_ADDR_PREFERRED);
 IP_ADDR4(&dns,192,168,2,3);dns_setserver(0,&dns);
 u=udp_new_ip_type(IPADDR_TYPE_ANY);if(!u)bounded_fatal(0x601);if(udp_bind(u,IP_ANY_TYPE,9601)!=ERR_OK)bounded_fatal(0x602);udp_recv(u,udp_recv_cb,0);
 t=tcp_new_ip_type(IPADDR_TYPE_ANY);if(!t)bounded_fatal(0x603);if(tcp_bind(t,IP_ANY_TYPE,9600)!=ERR_OK)bounded_fatal(0x604);t=tcp_listen(t);if(!t)bounded_fatal(0x605);tcp_accept(t,accepted);http_init();
}
void network_step(unsigned int ms,const unsigned char*packet,unsigned int length){
 now_ms+=ms;
 if(length){struct pbuf*p;if(length>1500){drops++;return;}p=pbuf_alloc(PBUF_RAW,length,PBUF_POOL);
  if(!p){drops++;return;}pbuf_take(p,packet,length);rx_count++;if(cardif.input(p,&cardif)!=ERR_OK)pbuf_free(p);}
 sys_check_timeouts();
}
unsigned int network_output(unsigned char*out,unsigned int cap){unsigned int n=0;while(queued&&n+4+lengths[head]<=cap){bio_put(out+n,lengths[head]);n+=4;memcpy(out+n,frames[head],lengths[head]);n+=lengths[head];head=(head+1)%NETWORK_QUEUE_SLOTS;queued--;}return n;}
unsigned int network_report(unsigned char*out){bio_put(out,rx_count);bio_put(out+4,tx_count);bio_put(out+8,drops);bio_put(out+12,fetch_state);bio_put(out+16,fetch_length);bio_put(out+20,fetch_hash);return 24;}
unsigned int network_fetch_data(unsigned char*out,unsigned int offset,unsigned int limit){unsigned int n=fetch_length;if(n>sizeof(fetch_bytes))n=sizeof(fetch_bytes);if(offset>=n)return 0;n-=offset;if(n>limit)n=limit;memcpy(out,fetch_bytes+offset,n);return n;}

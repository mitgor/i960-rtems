/* Bounded raw-API HTTP server. One response per connection, no dynamic buffers. */
#include <string.h>
#include "lwip/tcp.h"
#include "buffer_io.h"
#include "http.h"
#include "network.h"
#include "system_info.h"
#define CLIENTS 4
#define REQUEST_LIMIT 512
struct client {struct tcp_pcb *pcb; unsigned int length,idle,sending; char request[REQUEST_LIMIT];};
static struct client clients[CLIENTS];
#ifdef I960_BACKGROUND_NET
#define CLOCK_DESCRIPTION "Hardware timer interrupts drive RTEMS and network timers independently of host polling."
#else
#define CLOCK_DESCRIPTION "Execution is currently cooperative and host-polled."
#endif
static unsigned int page_requests;
static char page_buffer[4096];
static const char page[]=
"HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n<!doctype html><html><head><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Darth Vader | i960 RTEMS</title><style>body{background:#08090b;color:#eee;text-align:center;font-family:monospace;margin:3em 1em}pre{display:inline-block;text-align:left;color:#ddd;line-height:1.15;font-size:clamp(10px,3vw,16px)}h1{color:#f44}table{margin:1em auto;max-width:850px;border-collapse:collapse;text-align:left}th,td{padding:.6em;border-bottom:1px solid #333;vertical-align:top}th{width:30%;color:#faa}a{color:#faa}p{max-width:640px;margin:1em auto;line-height:1.5}</style></head><body><h1>Darth Vader</h1><pre role=\"img\" aria-label=\"ASCII portrait of Darth Vader\">              .-=========-.\n            .&#x27;             &#x27;.\n           /    .-------.    \\\n          /    /         \\    \\\n         |    |           |    |\n         |    |  ___ ___  |    |\n         |    | /   V   \\ |    |\n         |    | \\___|___/ |    |\n         |    /     |     \\    |\n         |   /    /---\\    \\   |\n         /  /    /|||||\\    \\  \\\n        /__/____/|||||||\\____\\__\\\n       /        \\=======/        \\\n      /__________\\=====/__________\\\n         /       |===|       \\\n        /________|___|________\\\n</pre><p>The Force is strong with this i960.</p><p>Served by RTEMS 4.6.6 and lwIP on a Mylex DAC960 card over IPv6.</p><p>"
CLOCK_DESCRIPTION "</p>";
static const char unavailable[]="HTTP/1.0 500 Internal Server Error\r\nConnection: close\r\nContent-Length: 0\r\n\r\n";
static const char *render_page(void){unsigned char stats[24];unsigned int i,active=0;struct info_writer w={page_buffer,sizeof(page_buffer),0,0};
 for(i=0;i<CLIENTS;i++)if(clients[i].pcb)active++;
 network_report(stats);info_text(&w,page);
 system_info(&w,http_uptime_seconds(),++page_requests,bio_word(stats),bio_word(stats+4),bio_word(stats+8),active);
 info_text(&w,"</body></html>\n");return w.failed?unavailable:page_buffer;
}
static const char bad[]="HTTP/1.0 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n";
static const char large[]="HTTP/1.0 431 Request Header Fields Too Large\r\nConnection: close\r\nContent-Length: 0\r\n\r\n";
static void failed(void *arg,err_t err){struct client*c=arg;if(c)memset(c,0,sizeof(*c));}
static err_t abort_client(struct client*c){struct tcp_pcb*p=c->pcb;tcp_arg(p,0);tcp_err(p,0);memset(c,0,sizeof(*c));tcp_abort(p);return ERR_ABRT;}
static err_t sent(void*,struct tcp_pcb*,u16_t);
static err_t poll(void*,struct tcp_pcb*);
static err_t receive(void*,struct tcp_pcb*,struct pbuf*,err_t);
static err_t close_client(struct client*c){struct tcp_pcb*p=c->pcb;err_t e;
 tcp_arg(p,0);tcp_recv(p,0);tcp_sent(p,0);tcp_poll(p,0,0);tcp_err(p,0);
 e=tcp_close(p);
 if(e==ERR_OK)memset(c,0,sizeof(*c));
 else {tcp_arg(p,c);tcp_recv(p,receive);tcp_sent(p,sent);tcp_poll(p,poll,2);tcp_err(p,failed);}
 return e;
}
static err_t sent(void*arg,struct tcp_pcb*p,u16_t n){struct client*c=arg;if(c&&c->sending){if(tcp_sndbuf(p)==TCP_SND_BUF)close_client(c);}return ERR_OK;}
static err_t poll(void*arg,struct tcp_pcb*p){struct client*c=arg;if(!c)return ERR_OK;if(++c->idle>=10)return abort_client(c);if(c->sending&&tcp_sndbuf(p)==TCP_SND_BUF)close_client(c);return ERR_OK;}
static err_t receive(void*arg,struct tcp_pcb*p,struct pbuf*b,err_t err){
 struct client*c=arg;const char*response=0;unsigned int n,i;err_t e;
 if(!c){if(b)pbuf_free(b);return ERR_OK;}
 if(!b){close_client(c);return ERR_OK;}
 if(err!=ERR_OK){pbuf_free(b);return ERR_OK;}
 c->idle=0;n=b->tot_len;
 if(!c->sending){
  if(n>REQUEST_LIMIT-c->length)response=large;
  else {pbuf_copy_partial(b,c->request+c->length,n,0);c->length+=n;
   for(i=3;i<c->length;i++)if(!memcmp(c->request+i-3,"\r\n\r\n",4)){response=c->length>=6&&!memcmp(c->request,"GET /",5)?render_page():bad;break;}
   if(!response&&c->length==REQUEST_LIMIT)response=large;
  }
 }
 tcp_recved(p,n);pbuf_free(b);
 if(response){e=tcp_write(p,response,strlen(response),TCP_WRITE_FLAG_COPY);if(e!=ERR_OK)return abort_client(c);c->sending=1;tcp_output(p);}
 return ERR_OK;
}
static err_t accept_client(void*arg,struct tcp_pcb*p,err_t err){unsigned int i;struct client*c=0;for(i=0;i<CLIENTS;i++)if(!clients[i].pcb){c=clients+i;break;}if(!c){tcp_abort(p);return ERR_ABRT;}memset(c,0,sizeof(*c));c->pcb=p;tcp_arg(p,c);tcp_recv(p,receive);tcp_sent(p,sent);tcp_err(p,failed);tcp_poll(p,poll,2);return ERR_OK;}
void http_init(void){struct tcp_pcb*p=tcp_new_ip_type(IPADDR_TYPE_ANY);if(!p)bounded_fatal(0x610);if(tcp_bind(p,IP_ANY_TYPE,80)!=ERR_OK)bounded_fatal(0x611);p=tcp_listen(p);if(!p)bounded_fatal(0x612);tcp_accept(p,accept_client);}

/* Small resident proof endpoint; TCP owns a copied response before close. */
#include "lwip/tcp.h"
static unsigned int requests;
static const char reply[]="HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nRTEMS resident IPv4/IPv6 on i960\nNo pending firmware callback. Host link: message-register PIO.\n";
static err_t receive(void*a,struct tcp_pcb*p,struct pbuf*b,err_t error){err_t e;
 if(!b)return tcp_close(p);
 if(error!=ERR_OK){pbuf_free(b);return error;}
 e=tcp_write(p,reply,sizeof(reply)-1,TCP_WRITE_FLAG_COPY);if(e!=ERR_OK)return e;
 tcp_recved(p,b->tot_len);pbuf_free(b);requests++;tcp_recv(p,0);tcp_output(p);tcp_close(p);return ERR_OK;
}
static err_t accept(void*a,struct tcp_pcb*p,err_t e){tcp_recv(p,receive);return ERR_OK;}
void http_init(void){struct tcp_pcb*p=tcp_new_ip_type(IPADDR_TYPE_ANY);if(!p||tcp_bind(p,IP_ANY_TYPE,80)!=ERR_OK)bounded_fatal(0x56002);p=tcp_listen(p);if(!p)bounded_fatal(0x56003);tcp_accept(p,accept);}

/* Stop-and-wait PIO; never accesses host or reclaimed DRAM. Caller serializes. */
#ifndef RESIDENT_PACKET_H
#define RESIDENT_PACKET_H
#define PACKET_CAP 1536u
struct packet_link {unsigned char rx[PACKET_CAP],tx[PACKET_CAP];volatile unsigned int length,words,ready,txlen,received,sent,rejected;};
static unsigned int packet_word(const unsigned char*p){return p[0]|((unsigned int)p[1]<<8)|((unsigned int)p[2]<<16)|((unsigned int)p[3]<<24);}
static unsigned int packet_command(struct packet_link*p,unsigned int op,unsigned int index,unsigned int value,unsigned int running){
 unsigned int i,n;
 if(!running){p->rejected++;return 0xfffffffeu;}
 if(op==10){if(index||value<20||value>1500||p->ready)goto bad;p->length=value;p->words=0;return 0;}
 if(op==11){if(!p->length||p->ready||index!=p->words||index>=(p->length+3)/4)goto bad;
  for(i=0;i<4;i++)p->rx[index*4+i]=(unsigned char)(value>>(8*i));p->words++;return 0;}
 if(op==12){if(index||!p->length||p->ready||p->words!=(p->length+3)/4)goto bad;p->ready=1;p->received++;return 0;}
 if(op==13){if(index)goto bad;return p->txlen;}
 if(op==14){if(!p->txlen||index>=(p->txlen+3)/4)goto bad;return packet_word(p->tx+index*4);}
 if(op==15){if(index||!p->txlen)goto bad;n=p->txlen;p->txlen=0;p->sent++;return n;}
 bad:p->rejected++;return 0xffffffffu;
}
#endif

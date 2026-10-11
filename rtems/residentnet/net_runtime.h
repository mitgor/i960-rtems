#include "../residentnet/packet.h"
#include "../residentnet/ram.h"
#include "../residentnet/board.h"
#include "../net/network.h"
extern unsigned int resident_queue_drops(void),resident_queue_peak(void);
#ifdef I960_SECONDARY_RESET
extern unsigned int scsi_target_verified(void);
#endif
static struct packet_link netlink;
static unsigned int net_tick,net_ready,net_memory_ok;
static void resident_net_init(void){unsigned int identity[7];
 identity[0]=(*(volatile unsigned char*)0xe0400000)&31;identity[1]=R(0xc011e22c);
 if(identity[1]!=0xc0110780u)bounded_fatal(0x56010);
 identity[2]=R(identity[1]+0xc0);identity[3]=R(identity[1]+0x168);
 identity[4]=R(0xc00a8718);identity[5]=R(0xc0112a70);identity[6]=R(identity[1]+8);
 if(resident_board_admit(identity))bounded_fatal(0x56011);

 net_memory_ok=ram_owned((unsigned int)&netlink,sizeof(netlink));
 if(!net_memory_ok)bounded_fatal(0x56001);
 network_init();net_ready=1;
}
static void resident_net_step(void){unsigned int n=0,elapsed=ticks-net_tick;
 if(!net_ready||resident_state!=1)return;
 if(netlink.ready)n=netlink.length;
 if(n||elapsed){network_step(elapsed*10,netlink.rx,n);net_tick=ticks;}
 if(n){netlink.ready=0;netlink.length=0;netlink.words=0;}
 if(!netlink.txlen){memset(netlink.tx,0,sizeof(netlink.tx));netlink.txlen=network_output(netlink.tx,sizeof(netlink.tx));}
}
static unsigned int resident_net_control(unsigned int token){unsigned int op=token>>28,value;
 if(op<10)return 0;
 value=packet_command(&netlink,op,(token>>16)&0xfff,R(0x1310),resident_state==1&&net_ready);
 R(0x1318)=value;(void)R(0x1318);R(0x1314)=0;R(0x131c)=token|0x08000000u;(void)R(0x131c);
 R(0x1324)=2;(void)R(0x1324);return 1;
}
static void resident_net_report(unsigned int*w){
 w[57]=0x33544e52; /* RNT3: 72 slots, each holding one <=1500-byte IP packet */
 w[58]=resident_queue_drops();w[59]=resident_queue_peak();
 w[60]=netlink.received;w[61]=netlink.sent;w[62]=netlink.rejected;w[63]=net_memory_ok;
#ifdef I960_SECONDARY_RESET
 w[63]|=scsi_target_verified()?2:0;
#endif
}

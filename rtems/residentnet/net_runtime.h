#include "../residentnet/packet.h"
#include "../residentnet/ram.h"
#include "../net/network.h"
static struct packet_link netlink;
static unsigned int net_tick,net_ready,net_memory_ok;
static void resident_net_init(void){
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
 w[57]=*(volatile unsigned short*)0x40800008;
 w[58]=*(volatile unsigned short*)0x4080000a;
 w[59]=R(0x40800000);
 w[60]=netlink.received;w[61]=netlink.sent;w[62]=netlink.rejected;w[63]=net_memory_ok;
}

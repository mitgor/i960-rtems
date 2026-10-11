#include "../residentnet/packet.h"
#include "../residentnet/ram.h"
#include "../residentnet/board.h"
#include "../net/network.h"
extern unsigned int resident_queue_drops(void),resident_queue_peak(void);
#ifdef I960_SECONDARY_RESET
extern unsigned int scsi_target_verified(void);
#endif
#ifdef I960_FAULT_OWNER
extern unsigned int exclusive_fault_valid(void);
#endif
#ifdef I960_EXTRA_RAM
extern unsigned int exclusive_extra_valid(void);
extern void exclusive_extra_report(unsigned int*);
extern void exclusive_abort(void);
#endif
#ifdef I960_GENERAL_HEAP
#include "general_heap.h"
#endif
static struct packet_link netlink;
static unsigned int net_tick,net_ready,net_memory_ok;
#ifdef I960_QUEUE_RECLAIM
static unsigned int net_irq_spans[2];
void resident_net_irq_counts(unsigned int*w){w[0]=net_irq_spans[0];w[1]=net_irq_spans[1];}
#endif
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
static void resident_net_step(void){unsigned int n=0,now,elapsed,output,before;
 if(!net_ready||resident_state!=1)return;
#ifdef I960_EXTRA_RAM
#ifdef I960_GENERAL_HEAP
 resident_heap_check();
#else
 if(!exclusive_extra_valid())exclusive_abort();
#endif
#endif
#ifdef I960_QUEUE_RECLAIM
 mask();
#endif
 now=ticks;elapsed=now-net_tick;
 if(netlink.ready)n=netlink.length;
#ifdef I960_QUEUE_RECLAIM
 /* ready remains asserted: ISR cannot overwrite the leased RX bytes. */
 enable();
#endif
 if(n||elapsed){before=ticks;network_step(elapsed*10,netlink.rx,n);net_tick=now;
#ifdef I960_QUEUE_RECLAIM
  if(ticks!=before)net_irq_spans[0]++;
#endif
 }
#ifdef I960_QUEUE_RECLAIM
 mask();
#endif
 if(n){netlink.length=0;netlink.words=0;netlink.ready=0;}
 output=!netlink.txlen;
#ifdef I960_QUEUE_RECLAIM
 enable();
#endif
 /* Only worker 0 writes TX storage. txlen==0 hides it from every ISR read.
  * Once published it remains immutable until the host acknowledges it. */
 if(output){before=ticks;memset(netlink.tx,0,sizeof(netlink.tx));output=network_output(netlink.tx,sizeof(netlink.tx));
#ifdef I960_QUEUE_RECLAIM
  if(ticks!=before)net_irq_spans[1]++;
  mask();
#endif
  netlink.txlen=output;
#ifdef I960_QUEUE_RECLAIM
  enable();
#endif
 }
}
static unsigned int resident_net_control(unsigned int token){unsigned int op=token>>28,value;
 if(op<10)return 0;
 value=packet_command(&netlink,op,(token>>16)&0xfff,R(0x1310),resident_state==1&&net_ready
#ifdef I960_OWNED_MIB
 &&!stop
#endif
 );
 R(0x1318)=value;(void)R(0x1318);R(0x1314)=0;R(0x131c)=token|0x08000000u;(void)R(0x131c);
 R(0x1324)=2;(void)R(0x1324);return 1;
}
static void resident_net_report(unsigned int*w){
 w[57]=0x33544e52; /* RNT3: 72 slots, each holding one <=1500-byte IP packet */
#ifdef I960_FAULT_OWNER
 w[57]=0x34544e52; /* RNT4: 68 slots and owned exception storage */
#endif
#ifdef I960_EXTRA_RAM
 w[57]=0x35544e52; /* RNT5: fixed guarded external queue, 128 slots */
 {unsigned int report[8];exclusive_extra_report(report);
 w[48]=0xc0200040u;w[49]=128*1500;w[50]=report[0];w[51]=report[1];}
#endif
#ifdef I960_GENERAL_HEAP
 {unsigned int heap[16];resident_heap_report(heap);w[57]=0x36544e52;
 w[48]=heap[1];w[49]=heap[2];w[50]=heap[5];w[51]=heap[6];}
#endif
#ifdef I960_HEAP_SHARED
 w[57]=0x37544e52; /* RNT7: shared-allocation cancellation + separate diagnostics */
#endif
#ifdef I960_QUEUE_RECLAIM
 w[57]=0x38544e52; /* RNT8: reclaimed fallback heap and preemptible network worker */
#endif
 w[58]=resident_queue_drops();w[59]=resident_queue_peak();
 w[60]=netlink.received;w[61]=netlink.sent;w[62]=netlink.rejected;w[63]=net_memory_ok;
#ifdef I960_SECONDARY_RESET
 w[63]|=scsi_target_verified()?2:0;
#ifdef I960_FAULT_OWNER
 w[63]|=exclusive_fault_valid()?4:0;
#ifdef I960_EXTRA_RAM
 w[63]|=exclusive_extra_valid()?8:0;
#ifdef I960_GENERAL_HEAP
 w[63]|=resident_heap_valid()?16:0;
#endif
#endif
#endif
#endif
}

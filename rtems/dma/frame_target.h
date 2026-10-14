/* Same-frame DMA: called only by the pinned renderer's RTEMS worker.
 * Failure must never return to the renderer or release its arena. */
#ifndef FD_R
#define FD_R(a) (*(volatile unsigned *)(a))
#define FD_S(a) (*(volatile unsigned short *)(a))
#define FD_ADDR(p) ((unsigned)(p))
#define FD_FATAL() exclusive_abort()
static unsigned fd_lock(void){unsigned pc=31u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(pc)::"g0","memory");return pc;}
static void fd_unlock(unsigned pc){__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(pc)::"g0","memory");}
#define FD_LOCK() fd_lock()
#define FD_UNLOCK(pc) fd_unlock(pc)
#endif
static unsigned fd_report[16],fd_destination;
static volatile unsigned fd_phase,fd_stage,fd_loops;
static unsigned fd_isolation_checks;
#define FD_STAGE(n) do{__asm__ volatile("":::"memory");fd_stage=(n);__asm__ volatile("":::"memory");}while(0)
unsigned frame_dma_diagnostic(unsigned i){
 if(i<16)return i==1?fd_phase:fd_report[i];
 switch(i){case 16:return fd_stage;case 17:return fd_loops;case 18:return FD_R(0x1444);case 19:return FD_R(0x144c);case 20:return FD_R(0x1450);case 21:return FD_R(0x1460);case 22:return FD_R(0x1440);case 23:return FD_S(0x1204);default:return 0;}
}
static volatile unsigned fd_storage[16] __attribute__((aligned(16)));
#define fd_desc ((volatile unsigned*)(((unsigned long)fd_storage+31)&~31UL))
/* A scheduled peer may validate heap/isolation while this worker is paused
 * inside its owned transaction. Normalize only that exact DMA1 lease in the
 * caller's local snapshot; all other isolation fields retain strict checks.
 * Caller masks task switching while taking/validating the snapshot. */
unsigned frame_dma_isolation_snapshot(unsigned *w){unsigned i;
 if(fd_phase!=1||fd_stage<4||fd_stage>10||!play_frame||play_ack||
    play_sequence!=fd_report[2]||FD_ADDR(play_frame)!=fd_report[4]||
    fd_report[13]||fd_destination!=fd_report[3]||
    fd_destination<=4096||fd_destination>0xffffffffu-65536||
    fd_report[4]<0xc0240000u||fd_report[4]>0xc0e30000u||
    fd_report[15]!=FD_ADDR(fd_desc)||fd_report[15]<0xc0f4c010u||
    fd_report[15]>0xc0f8bfe0u||(fd_report[15]&31))return 0;
 for(i=0;i<8;i++){
  unsigned expected=i==1?fd_destination:i==3?fd_report[4]:i==4?65536:i==5?7:i>=6?0xfacefeed:0;
  if(fd_desc[i]!=expected)return 0;
 }
 if(w[0]||w[1]||w[4]||w[5]||w[2]>1||(w[3]&~0x400u)||
    (w[6]!=2&&w[6]!=6))return 0;
 if(fd_stage==4&&(w[2]||w[3]))return 0;
 if(fd_stage>=5&&fd_stage<=9&&w[6]!=6)return 0;
 if(fd_stage==5&&(w[2]||w[3]))return 0;
 if(fd_stage>=7&&fd_stage<=8&&w[2]!=1)return 0;
 if(fd_stage==10&&(w[2]||w[3]))return 0;
 w[2]=w[3]=0;w[6]=2;fd_isolation_checks++;return 1;
}
static unsigned fd_crc(const unsigned char*p){
 static const unsigned table[16]={0,0x1db71064,0x3b6e20c8,0x26d930ac,0x76dc4190,0x6b6b51f4,0x4db26158,0x5005713c,0xedb88320,0xf00f9344,0xd6d6a3e8,0xcb61b38c,0x9b64c2b0,0x86d3d2d4,0xa00ae278,0xbdbdf21c};
 unsigned c=~0u,n;for(n=0;n<65536;n++){c^=p[n];c=(c>>4)^table[c&15];c=(c>>4)^table[c&15];}return ~c;
}
static unsigned fd_idle(void){
 return !FD_R(0x1400)&&!FD_R(0x1404)&&!FD_R(0x1440)&&!FD_R(0x1444)&&!FD_R(0x1480)&&!FD_R(0x1484)&&FD_S(0x1204)==2&&FD_S(0x1298)==0&&FD_R(0x104c)==0x13ffc;
}
static unsigned fd_control(unsigned index,unsigned value){
 if(index==5)return value==16?fd_isolation_checks:value==1?fd_phase:value<16?fd_report[value]:~0u;
 if(fd_phase==1||!play_frame||play_ack)return ~0u;
 if(index==3){if(!value||value>0xffffffffu-65536)return ~0u;fd_destination=value;return 0;}
 if(index!=4||!fd_destination||!value||value!=play_sequence||value<=fd_report[2])return ~0u;
 fd_report[0]=0x314d4446;fd_report[2]=value;fd_report[3]=fd_destination;
 fd_report[4]=FD_ADDR(play_frame);fd_report[13]=0;
 __asm__ volatile("":::"memory");fd_phase=1;return 0;
}
static void fd_step(void){unsigned i,csr=0,rc=0;const unsigned char*source=play_frame;
 if(fd_phase!=1)return;
 if(!source||play_ack||play_sequence!=fd_report[2]||!fd_idle()){rc=1;goto failed;}
 FD_STAGE(1);fd_loops=0;fd_report[5]=fd_crc(source);FD_STAGE(2);
 fd_desc[0]=0;fd_desc[1]=fd_destination;fd_desc[2]=0;fd_desc[3]=FD_ADDR(source);fd_desc[4]=65536;fd_desc[5]=7;fd_desc[6]=0xfacefeed;fd_desc[7]=0xfacefeed;
 fd_report[15]=FD_ADDR(fd_desc);FD_STAGE(3);
 if(play_api->stopping()){rc=2;goto failed;}
 FD_STAGE(4);FD_S(0x1204)=6;if(FD_S(0x1204)!=6){rc=3;goto cleanup;}
 FD_STAGE(5);FD_R(0x1450)=FD_ADDR(fd_desc);(void)FD_R(0x1450);FD_STAGE(6);FD_R(0x1440)=1;(void)FD_R(0x1440);FD_STAGE(7);
 for(i=0;i<200000;i++){
  fd_loops=i;csr=FD_R(0x1444);if(csr&~0x400u){rc=4;break;}
  if(!csr&&!FD_R(0x1450)&&FD_R(0x144c)==FD_ADDR(fd_desc)&&!FD_R(0x1460))break;
 }
 FD_STAGE(8);if(i==200000)rc=5;
 fd_report[7]=csr;fd_report[8]=FD_R(0x144c);fd_report[9]=FD_R(0x1450);fd_report[10]=FD_R(0x1460);fd_report[11]=FD_R(0x1464);fd_report[12]=i;
cleanup:
 FD_STAGE(9);FD_R(0x1440)=0;(void)FD_R(0x1440);FD_STAGE(10);FD_S(0x1204)=2;(void)FD_S(0x1204);FD_STAGE(11);
 if(rc)goto failed;
 fd_report[6]=fd_crc(source);FD_STAGE(12);
 if(!fd_idle()||FD_R(0x1450)||fd_report[5]!=fd_report[6]||fd_desc[6]!=0xfacefeed||fd_desc[7]!=0xfacefeed){rc=6;goto failed;}
 FD_STAGE(13);__asm__ volatile("":::"memory");fd_phase=2;return;
failed:
 fd_report[13]=rc;FD_FATAL(); /* nonreturning quarantine, frame remains pinned */
}

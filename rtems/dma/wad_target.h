/* WAD DMA1 Memory Read. IRQ stages a fixed request; only its owning task
 * starts hardware. A completion ACK pins both mappings through validation. */
static unsigned wd_host,wd_sequence,wd_report[12];
static volatile unsigned wd_phase,wd_stage;
static unsigned char *wd_buffer;
static volatile unsigned wd_storage[16] __attribute__((aligned(16)));
#ifndef WD_R
#define WD_ADDR(p) ((unsigned)(p))
#define WD_R(a) (*(volatile unsigned *)(a))
#define WD_S(a) (*(volatile unsigned short *)(a))
#endif
#define wd_desc ((volatile unsigned*)(((unsigned long)wd_storage+31)&~31UL))
static unsigned wd_idle(void){return !WD_R(0x1400)&&!WD_R(0x1404)&&!WD_R(0x1440)&&!WD_R(0x1444)&&!WD_R(0x1480)&&!WD_R(0x1484)&&WD_S(0x1204)==2&&WD_S(0x1298)==0&&WD_R(0x104c)==0x13ffc;}
unsigned wad_dma_isolation_snapshot(unsigned*w){unsigned i;
 if(wd_phase!=1||wd_stage<4||wd_stage>10||!wd_buffer||batch.state!=WAD_REQUEST||wd_sequence!=batch.sequence||wd_report[0]!=wd_sequence||wd_report[1]!=wd_host||wd_report[2]!=WD_ADDR(wd_buffer+4096))return 0;
 for(i=0;i<8;i++){unsigned e=i==1?wd_host:i==3?WD_ADDR(wd_buffer+4096):i==4?4096:i==5?6:i>=6?0xfacefeed:0;if(wd_desc[i]!=e)return 0;}
 if(w[0]||w[1]||w[4]||w[5]||w[2]>1||(w[3]&~0x400u)||(w[6]!=2&&w[6]!=6))return 0;
 if(wd_stage==4&&(w[2]||w[3]))return 0;
 if(wd_stage>=5&&wd_stage<=9&&w[6]!=6)return 0;
 if(wd_stage==5&&(w[2]||w[3]))return 0;
 if(wd_stage>=7&&wd_stage<=8&&w[2]!=1)return 0;
 if(wd_stage==10&&(w[2]||w[3]))return 0;
 w[2]=w[3]=0;w[6]=2;return 1;
}
static unsigned wd_control(unsigned index,unsigned value,unsigned running){
 if(index==3)return value?~0u:wd_phase;
 if(index==4)return value<12?wd_report[value]:~0u;
 if(index==5){if(wd_phase!=2||value!=wd_sequence)return ~0u;wd_phase=3;return 0;}
 if(!running||batch.state!=WAD_REQUEST||!wd_buffer||batch.fragments||batch.expected||wd_phase)return ~0u;
 if(index==1){if(!value||(value&3)||value>0xffffffffu-4096)return ~0u;wd_host=value;return 0;}
 if(index!=2||!wd_host||value!=batch.sequence||value<=wd_sequence)return ~0u;
 wd_sequence=value;wd_report[0]=value;wd_report[1]=wd_host;wd_report[2]=WD_ADDR(wd_buffer+4096);wd_report[3]=4096;wd_report[11]=0;
 __asm__ volatile("":::"memory");wd_phase=1;return 0;
}
#define WD_STAGE(n) do{__asm__ volatile("":::"memory");wd_stage=n;__asm__ volatile("":::"memory");}while(0)
static void wd_step(void){unsigned i,csr=0,rc=0;
 if(wd_phase!=1)return;
 if(!owned_owner()||!wd_buffer||wd_sequence!=batch.sequence||!wd_idle()){rc=1;goto failed;}
 WD_STAGE(1);
 wd_desc[0]=0;wd_desc[1]=wd_host;wd_desc[2]=0;wd_desc[3]=WD_ADDR(wd_buffer+4096);wd_desc[4]=4096;wd_desc[5]=6;wd_desc[6]=wd_desc[7]=0xfacefeed;
 wd_report[10]=WD_ADDR(wd_desc);
 WD_STAGE(4);WD_S(0x1204)=6;if(WD_S(0x1204)!=6){rc=2;goto cleanup;}
 WD_STAGE(5);WD_R(0x1450)=WD_ADDR(wd_desc);(void)WD_R(0x1450);WD_STAGE(6);WD_R(0x1440)=1;(void)WD_R(0x1440);WD_STAGE(7);
 for(i=0;i<200000;i++){csr=WD_R(0x1444);if(csr&~0x400u){rc=3;break;}if(!csr&&!WD_R(0x1450)&&WD_R(0x144c)==WD_ADDR(wd_desc)&&!WD_R(0x1460))break;}
 WD_STAGE(8);if(i==200000)rc=4;
 wd_report[4]=csr;wd_report[5]=WD_R(0x144c);wd_report[6]=WD_R(0x1450);wd_report[7]=WD_R(0x1460);wd_report[8]=WD_R(0x1464);wd_report[9]=i;
cleanup:
 WD_STAGE(9);WD_R(0x1440)=0;(void)WD_R(0x1440);WD_STAGE(10);WD_S(0x1204)=2;(void)WD_S(0x1204);WD_STAGE(11);
 if(rc)goto failed;
 if(!wd_idle()||WD_R(0x1450)||wd_desc[6]!=0xfacefeed||wd_desc[7]!=0xfacefeed){rc=5;goto failed;}
 for(i=0;i<4096;i++)if(wd_buffer[i]!=0xa5||wd_buffer[8192+i]!=0xa5){rc=6;goto failed;}
 __asm__ volatile("":::"memory");wd_phase=2;return;
failed:wd_report[11]=rc;exclusive_abort();for(;;){}
}

/* Caller masks interrupts: a late submit must never escape lease teardown. */
static void wd_release(void){if(wd_phase==1||wd_phase==2){exclusive_abort();for(;;){}}wd_buffer=0;wd_phase=0;}

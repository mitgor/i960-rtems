/* Opt-in single-descriptor DMA1 proof. Intel 272736-002 sections 4.4.4,
 * 20.3.1/2 and tables 20-3/4/11/12. No firmware return or active abort. */
#ifndef DMA_R
#define DMA_R(a) (*(volatile unsigned int *)(a))
#define DMA_S(a) (*(volatile unsigned short *)(a))
#define DMA_ADDR(p) ((unsigned int)(p))
#define DMA_FENCE() __asm__ volatile("":::"memory")
#define DMA_JOB_R(a) hw[((a)-0x1400)/4]
#endif
#define DMA_PHASE(r) (*(volatile unsigned int*)((r)+31))
static unsigned int dma_args[4],dma_report[32]={0x31414d44,0,0,0,0,0,0,0,0,0,0,2};

static volatile unsigned char dma_source[65536+128] __attribute__((aligned(16)));
static volatile unsigned int dma_desc_storage[16] __attribute__((aligned(16)));
#define dma_desc ((volatile unsigned int*)(((unsigned long)dma_desc_storage+31)&~31UL))
static unsigned int __attribute__((noinline)) dma_isolated(void){unsigned int i;
 static const unsigned int addresses[6]={0x1400,0x1404,0x1440,0x1444,0x1480,0x1484};
 for(i=0;i<6;i++)if(DMA_R(addresses[i]))return 0;
 return DMA_S(0x1204)==2&&DMA_S(0x1298)==0&&DMA_R(0x104c)==0x13ffc;
}
static unsigned int __attribute__((noinline)) dma_pattern(unsigned int n,unsigned int seed,unsigned int fill){unsigned int i,j,v;
 for(i=0;i<sizeof(dma_source);i++){j=i-64;v=j<n?((j*13u^seed^(j>>8))&255):0xa5;
  if(fill)dma_source[i]=v;else if(dma_source[i]!=v)return 0;
 }return 1;
}
static unsigned int __attribute__((noinline)) dma_control_impl(unsigned int op,unsigned int index,unsigned int value,unsigned int running,unsigned int*report,unsigned int*args){
 if(op==0x52)return index<32?report[index]:~0u;
 if(!running||report[15])return 1;
 if(DMA_PHASE(report)==1)return 10;
 if(op==0x50){if(index>=4)return 2;args[index]=value;return 0;}
 if(index||value)return 2;
 report[14]=0;DMA_PHASE(report)=1;
 DMA_FENCE();return 0;
}
/* Only worker 1 calls this with interrupts enabled. No other context writes
 * descriptors/source/report until completion. Pending rejects all argument edits. */
static void __attribute__((noinline)) dma_step_impl(unsigned int *report,unsigned int *args,volatile unsigned int *hw){
 unsigned int n,base,seq,csr=0,rc=0,loops=0;
 if(DMA_PHASE(report)!=1)return;
 base=args[0];n=args[1];seq=args[3];
 if(!base||base>0xffffffffu-65536u||n-1>=65536||!seq||seq!=report[1]+1){rc=3;goto failed;}
 /* This profile owns the CPU and keeps DMA0/2 and the secondary bus disabled. */
 if(!dma_isolated()){rc=4;goto failed;}
 report[1]=seq;report[2]=base;report[3]=n;report[4]=args[2];
 dma_pattern(n,args[2],1);
 dma_desc[0]=0;dma_desc[1]=base;dma_desc[2]=0;dma_desc[3]=DMA_ADDR(dma_source+64);dma_desc[4]=n;dma_desc[5]=7;dma_desc[6]=0xfacefeed;dma_desc[7]=0xfacefeed;
 DMA_FENCE();
 if(DMA_STOP()){rc=10;goto cleanup;}
 /* Pending excludes mutation; report sequence forbids replay. */
 DMA_S(0x1204)=6;if(DMA_S(0x1204)!=6){rc=5;goto cleanup;}
 DMA_JOB_R(0x1450)=DMA_ADDR(dma_desc);(void)DMA_JOB_R(0x1450);
 DMA_JOB_R(0x1440)=1;(void)DMA_JOB_R(0x1440);
 for(loops=0;loops<200000;loops++){
  csr=DMA_JOB_R(0x1444);
  if(csr&~0x400u){rc=6;break;}
  if(!csr&&DMA_JOB_R(0x1450)==0&&DMA_JOB_R(0x144c)==DMA_ADDR(dma_desc)&&DMA_JOB_R(0x1460)==0)break;
 }
 if(loops==200000)rc=7;
 report[5]=csr;report[6]=loops;report[7]=DMA_JOB_R(0x144c);report[8]=DMA_JOB_R(0x1450);report[9]=DMA_JOB_R(0x1460);report[10]=DMA_JOB_R(0x1464);
cleanup:
 DMA_JOB_R(0x1440)=0;(void)DMA_JOB_R(0x1440);DMA_S(0x1204)=2;(void)DMA_S(0x1204);
 if(rc)goto failed;
 if(!dma_isolated()||DMA_JOB_R(0x1450))rc=8;
 if(!dma_pattern(n,args[2],0))rc=9;
 if(dma_desc[6]!=0xfacefeed||dma_desc[7]!=0xfacefeed)rc=9;
 if(rc)goto failed;
 report[14]=1;goto finished; /* isolated readbacks checked above */
failed:
 /* Suspension is not abort/drain. Deny further submissions, retain all memory.
  * Never publish success or recycle buffers even if clearing controls succeeds. */
 report[15]=rc;
finished:
 DMA_FENCE();DMA_PHASE(report)=2;
}

#define dma_step() dma_step_impl(dma_report,dma_args,(volatile unsigned int*)0x1400)

#define dma_control(op,index,value,running) dma_control_impl(op,index,value,running,dma_report,dma_args)

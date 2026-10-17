#include <rtems/system.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/score/context.h>
#include <rtems/score/thread.h>
#include <stddef.h>

extern unsigned char _bss_start[],_bss_end[];
extern void bounded_escape(unsigned int code) __attribute__((noreturn));
extern void lease_invalidate_dcache(void);
static unsigned char workspace[32768] __attribute__((aligned(16)));
static volatile unsigned int done,stop_seen,polls,worker_sp,result;
static rtems_id worker_id;
static volatile unsigned int * const control=(volatile unsigned int *)0xc000fa40u;
static volatile unsigned int * const exclusive=(volatile unsigned int *)0xc000fa80u;
static volatile unsigned int * const census=(volatile unsigned int *)0xc000fb00u;
static volatile unsigned char * const bitmap=(volatile unsigned char *)0xc0731000u;
#define UPPER_PAGE 0xc0f01000u
#define BANK_BASE 0xc0800000u
#define BANK_PAGES 2048u

/* This call runs at interrupt priority 31 on the grant-owned entry stack.
 * Stock's command path cannot execute concurrently on the same core. Check
 * all three 80303 DMA channels without reading CSR's read-clear bits. */
static unsigned int dma_busy_mask(void){
 unsigned int ch,busy=0;
 for(ch=0;ch<3u;ch++){
  volatile unsigned int *r=(volatile unsigned int *)(0x00001400u+ch*0x40u);
  if(r[0]!=0u||r[4]!=0u||r[8]!=0u)busy|=1u<<ch;
 }
 return busy;
}
static unsigned int page_fnv(volatile unsigned char *p){
 unsigned int i,h=0x811c9dc5u;
 for(i=0;i<4096u;i++)h=(h^p[i])*0x01000193u;
 return h;
}
/* Read every word of the upper 8 MiB without changing that bank. The 256
 * useful bitmap bytes live in an odd page of the existing 512 KiB grant. */
static unsigned int survey_bank(void){
 unsigned int page,word,h=0x811c9dc5u,bh=0x811c9dc5u;
 unsigned int cache,scratch,after,busy,value,any,first=0xffffffffu,last=0;
 volatile unsigned int *p;
 for(word=0;word<16u;word++)census[word]=0u;
 for(word=0;word<4096u;word++)bitmap[word]=0u;
 census[0]=0x31534e43u;census[1]=BANK_PAGES;
 census[4]=first;census[9]=busy=dma_busy_mask();
 if(busy){census[14]=1u;return 1u;}
 __asm__ volatile("flushreg":::"memory");
 __asm__ volatile("dcctl 4,0,%0":"=r"(cache)::"memory");
 census[12]=cache;
 __asm__ volatile("dcctl 0,0,%0":"=r"(scratch)::"memory");
 for(page=0;page<BANK_PAGES;page++){
  p=(volatile unsigned int *)(BANK_BASE+page*4096u);
  any=0u;
  for(word=0;word<1024u;word++){
   value=p[word];h=(h^value)*0x01000193u;
   if(value){
    census[3]++;any=1u;
    if(first==0xffffffffu)first=BANK_BASE+page*4096u+word*4u;
    last=BANK_BASE+page*4096u+word*4u;
   }
  }
  if(any){
   bitmap[page/8u]|=(unsigned char)(1u<<(page%8u));
   census[2]++;
   if(page&1u)census[8]++;else census[7]++;
  }
 }
 census[4]=first;census[5]=last;census[6]=h;
 for(word=0;word<256u;word++)bh=(bh^bitmap[word])*0x01000193u;
 census[11]=bh;
 __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
 if(cache&1u)__asm__ volatile("dcctl 1,0,%0":"=r"(scratch)::"memory");
 __asm__ volatile("dcctl 4,0,%0":"=r"(after)::"memory");
 census[13]=after;
 census[10]=dma_busy_mask();
 census[14]=((after&1u)!=(cache&1u)||census[10])?2u:0u;
 return census[14];
}
static unsigned int exclusive_page_probe(void){
 volatile unsigned char *page=(volatile unsigned char *)UPPER_PAGE;
 volatile unsigned int *words=(volatile unsigned int *)(UPPER_PAGE+0x80u);
 const unsigned int pattern[4]={0x314c4358u,0x95a53c69u,0x6a5ac396u,0x58434c31u};
 unsigned int old[4],i,before,after,busy;
 exclusive[0]=0x314c4358u;exclusive[1]=UPPER_PAGE;
 busy=dma_busy_mask();exclusive[2]=busy;
 if(busy){exclusive[6]=1u;return 0xbad10001u;}
 before=page_fnv(page);exclusive[3]=before;
 for(i=0;i<4096u;i++)if(page[i]!=0u){exclusive[6]=2u;return 0xbad10002u;}
 for(i=0;i<4u;i++)old[i]=words[i];
 for(i=0;i<4u;i++)words[i]=pattern[i];
 for(i=0;i<4u;i++)if(words[i]!=pattern[i])break;
 exclusive[4]=i;
 /* Restore even after a failed pattern readback; never leave test bytes. */
 for(i=0;i<4u;i++)words[i]=old[i];
 after=page_fnv(page);exclusive[5]=after;
 busy=dma_busy_mask();exclusive[7]=busy;
 if(exclusive[4]!=4u||after!=before||busy){
  exclusive[6]=3u;return 0xbad10003u;
 }
 exclusive[6]=0u;
 return 0u;
}

void bounded_fatal(unsigned int code){bounded_escape(0xf0000000u|code);}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000u+__LINE__*256u+e);}while(0)
#define ASSERT(x) do {if(!(x))bounded_fatal(0x20000u+__LINE__);}while(0)
typedef char context_pc_offset[(offsetof(Context_Control,pc)==8)?1:-1];
typedef char context_g8_offset[(offsetof(Context_Control,g8)==12)?1:-1];

static void Worker(rtems_task_argument nonce){
 unsigned int i,sp;
 __asm__ volatile("mov sp,%0":"=r"(sp));
 worker_sp=sp;
 control[4]=0x59444152u; /* READY */
 for(i=0;i<2000000u;i++){
  lease_invalidate_dcache();
  if(control[3]==0x504f5453u){
   ASSERT(control[0]==0x3145534cu&&control[1]==nonce&&control[2]==1u);
   control[5]=0x214b4341u; /* ACK */
   control[6]=nonce;
   control[7]=1u;
   stop_seen=1u;
   break;
  }
  if((i&4095u)==0)CHECK(rtems_task_wake_after(0));
 }
 polls=i;
 if(!stop_seen)control[4]=0x454d4954u; /* TIME */
 done=1u;
 CHECK(rtems_task_delete(RTEMS_SELF));
 bounded_fatal(0x30001u);
}

static void Init(rtems_task_argument nonce){
 rtems_task_priority old;
 (void)nonce;
 CHECK(rtems_task_create(0x574f524bu,2,4096,
       RTEMS_INTERRUPT_LEVEL(31),RTEMS_DEFAULT_ATTRIBUTES,&worker_id));
 CHECK(rtems_task_start(worker_id,Worker,0x161610d1u));
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));
 while(!done)CHECK(rtems_task_wake_after(0));
 result=stop_seen?0x504f5453u:0x454d4954u;
 rtems_shutdown_executive(0);
}

static rtems_initialization_tasks_table tasks[]={{0x494e4954,4096,1,
 RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={3,0,2,0,0,0,0,0,1,tasks};
static rtems_configuration_table config={workspace,sizeof(workspace),0,
 10000,1,0,0,0,0,0,0,0,&api,0,0};
static rtems_cpu_table cpu={0,0,0,0,1,2048,2048,0,0,0};
void _ISR_Handler(void){bounded_fatal(0x40000u);}
void _CPU_ISR_install_raw_handler(unsigned int v,proc_ptr n,proc_ptr*o){
 bounded_fatal(0x40000u|v);
}

unsigned int bounded_main(unsigned int report_addr,unsigned int nonce){
 volatile unsigned int *report=(volatile unsigned int *)report_addr;
 unsigned char *p;
 if(report_addr!=0xc000fa20u||nonce!=0x161610d1u)return 0xbad00001u;
 for(p=_bss_start;p<_bss_end;p++)*p=0;
 if(control[0]!=0x3145534cu||control[1]!=nonce||
    control[2]!=1u||control[3]!=0)return 0xbad00002u;
 if(survey_bank()!=0u)return 0xbad20001u;
 if(exclusive_page_probe()!=0u)return 0xbad10004u;
 rtems_initialize_executive(&config,&cpu);
 if(done!=1u||result!=(stop_seen?0x504f5453u:0x454d4954u))
  return 0xbad00003u;
 report[0]=0x314e5552u; /* RUN1 */
 report[1]=nonce;
 report[2]=0x31454e4fu; /* ONE1 */
 report[6]=result;
 ((volatile unsigned int *)0xc000fa70u)[0]=worker_sp;
 ((volatile unsigned int *)0xc000fa70u)[1]=polls;
 ((volatile unsigned int *)0xc000fa70u)[2]=stop_seen;
 ((volatile unsigned int *)0xc000fa70u)[3]=done;
 return 0;
}

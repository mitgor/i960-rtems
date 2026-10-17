/* AcceleRAID 160: bounded upper-bank address-distinctness and pattern proof. */
#include <rtems/system.h>
#include <rtems/rtems/tasks.h>
#include <rtems/rtems/clock.h>
#include <rtems/config.h>
#include <rtems/init.h>
#include <rtems/score/context.h>
#include <rtems/score/thread.h>
#include <rtems/score/isr.h>
#include <stddef.h>
#include "lifetime.h"
#include "arena.h"
#include "sha256.h"
#include "engine_identity.h"
extern unsigned char _bss_start[],_bss_end[],switch_irq_areas[3][8192];
extern void bounded_escape(unsigned int) __attribute__((noreturn));
extern void lease_invalidate_dcache(void),timer_isr(void);
void bounded_fatal(unsigned int code) __attribute__((noreturn));
#define REG(a) (*(volatile unsigned int *)(a))
#define STOP 0x504f5453u
#define TIME 0x454d4954u
static unsigned char workspace[40960] __attribute__((aligned(16)));
static volatile unsigned int done[2],stop_seen,deadline,loops[2],result;
static volatile unsigned int ticks,irq_sp[3],handoffs,two_live;
volatile unsigned int switch_threads[3],switch_active[3],switch_fault,switch_stop;
static struct irq_lifetime life[3];
static unsigned int saved_mask,saved_map,saved_vector,saved_reload,saved_count;
static volatile unsigned int armed,restoration;
static rtems_id worker_id[2];
static volatile unsigned int * const control=(volatile unsigned int *)0xc000fa40u;
static volatile unsigned int * const xreport=(volatile unsigned int *)0xc000fa80u;
static volatile unsigned int * const bank_report=(volatile unsigned int *)0xc000fb00u;
#define UPPER_PAGE 0xc0f01000u
#define STOCK_PAGE 0xc0011000u
#define BANK_BASE 0xc0800000u
#define BANK_PAGES 2048u
#define BANK_END 0xc1000000u
#define ARENA_BASE 0xc0810000u
#define ARENA_END 0xc0ff0000u
static unsigned int upper_old[4],stock_old[4];
static unsigned int upper_hash,stock_hash,page_armed;
static volatile unsigned int claimed;
static volatile unsigned int * const claim_report=(volatile unsigned int *)0xc000fb40u;
static volatile unsigned int * const bridge=(volatile unsigned int *)0xc000fb80u;
static volatile unsigned int * const wad_wire=(volatile unsigned int *)0xc000fc00u;
static volatile unsigned char * const inbound=(volatile unsigned char *)0xc078b000u;
static volatile unsigned char * const outbound=(volatile unsigned char *)0xc078d000u;
static struct arena doom_arena;
static unsigned int image_handle,zone_handle,frame_handle,wad_handle;
static unsigned char *image_base,*zone_base,*frame_base,*wad_buffer;
static unsigned int upload_bytes,admitted,wad_ready,frame_ready,last_seq;
static unsigned int wad_seq,wad_good,wad_bad;
#define ENGINE_ADMISSION (ENGINE_META+ENGINE_SITES*4u)
#define ENGINE_RESERVE 900000u
#define ZONE_BYTES 6291456u
#define FRAME_BYTES 65536u
#define WAD_BUFFER_BYTES 4096u
#define WAD_FILE_BYTES 28795076u
#define BRIDGE_EPOCH 0x161610e1u
typedef char context_pc_offset[(offsetof(Context_Control,pc)==8)?1:-1];
typedef char context_g8_offset[(offsetof(Context_Control,g8)==12)?1:-1];
static void mask31(void){unsigned int level=31u<<16;
 __asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(level)::"g0","memory");
}
static void priority0(void){unsigned int level=0u;
 __asm__ volatile("lda 0x1f0000,g0; modpc 0,g0,%0":"+r"(level)::"g0","memory");
}
static void clear_tip1(void){unsigned int old=0;
 __asm__ volatile("lda 0xff008500,g0; lda 0x2000,g1; atmod g0,g1,%0"
                  :"+r"(old)::"g0","g1","memory");
}
static unsigned int preflight(void){
 REG(0xc000fa70u)=REG(0xff008500u);
 REG(0xc000fa74u)=REG(0xff008504u);
 REG(0xc000fa78u)=REG(0xff008528u);
 if(REG(0xff008510u)!=0x6000u)return 1u;
 if(REG(0xff008520u)!=0x4444u)return 2u;
 if(REG(0xff008524u)!=0x6754u)return 3u;
 if(REG(0xff008528u)!=0x80000u)return 4u;
 if(REG(0xff008504u)!=0x10c7u)return 5u;
 /* Stock timer 0 can be pending while RTEMS starts at priority 31. Only
  * timer 1 (our borrowed source) must be clear. Preserve other pending bits. */
 if(REG(0xff008500u)&0x2000u)return 6u;
 if(REG(0xff000310u)!=0u)return 7u;
 if(REG(0xff000314u)!=0u)return 8u;
 if(REG(0x4u)!=0xaaaaaaaau)return 9u;
 if(REG(0x20u)!=0xc0000418u)return 10u;
 if(REG(0x3cu)!=0xe0000ff0u)return 11u;
 if(REG(0xff000318u)!=0u)return 12u;
 if(REG(0xff000310u)!=0u)return 13u;
 if(REG(0xff000314u)!=0u)return 14u;
 if(REG(0xff008500u)&0x2000u)return 15u;
 if(REG(0xff008504u)!=0x10c7u)return 16u;
 if(REG(0xff008528u)!=0x80000u)return 17u;
 if(REG(0x4u)!=0xaaaaaaaau)return 18u;
 return 0u;
}
static void stop_timer(void){
 if(!armed)return;
 mask31();
 REG(0xff008504u)=0u;
 REG(0xff000318u)=0u;
 clear_tip1();
 REG(0xff008528u)=saved_map;
 REG(0x4u)=saved_vector;
 REG(0xff000310u)=saved_reload;
 REG(0xff000314u)=saved_count;
 REG(0xff008504u)=saved_mask;
 armed=0u;
 restoration=(REG(0xff008504u)==saved_mask &&
              REG(0xff008528u)==saved_map && REG(0x4u)==saved_vector &&
              REG(0xff000310u)==saved_reload &&
              REG(0xff000314u)==saved_count &&
              !(REG(0xff008500u)&0x2000u) &&
              REG(0xff000318u)==0u && !switch_active[0] && !switch_active[1] && !switch_active[2] && !switch_fault);
}
/* Only CCR, NDAR and BCR: CSR has read-clear status. */
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
/* Word hashes avoid an eight-million-byte multiply loop. The lower hash
 * excludes our grant and the host control page, which this image changes. */
static unsigned int lower_hash(void){
 unsigned int addr,j,h=0x811c9dc5u;
 for(addr=0xc0000000u;addr<0xc0800000u;addr+=4096u){
  volatile unsigned int *p;
  if(addr==0xc000f000u||(addr>=0xc0710000u&&addr<0xc0790000u))continue;
  p=(volatile unsigned int *)addr;
  for(j=0;j<1024u;j++)h=(h^p[j])*0x01000193u;
 }
 return h;
}
static unsigned int static_code_hash(void){
 volatile unsigned int *p=(volatile unsigned int *)0xc0710000u;
 unsigned int i,h=0x811c9dc5u;
 for(i=0;i<((unsigned int)_bss_start-0xc0710000u)/4u;i++)
  h=(h^p[i])*0x01000193u;
 return h;
}
static unsigned int bank_word_hash(void){
 volatile unsigned int *p=(volatile unsigned int *)BANK_BASE;
 unsigned int i,h=0x811c9dc5u;
 for(i=0;i<(BANK_END-BANK_BASE)/4u;i++)h=(h^p[i])*0x01000193u;
 return h;
}
static unsigned int marker(unsigned int index){
 return 0x5a960000u^(index*0x9e3779b9u);
}
static unsigned int pattern(unsigned int page,unsigned int word){
 return 0x7e960160u^(page*0x85ebca6bu)^(word*0xc2b2ae35u);
}
/* A reset leaves arbitrary prior RTEMS bytes in DRAM. Save one word per page
 * for simultaneous markers, then save/restore each whole page in turn using
 * scratch inside the owned grant. A failed restore quarantines the callback. */
#define MARK_SAVE 0xc0740000u
#define PAGE_SAVE 0xc0742000u
static unsigned int bank_probe(void){
 unsigned int page,word,marked=0,lower_before,lower_during,lower_after;
 unsigned int code_before,code_after,bank_before,bank_after,error=0,busy;
 unsigned int cache=0,scratch=0,now=0,cache_disabled=0,touched=0;
 volatile unsigned int *p,*saved;
 for(word=0;word<16u;word++)bank_report[word]=0u;
 bank_report[0]=0x314b4e42u;bank_report[1]=0xffffffffu;
 bank_report[3]=BANK_END-BANK_BASE;
 busy=dma_busy_mask();bank_report[12]=busy;
 if(busy){error=1u;goto finish;}
 __asm__ volatile("flushreg":::"memory");
 __asm__ volatile("dcctl 4,0,%0":"=r"(cache)::"memory");
 __asm__ volatile("dcctl 0,0,%0":"=r"(scratch)::"memory");
 cache_disabled=1u;
 bank_before=bank_word_hash();
 for(page=0;page<BANK_PAGES;page++){
  p=(volatile unsigned int *)(BANK_BASE+page*4096u);
  REG(MARK_SAVE+page*4u)=p[0x80u/4u];
 }
 bank_report[2]=BANK_PAGES; /* all marker preimages saved */
 if(bank_word_hash()!=bank_before){error=5u;goto finish;}
 lower_before=lower_hash();
 code_before=static_code_hash();
 bank_report[4]=lower_before;bank_report[14]=code_before;
 for(page=0;page<BANK_PAGES;page++){
  p=(volatile unsigned int *)(BANK_BASE+page*4096u);
  touched=1u;
  p[0x80u/4u]=marker(page);
  marked=page+1u;
  if(p[0x80u/4u]!=marker(page)){
   bank_report[8]++;error=6u;goto clear_markers;
  }
 }
 for(page=0;page<BANK_PAGES;page++){
  p=(volatile unsigned int *)(BANK_BASE+page*4096u);
  if(p[0x80u/4u]!=marker(page)){
   bank_report[8]++;error=7u;goto clear_markers;
  }
 }
 lower_during=lower_hash();bank_report[5]=lower_during;
 if(lower_during!=lower_before){error=8u;goto clear_markers;}
 if(static_code_hash()!=code_before){error=9u;goto clear_markers;}
clear_markers:
 while(marked){
  marked--;
  p=(volatile unsigned int *)(BANK_BASE+marked*4096u);
  p[0x80u/4u]=REG(MARK_SAVE+marked*4u);
 }
 lower_after=lower_hash();bank_report[6]=lower_after;
 if(lower_after!=lower_before&&!error)error=10u;
 if(bank_word_hash()!=bank_before){claimed=1u;if(!error)error=11u;}
 if(error)goto finish;
 bank_report[7]=BANK_PAGES;
 saved=(volatile unsigned int *)PAGE_SAVE;
 for(page=0;page<BANK_PAGES;page++){
  p=(volatile unsigned int *)(BANK_BASE+page*4096u);
  for(word=0;word<1024u;word++)saved[word]=p[word];
  for(word=0;word<1024u;word++)if(saved[word]!=p[word]){
   error=19u;goto finish;
  }
  for(word=0;word<1024u;word++)p[word]=pattern(page,word);
  for(word=0;word<1024u;word++)if(p[word]!=pattern(page,word)){
   bank_report[10]++;error=12u;break;
  }
  for(word=0;word<1024u;word++)p[word]=saved[word];
  for(word=0;word<1024u;word++)if(p[word]!=saved[word]){
   bank_report[10]++;if(!error)error=13u;break;
  }
  if(error)goto finish;
  bank_report[9]=page+1u;
 }
 bank_after=bank_word_hash();bank_report[11]=bank_after;
 if(bank_after!=bank_before){claimed=1u;error=14u;}
 if(lower_hash()!=lower_before&&!error)error=15u;
 code_after=static_code_hash();bank_report[15]=code_after;
 if(code_after!=code_before&&!error)error=16u;
finish:
 if(touched&&bank_word_hash()!=bank_before){claimed=1u;if(!error)error=20u;}
 bank_report[13]=dma_busy_mask();
 if(bank_report[13]&&!error)error=17u;
 if(cache_disabled){
  __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
  if(cache&1u)__asm__ volatile("dcctl 1,0,%0":"=r"(scratch)::"memory");
  __asm__ volatile("dcctl 4,0,%0":"=r"(now)::"memory");
  if((now&1u)!=(cache&1u)&&!error)error=18u;
 }
 bank_report[1]=error;
 return error;
}
static unsigned int exclusive_enter(void){
 volatile unsigned char *upper=(volatile unsigned char *)UPPER_PAGE;
 volatile unsigned int *uw=(volatile unsigned int *)(UPPER_PAGE+0x80u);
 volatile unsigned int *sw=(volatile unsigned int *)(STOCK_PAGE+0x80u);
 const unsigned int upat[4]={0x314d5458u,0x89abcdefu,0x13579bdfu,0x554d5458u};
 const unsigned int spat[4]={0x324d5458u,0xfedcba98u,0x2468ace0u,0x554d5458u};
 unsigned int i,busy=dma_busy_mask();
 xreport[0]=0x314d5458u;xreport[1]=busy;xreport[7]=0xffffffffu;
 if(busy)return 1u;
 for(i=0;i<4096u;i++)if(upper[i]!=0u)return 2u;
 upper_hash=page_fnv(upper);
 stock_hash=page_fnv((volatile unsigned char *)STOCK_PAGE);
 if(stock_hash==upper_hash)return 3u;
 for(i=0;i<4u;i++){upper_old[i]=uw[i];stock_old[i]=sw[i];}
 xreport[2]=upper_hash;xreport[3]=stock_hash;
 page_armed=1u;
 for(i=0;i<4u;i++){uw[i]=upat[i];sw[i]=spat[i];}
 for(i=0;i<4u;i++)if(uw[i]!=upat[i]||sw[i]!=spat[i])return 4u;
 return 0u;
}
static unsigned int exclusive_leave(void){
 volatile unsigned int *uw=(volatile unsigned int *)(UPPER_PAGE+0x80u);
 volatile unsigned int *sw=(volatile unsigned int *)(STOCK_PAGE+0x80u);
 unsigned int i,busy,good;
 if(!page_armed)return 0u;
 for(i=0;i<4u;i++){uw[i]=upper_old[i];sw[i]=stock_old[i];}
 page_armed=0u;
 xreport[4]=page_fnv((volatile unsigned char *)UPPER_PAGE);
 xreport[5]=page_fnv((volatile unsigned char *)STOCK_PAGE);
 busy=dma_busy_mask();xreport[6]=busy;
 good=(xreport[4]==upper_hash&&xreport[5]==stock_hash&&busy==0u);
 xreport[7]=good?0u:5u;
 return good?0u:5u;
}
static unsigned int byte_fnv(volatile const unsigned char *p,unsigned int n){
 unsigned int h=0x811c9dc5u,i;
 for(i=0;i<n;i++)h=(h^p[i])*0x01000193u;
 return h;
}
static unsigned int little_word(const unsigned char *p){
 return (unsigned int)p[0]|((unsigned int)p[1]<<8)|
        ((unsigned int)p[2]<<16)|((unsigned int)p[3]<<24);
}
static void put_word(unsigned char *p,unsigned int value){unsigned int i;
 for(i=0;i<4u;i++)p[i]=(unsigned char)(value>>(8u*i));
}
static unsigned int digest_equal(const unsigned char *p,unsigned int n,
                                 const unsigned char expected[32]){
 struct sha256 hash;unsigned char out[32];unsigned int i;
 sha256_init(&hash);
 if(!sha256_update(&hash,p,n))return 0u;
 sha256_finish(&hash,out);
 for(i=0;i<32u;i++)if(out[i]!=expected[i])return 0u;
 return 1u;
}
static unsigned int admit_engine(void){
 unsigned int i,x,last=0,base=(unsigned int)image_base;
 if(upload_bytes!=ENGINE_ADMISSION||admitted)return 1u;
 if(!arena_valid(&doom_arena))return 2u;
 if(!digest_equal(image_base,ENGINE_FILE,engine_image_sha)||
    !digest_equal(image_base+ENGINE_META,ENGINE_SITES*4u,engine_metadata_sha)||
    !digest_equal(image_base,ENGINE_TEXT,engine_text_sha))return 3u;
 for(i=ENGINE_FILE;i<ENGINE_META;i++)if(image_base[i])return 4u;
 for(i=0;i<ENGINE_SITES;i++){
  x=little_word(image_base+ENGINE_META+i*4u);
  if((x&3u)||x>ENGINE_FILE-4u||(i&&x<=last)||
     little_word(image_base+x)>ENGINE_SPAN)return 5u;
  last=x;
 }
 for(i=0;i<ENGINE_SITES;i++){
  x=little_word(image_base+ENGINE_META+i*4u);
  put_word(image_base+x,little_word(image_base+x)+base);
 }
 __asm__ volatile("icctl 2,0,%0":"=r"(x)::"memory");
 admitted=1u;
 bridge[14]=ENGINE_ENTRY+base;
 bridge[15]=ENGINE_ADMISSION;
 return 0u;
}
static void render_diagnostic(void){unsigned int x,y,i;
 for(y=0;y<200u;y++)for(x=0;x<320u;x++)
  frame_base[y*320u+x]=(unsigned char)(((x>>3)^(y>>3)^zone_base[(x+y)&511u])&255u);
 for(i=64000u;i<FRAME_BYTES;i++)frame_base[i]=0u;
 frame_ready=1u;
 bridge[16]=byte_fnv(frame_base,FRAME_BYTES);
}
/* This is the read callback's transport core. The card owns request order and
 * destination; the host may only answer the exact sequence, file range and
 * size. A bad/stale reply never changes the destination. A 500-tick stall is
 * finite, and STOP is observed while the callback is waiting. */
static unsigned int wad_fetch(unsigned int offset,unsigned int n,unsigned int *value){
 unsigned int seq,start,reply,i,checksum;
 *value=0u;
 if(!wad_ready||!n||n>WAD_BUFFER_BYTES||offset>WAD_FILE_BYTES||
    n>WAD_FILE_BYTES-offset)return 10u;
 seq=++wad_seq;
 wad_wire[4]=0u;wad_wire[5]=0u;wad_wire[6]=0u;
 wad_wire[7]=0u;wad_wire[8]=0u;
 wad_wire[1]=offset;wad_wire[2]=n;wad_wire[3]=1u;
 wad_wire[9]=0x444e4550u; /* PEND */
 wad_wire[10]=0u;wad_wire[11]=0u;wad_wire[12]=BRIDGE_EPOCH;
 wad_wire[0]=seq; /* request publish last */
 start=ticks;
 while(ticks-start<500u){
  lease_invalidate_dcache();
  if(control[3]==STOP){wad_wire[9]=15u;wad_bad++;return 15u;}
  reply=wad_wire[4];
  if(reply){
   if(reply!=seq){wad_wire[9]=11u;wad_bad++;return 11u;}
   if(wad_wire[5]!=offset||wad_wire[6]!=n||wad_wire[8]!=0u||
      byte_fnv(inbound,n)!=wad_wire[7]){
    wad_wire[9]=12u;wad_bad++;return 12u;
   }
   checksum=wad_wire[7];
   for(i=0;i<n;i++)wad_buffer[i]=inbound[i];
   if(byte_fnv(wad_buffer,n)!=checksum){
    wad_wire[9]=13u;wad_bad++;return 13u;
   }
   wad_wire[10]=checksum;wad_wire[11]=n;wad_wire[9]=0u;
   wad_good++;*value=checksum;return 0u;
  }
  if(rtems_task_wake_after(1)!=RTEMS_SUCCESSFUL){
   wad_wire[9]=14u;wad_bad++;return 14u;
  }
  priority0();
 }
 wad_wire[9]=16u;wad_bad++;return 16u;
}
/* PCI sideband never submits a stock mailbox command. The host writes a 4 KiB
 * odd-page stage, then publishes seq last. Only this task copies application
 * bytes; the ISR handles timer/context only. ACK is written last. */
static void bridge_poll(void){
 unsigned int seq=bridge[0],op,offset,n,expected,epoch,status=0,value=0,i;
 if(!seq||seq==last_seq)return;
 op=bridge[1];offset=bridge[2];n=bridge[3];expected=bridge[4];epoch=bridge[5];
 if(seq!=last_seq+1u||epoch!=BRIDGE_EPOCH){status=1u;goto reply;}
 if(op==1u){
  if(admitted||offset!=upload_bytes||n==0u||n>4096u||
     offset>ENGINE_ADMISSION||n>ENGINE_ADMISSION-offset){status=2u;goto reply;}
  if(byte_fnv(inbound,n)!=expected){status=3u;goto reply;}
  for(i=0;i<n;i++)image_base[offset+i]=inbound[i];
  if(byte_fnv(image_base+offset,n)!=expected){status=4u;goto reply;}
  upload_bytes+=n;value=upload_bytes;
 }else if(op==2u){
  static const unsigned char wad_sha[32]={0x93,0xbd,0x1d,0xdc,0xfc,0x43,0xfb,0xf2,
   0x33,0x20,0x78,0x76,0xf5,0xcf,0xcb,0xae,0xf4,0xcf,0x4e,0x64,0xa1,0x09,
   0x3e,0xfa,0x47,0xbe,0x95,0x17,0xd9,0x32,0x14,0xbd};
  unsigned char sample[512];
  if(!admitted||wad_ready||offset!=0u||n!=512u){status=5u;goto reply;}
  if(byte_fnv(inbound,n)!=expected){status=6u;goto reply;}
  for(i=0;i<n;i++)sample[i]=inbound[i];
  if(!digest_equal(sample,n,wad_sha)||
     sample[0]!='I'||sample[1]!='W'||sample[2]!='A'||sample[3]!='D'){
   status=7u;goto reply;
  }
  for(i=0;i<n;i++)zone_base[i]=sample[i];
  wad_ready=1u;value=little_word(zone_base+4);
  render_diagnostic();
 }else if(op==3u){
  if(!frame_ready||offset>=16u||n!=4096u){status=8u;goto reply;}
  for(i=0;i<4096u;i++)outbound[i]=frame_base[offset*4096u+i];
  value=byte_fnv(outbound,4096u);
 }else if(op==4u){
  status=admit_engine();value=admitted;
 }else if(op==5u){
  status=wad_fetch(offset,n,&value);
 }else if(op==6u){
  if(!wad_ready||offset||n!=WAD_BUFFER_BYTES){status=17u;goto reply;}
  for(i=0;i<WAD_BUFFER_BYTES;i++)outbound[i]=wad_buffer[i];
  value=byte_fnv(outbound,WAD_BUFFER_BYTES);
 }else{status=9u;}
reply:
 bridge[9]=status;bridge[10]=value;bridge[11]=upload_bytes;
 bridge[12]=admitted;bridge[13]=wad_ready;
 bridge[17]=arena_valid(&doom_arena);
 if(!bridge[17])bounded_fatal(0x74001u);
 bridge[18]=wad_good;bridge[19]=wad_bad;
 last_seq=seq;bridge[8]=seq;
}
void bounded_fatal(unsigned int code){
 stop_timer();
 if(claimed){
  claim_report[6]=0xf0000000u|code;
  mask31();
  for(;;)__asm__ volatile("":::"memory");
 }
 bounded_escape(0xf0000000u|code);
}
#define CHECK(x) do {unsigned int e=(x);if(e)bounded_fatal(0x10000u+__LINE__*256u+e);}while(0)
#define ASSERT(x) do {if(!(x))bounded_fatal(0x20000u+__LINE__);}while(0)

static void measure(unsigned int id){unsigned int sp,base=(unsigned int)switch_irq_areas[id];
 __asm__ volatile("mov sp,%0":"=r"(sp));irq_sp[id]=sp;
 if(sp<base+192u||sp>=base+8128u)switch_fault|=1u;
}
void switch_irq_enter(unsigned int id,unsigned int frame){
 measure(id);
 if(!lifetime_enter(&life[id],(unsigned int)_Thread_Executing,frame,
                    REG(frame-16),REG(frame-12),REG(frame-8)))switch_fault|=2u;
 if(life[1].live&&life[2].live)two_live++;
}
void switch_irq_body(void){
 _ISR_Nest_level++;_Thread_Dispatch_disable_level++;
 ticks++;
 if(rtems_clock_tick())switch_fault|=8u;
 _Thread_Dispatch_disable_level--;_ISR_Nest_level--;
 if(_Context_Switch_necessary&&!_Thread_Dispatch_disable_level){
  if(_Thread_Heir!=_Thread_Executing)handoffs++;
  _Thread_Dispatch(); /* Can remain suspended on this owner's ISR stack. */
 }
}
void switch_irq_leave(unsigned int id,unsigned int frame){unsigned int i,tc,*save;
 measure(id);
 if(!lifetime_leave(&life[id],(unsigned int)_Thread_Executing,frame,
                    REG(frame-16),REG(frame-12),REG(frame-8)))switch_fault|=4u;
 for(i=0;i<64;i++)if(switch_irq_areas[id][i]!=0xa5u||
                        switch_irq_areas[id][8128+i]!=0xa5u)switch_fault|=16u;
 save=(unsigned int*)(switch_irq_areas[id]+64);
 __asm__ volatile("modtc 0,0,%0":"=r"(tc));
 if((tc^save[16])&0x0f000000u)switch_fault|=32u;
}
static void arm_timer(void){unsigned int error=preflight();
 REG(0xc000fa64u)=error;
 if(error)bounded_fatal(0x50000u|error);
 saved_mask=REG(0xff008504u);
 saved_map=REG(0xff008528u);
 saved_vector=REG(0x4u);
 saved_reload=REG(0xff000310u);
 saved_count=REG(0xff000314u);
 mask31();
 REG(0xff008504u)=0u;
 REG(0x4u)=(unsigned int)timer_isr;
 REG(0xff008528u)=0x00180000u;
 /* 100 MHz / 8 / 125000 = 100 Hz, matching RTEMS 10000 us/tick. */
 REG(0xff000310u)=125000u;
 REG(0xff000314u)=125000u;
 REG(0xff008504u)=0x2000u;
 armed=1u;
 REG(0xff000318u)=0x36u;
}

static void Worker(rtems_task_argument id){unsigned int i,old;
 switch_threads[id+1]=(unsigned int)_Thread_Executing;
 life[id+1].owner=switch_threads[id+1];
 life[id+1].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;
 life[id+1].high=life[id+1].low+_Thread_Executing->Start.Initial_stack.size;
 CHECK(rtems_task_mode(RTEMS_INTERRUPT_LEVEL(0),RTEMS_INTERRUPT_MASK,&old));
 priority0();
 for(i=0;i<100000000u&&!switch_stop;i++){
  loops[id]=i;
  __asm__ volatile("":::"memory");
 }
 if(!switch_stop)switch_fault|=0x100u;
 loops[id]=i;done[id]=1u;
 CHECK(rtems_task_suspend(RTEMS_SELF));
 bounded_fatal(0x30001u+id);
}
static void Init(rtems_task_argument nonce){rtems_task_priority old;
 unsigned int i,j,all_drained=1u;
 (void)nonce;
 for(i=0;i<sizeof(switch_irq_areas);i++)((unsigned char*)switch_irq_areas)[i]=0xa5;
 switch_threads[0]=(unsigned int)_Thread_Executing;
 life[0].owner=switch_threads[0];
 life[0].low=(unsigned int)_Thread_Executing->Start.Initial_stack.area;
 life[0].high=life[0].low+_Thread_Executing->Start.Initial_stack.size;
 CHECK(rtems_task_create(0x574b5230u,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),
                         RTEMS_DEFAULT_ATTRIBUTES,&worker_id[0]));
 CHECK(rtems_task_create(0x574b5231u,2,8192,RTEMS_TIMESLICE|RTEMS_INTERRUPT_LEVEL(31),
                         RTEMS_DEFAULT_ATTRIBUTES,&worker_id[1]));
 CHECK(rtems_task_start(worker_id[0],Worker,0));
 CHECK(rtems_task_start(worker_id[1],Worker,1));
 arm_timer();priority0();
 for(i=0;;i++){
  CHECK(rtems_task_wake_after(2));priority0();
  lease_invalidate_dcache();
  claim_report[4]=ticks;
  bridge_poll();
  if(ticks>=6u&&handoffs>=2u&&life[1].entries&&life[2].entries)
   control[4]=0x59444152u;
  if(control[3]==STOP){
   if(control[0]!=0x3145534cu||control[1]!=0x161610d1u||control[2]!=1u)
    switch_fault|=0x200u;
   else {stop_seen=1u;break;}
  }
  if(switch_fault)bounded_fatal(0x62000u|switch_fault);
 }
 deadline=i;
 switch_stop=1u;
 CHECK(rtems_task_set_priority(RTEMS_SELF,3,&old));
 /* Do not reclaim an ISR continuation before its owner has run again. */
 for(i=0;i<100u&&!done[0]&&!switch_fault;i++){
  CHECK(rtems_task_wake_after(1));priority0();
 }
 for(i=0;i<100u&&!done[1]&&!switch_fault;i++){
  CHECK(rtems_task_wake_after(1));priority0();
 }
 mask31();
 if(!done[0]||!done[1]||!lifetime_drained(life)||
    switch_active[0]||switch_active[1]||switch_active[2]||
    _ISR_Nest_level||_Thread_Dispatch_disable_level)switch_fault|=0x400u;
 for(i=0;i<3;i++)for(j=0;j<64;j++)
  if(switch_irq_areas[i][j]!=0xa5u||switch_irq_areas[i][8128+j]!=0xa5u)
   switch_fault|=0x800u;
 stop_timer();
 if(!restoration||switch_fault||ticks<4u||handoffs<2u||
    !life[1].entries||!life[2].entries||!two_live)
  bounded_fatal(0x61000u|switch_fault);
 {volatile unsigned int *trace=(volatile unsigned int*)(switch_irq_areas[0]+4096);
  trace[0]=0x54504d45u;trace[1]=ticks;trace[2]=handoffs;trace[3]=two_live;
  trace[4]=loops[0];trace[5]=loops[1];trace[6]=deadline;
  trace[7]=life[0].entries;trace[8]=life[0].returns;
  trace[9]=life[1].entries;trace[10]=life[1].returns;
  trace[11]=life[2].entries;trace[12]=life[2].returns;
  trace[13]=irq_sp[0];trace[14]=irq_sp[1];trace[15]=irq_sp[2];
  trace[16]=life[0].vector;trace[17]=life[1].vector;trace[18]=life[2].vector;
  trace[19]=REG(0xff008504u);trace[20]=REG(0xff008528u);
  trace[21]=REG(0x4u);trace[22]=REG(0xff000310u);trace[23]=REG(0xff000314u);
  trace[24]=REG(0xff000318u);trace[25]=REG(0xff008500u);
  trace[26]=switch_fault;trace[27]=restoration;
 }
 if(stop_seen){control[5]=0x214b4341u;control[6]=0x161610d1u;control[7]=1u;}
 result=STOP;
 claim_report[5]=0x45495551u; /* QUIE; the callback/grant stay pinned. */
 mask31();
 for(;;)__asm__ volatile("":::"memory");
}
static rtems_initialization_tasks_table tasks[]={{0x494e4954,4096,1,
 RTEMS_DEFAULT_ATTRIBUTES,Init,RTEMS_INTERRUPT_LEVEL(31),0}};
static rtems_api_configuration_table api={4,0,2,0,0,0,0,0,1,tasks};
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
 unsigned int page,word;
 if(report_addr!=0xc000fa20u||nonce!=0x161610d1u)return 0xbad00001u;
 for(p=_bss_start;p<_bss_end;p++)*p=0;
 if(control[0]!=0x3145534cu||control[1]!=nonce||
    control[2]!=1u||control[3]!=0)return 0xbad00002u;
 for(word=0;word<16u;word++)claim_report[word]=0u;
 if(bank_probe())bounded_fatal(0x71001u);
 if(dma_busy_mask())bounded_fatal(0x72001u);
 /* This is the irreversible boundary until card reset: stock-only diagnostic
  * pages and all other upper pages become the RTEMS application arena. */
 claimed=1u;
 claim_report[0]=0x314d5241u; /* ARM1 */
 claim_report[1]=BANK_PAGES;
 for(page=0;page<BANK_PAGES;page++){
  volatile unsigned int *q=(volatile unsigned int *)(BANK_BASE+page*4096u);
  for(word=0;word<1024u;word++)q[word]=pattern(page,word);
 }
 claim_report[2]=bank_word_hash();
 claim_report[3]=dma_busy_mask();
 if(claim_report[3])bounded_fatal(0x72002u);
 if(!arena_init(&doom_arena,(void *)ARENA_BASE,ARENA_END-ARENA_BASE))
  bounded_fatal(0x73001u);
 image_handle=arena_alloc(&doom_arena,ENGINE_RESERVE);
 zone_handle=arena_alloc(&doom_arena,ZONE_BYTES);
 frame_handle=arena_alloc(&doom_arena,FRAME_BYTES);
 wad_handle=arena_alloc(&doom_arena,WAD_BUFFER_BYTES);
 if(!image_handle||!zone_handle||!frame_handle||!wad_handle)
  bounded_fatal(0x73002u);
 image_base=arena_pin(&doom_arena,image_handle);
 zone_base=arena_pin(&doom_arena,zone_handle);
 frame_base=arena_pin(&doom_arena,frame_handle);
 wad_buffer=arena_pin(&doom_arena,wad_handle);
 if(!image_base||!zone_base||!frame_base||!wad_buffer||
    !arena_valid(&doom_arena))
  bounded_fatal(0x73003u);
 for(word=0;word<WAD_BUFFER_BYTES;word++)wad_buffer[word]=0u;
 claim_report[7]=(unsigned int)image_base;
 claim_report[8]=(unsigned int)zone_base;
 claim_report[9]=(unsigned int)frame_base;
 claim_report[10]=ENGINE_RESERVE;
 claim_report[11]=ZONE_BYTES;
 claim_report[12]=FRAME_BYTES;
 claim_report[13]=image_handle;
 claim_report[14]=zone_handle;
 claim_report[15]=frame_handle;
 for(word=0;word<20u;word++)bridge[word]=0u;
 bridge[6]=0x31475242u;
 bridge[7]=BRIDGE_EPOCH;
 for(word=0;word<16u;word++)wad_wire[word]=0u;
 wad_wire[12]=BRIDGE_EPOCH;wad_wire[14]=(unsigned int)wad_buffer;
 wad_wire[15]=WAD_BUFFER_BYTES;
 rtems_initialize_executive(&config,&cpu);
 bounded_fatal(0x72003u);
}

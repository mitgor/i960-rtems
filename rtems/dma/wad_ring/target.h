/* Included in the owned runtime. All DMA work is task context. Only wr_control
 * runs in the MU handler, before a game owns the runtime. */
#include "wire.h"
struct wr_target {
 unsigned bus[2],generation,active,stage,slot,offset,length,command;
 unsigned local,remote,pad[5]; volatile unsigned desc[8];
 struct wr_record record,reply;
 unsigned char guard[4096],payload[WR_BLOCK],upper[4096];
};
static struct wr_target *wr;
static unsigned wr_bus[2],wr_retired;
#include "profile.h"
#ifndef WR_ADDR
#define WR_ADDR(p) ((unsigned)(p))
#define WR_R(a) (*(volatile unsigned *)(a))
#define WR_S(a) (*(volatile unsigned short *)(a))
#endif
static void wr_fail(void){exclusive_abort();for(;;){}}
static unsigned wr_control(unsigned index,unsigned value){unsigned slot=index-6;
 if(slot>1||owned_running||wr||wr_bus[slot]||value<4096||
 (value&63u)||value>0xffffffffu-WR_BYTES)return ~0u;
 if(wr_bus[slot^1]&&!(value+WR_BYTES<=wr_bus[slot^1]||wr_bus[slot^1]+WR_BYTES<=value))return ~0u;
 wr_bus[slot]=value;return 0;
}
typedef unsigned wr_word __attribute__((__may_alias__));
static unsigned wr_guard(void){WP_START(t);unsigned i;const wr_word*a=(const wr_word*)wr->guard,*b=(const wr_word*)wr->upper;
 for(i=0;i<1024;i++)if(a[i]!=0xa5a5a5a5u||b[i]!=0xa5a5a5a5u)return 0;WP_ADD(wp_bench?13:5,t);return 1;}
static void wr_copy(unsigned char*d,const unsigned char*s,unsigned n){unsigned i;
 if(!(((unsigned long)d|(unsigned long)s)&3)){
  for(i=0;i<n/4;i++)((wr_word*)d)[i]=((const wr_word*)s)[i];i*=4;
 }else i=0;
 for(;i<n;i++)d[i]=s[i];
}
static unsigned wr_geometry(void){
 unsigned b;if(!wr||!wr->active||wr->slot>=2)return 0;b=wr->bus[wr->slot];
 if(!b||b!=wr_bus[wr->slot])return 0;
 if(wr->command==6){
  if(wr->remote==b+WR_RESPONSE&&wr->local==WR_ADDR(&wr->reply)&&wr->length==64)return 1;
  return wr->remote==b+WR_DATA&&wr->local==WR_ADDR(wr->payload)&&wr->length==WR_BLOCK;
 }
 if(wr->command!=7)return 0;
 if(wr->remote!=b+WR_REQUEST&&wr->remote!=b+WR_COMPLETE&&
    wr->remote!=b+WR_REQUEST+28&&wr->remote!=b+WR_COMPLETE+28)return 0;
 return (wr->length==64&&wr->local==WR_ADDR(&wr->record)&&!(wr->remote&63))||
 (wr->length==4&&wr->local==WR_ADDR(&wr->record.w[7])&&(wr->remote&63)==28);
}
static unsigned wr_descriptor_valid(void){unsigned i,e;
 if(!wr_geometry())return 0;
 for(i=0;i<8;i++){
  e=i==1?wr->remote:i==3?wr->local:i==4?wr->length:i==5?wr->command:i>=6?0xfacefeed:0;
  if(wr->desc[i]!=e)return 0;
 }return 1;
}
static unsigned wr_isolation_snapshot(unsigned*w){
 if(!wr_descriptor_valid()||wr->stage<4||wr->stage>10)return 0;
 if(w[0]||w[1]||w[4]||w[5]||w[2]>1||(w[3]&~0x400u)||(w[6]!=2&&w[6]!=6))return 0;
 if((wr->stage==4||wr->stage==5||wr->stage==10)&&(w[2]||w[3]))return 0;
 if(wr->stage>=5&&wr->stage<=9&&w[6]!=6)return 0;
 if(wr->stage>=7&&wr->stage<=8&&w[2]!=1)return 0;
 w[2]=w[3]=0;w[6]=2;return 1;
}
#define WR_STAGE(n) do{__asm__ volatile("":::"memory");wr->stage=n;__asm__ volatile("":::"memory");}while(0)
static void wr_transfer(unsigned slot,unsigned remote,void*local,unsigned n,unsigned command){
 WP_START(total);unsigned hw=0;unsigned i,csr,rc=0;
 if(!owned_owner()||!wr||wr->active||!wd_idle()||!wr_guard())wr_fail();
 wr->slot=slot;wr->remote=remote;wr->local=WR_ADDR(local);wr->length=n;wr->command=command;wr->active=1;
 if(!wr_geometry())wr_fail();
 wr->desc[0]=0;wr->desc[1]=remote;wr->desc[2]=0;wr->desc[3]=WR_ADDR(local);wr->desc[4]=n;wr->desc[5]=command;wr->desc[6]=wr->desc[7]=0xfacefeed;
 WR_STAGE(4);WR_S(0x1204)=6;if(WR_S(0x1204)!=6)wr_fail();
 WR_STAGE(5);WR_R(0x1450)=WR_ADDR(wr->desc);(void)WR_R(0x1450);WR_STAGE(6);
#ifdef I960_WAD_PROFILE
 hw=wp_now();
#endif
 WR_R(0x1440)=1;(void)WR_R(0x1440);WR_STAGE(7);
 for(i=0;i<200000;i++){
  csr=WR_R(0x1444);if(csr&~0x400u){rc=1;break;}
  if(!csr&&!WR_R(0x1450)&&WR_R(0x144c)==WR_ADDR(wr->desc)&&!WR_R(0x1460))break;
 }
 WP_ADD(wp_bench?12:6,hw);
 WR_STAGE(8);if(i==200000)rc=1;
 WR_STAGE(9);WR_R(0x1440)=0;(void)WR_R(0x1440);WR_STAGE(10);WR_S(0x1204)=2;(void)WR_S(0x1204);WR_STAGE(11);
 if(rc||!wd_idle()||WR_R(0x1450)||WR_R(0x1464)!=command||!wr_guard()||!wr_descriptor_valid())wr_fail();
 wr->active=0;WR_STAGE(0);
#ifdef I960_WAD_PROFILE
 if(!wp_bench&&command==6&&remote==wr->bus[slot]+WR_RESPONSE)WP_ADD(16,total);
#endif
 WP_ADD(wp_bench?11:7,total);
}
static void wr_publish(unsigned slot,unsigned where,unsigned magic,unsigned gen,unsigned off,unsigned n,unsigned total){
 wr_record_make(&wr->record,magic,gen,off,n,total);wr->record.w[7]=0;
 wr_transfer(slot,wr->bus[slot]+where,&wr->record,64,7);
 wr->record.w[7]=gen;wr_transfer(slot,wr->bus[slot]+where+28,&wr->record.w[7],4,7);
}
static int wr_read(unsigned f,unsigned off,void*p,unsigned n){
 WP_START(read_time);unsigned stamp=0;struct doom_heap*h=doom_arena_context();unsigned loan=0,stage_loan=0,saved,i,j,count,total,gen,start;
 void*allocation=0;int result=-1;
 if(!owned_owner()||owned_stopping()||!h||f!=1||!wr_bus[0]||!wr_bus[1]||wr||wr_retired||
    (off&(WR_BATCH-1))||!n||n>WR_BATCH||off>=api.file_bytes)return -1;
 total=api.file_bytes-off;if(total>WR_BATCH)total=WR_BATCH;if(n!=total)return -1;
#ifdef I960_WAD_PROFILE
 stamp=wp_now();
#endif
#ifdef I960_PINGPONG
 {extern void frame_dma_wad_barrier(void);frame_dma_wad_barrier();}
#endif
 WP_ADD(1,stamp);
#ifdef I960_WAD_PROFILE
 stamp=wp_now();
#endif
 loan=doom_heap_borrow(h,p,n);if(!loan)return -1;leases++;
 {WP_START(alloc);allocation=owned_allocate(sizeof(*wr)+31);WP_ADD(17,alloc);}if(!allocation)goto done;
 stage_loan=doom_heap_borrow(h,allocation,sizeof(*wr)+31);if(!stage_loan)goto done;
 WP_ADD(2,stamp);
#ifdef I960_WAD_PROFILE
 stamp=wp_now();
#endif
 wr=(struct wr_target*)(((unsigned long)allocation+31)&~31UL);
 /* Struct descriptor must itself be 32-byte aligned. */
 for(i=0;i<sizeof(*wr)/4;i++)((wr_word*)wr)[i]=0;
 for(i=0;i<1024;i++)((wr_word*)wr->guard)[i]=((wr_word*)wr->upper)[i]=0xa5a5a5a5u;
 for(i=0;i<2;i++)wr->bus[i]=wr_bus[i];
 WP_ADD(3,stamp);
 count=(n+WR_BLOCK-1)/WR_BLOCK;
 if(batch.sequence>0xfffffffcu)wr_fail();gen=batch.sequence+1;
 for(i=0;i<count;i++){
  unsigned length=total-i*WR_BLOCK;if(length>WR_BLOCK)length=WR_BLOCK;
  wr_publish((gen+i-1)&1,WR_REQUEST,WR_REQ_MAGIC,gen+i,off+i*WR_BLOCK,length,api.file_bytes);
 }
 for(i=0;i<count;i++){
  unsigned slot=(gen+i-1)&1,length=total-i*WR_BLOCK;if(length>WR_BLOCK)length=WR_BLOCK;start=upload_time();
  {WP_START(wait);
  for(;;){
   wr_transfer(slot,wr->bus[slot]+WR_RESPONSE,&wr->reply,64,6);
   if(wr->reply.w[7]==gen+i){
    /* A first DMA can straddle host publication. Once committed, the response
     * is immutable until this task completes it: reread a stable full record. */
    wr_transfer(slot,wr->bus[slot]+WR_RESPONSE,&wr->reply,64,6);break;
   }
   if(wr->reply.w[7]&&wr->reply.w[7]!=gen+i-2)wr_fail();
   if(owned_stopping()||upload_time()-start>=500){wr_retired=1;result=-4;goto done;}
   {WP_START(service);doom_shared_service();doom_shared_yield();WP_ADD(9,service);}
  }
  WP_ADD(8,wait);}
  if(!wr_record_valid(&wr->reply,WR_RSP_MAGIC,gen+i,api.file_bytes)||wr->reply.w[3]!=off+i*WR_BLOCK||wr->reply.w[4]!=length)wr_fail();
  wr_transfer(slot,wr->bus[slot]+WR_DATA,wr->payload,WR_BLOCK,6);
  for(j=length;j<WR_BLOCK;j++)if(wr->payload[j])wr_fail();
  if(!owned_stopping()){WP_START(copy);wr_copy((unsigned char*)p+i*WR_BLOCK,wr->payload,length);WP_ADD(10,copy);}
#ifdef I960_WAD_PROFILE
  /* Host cannot recycle this slot until completion. Repeat only a valid full
   * payload, into the same borrowed destination, with every normal check. */
  if(!wp_done&&length==WR_BLOCK&&!owned_stopping()){
   unsigned k,j;wp_bench=1;
   for(k=0;k<64;k++){
    {WP_START(empty);WP_ADD(14,empty);}
    if(owned_stopping())break;
    wr_transfer(slot,wr->bus[slot]+WR_DATA,wr->payload,WR_BLOCK,6);
    {WP_START(check);const wr_word*a=(const wr_word*)wr->payload;
     const wr_word*b=(const wr_word*)((unsigned char*)p+i*WR_BLOCK);
     for(j=0;j<WR_BLOCK/4;j++)if(a[j]!=b[j])wr_fail();WP_ADD(15,check);}
    doom_shared_service();
   }
   wp_done=k;wp_bench=0;
  }
#endif
  wr_publish(slot,WR_COMPLETE,WR_END_MAGIC,gen+i,off+i*WR_BLOCK,length,api.file_bytes);
 }
 batch.sequence+=count;batch.accepted+=count;result=owned_stopping()?-4:n;
 done:
#ifdef I960_WAD_PROFILE
 stamp=wp_now();
#endif
 saved=runtime_lock();if(wr&&wr->active)wr_fail();wr=0;runtime_unlock(saved);
 if(stage_loan&&!doom_heap_return(h,allocation,stage_loan))wr_fail();if(allocation){WP_START(free_time);owned_release(allocation);WP_ADD(18,free_time);}
 if(!doom_heap_return(h,p,loan))wr_fail();leases--;WP_ADD(4,stamp);WP_ADD(0,read_time);return result;
}

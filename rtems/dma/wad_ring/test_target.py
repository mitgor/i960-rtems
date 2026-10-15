#!/usr/bin/env python3
"""Execute the real ring target with modeled DMA and sanitizer-checked RAM."""
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[3]
code=r'''
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <setjmp.h>
#include <stddef.h>
struct doom_heap {unsigned dummy;};static struct doom_heap heap;
static struct {unsigned file_bytes;}api;
static struct {unsigned sequence,accepted;}batch;
static unsigned owned_running,leases,stopping,clock_tick,mode,transfers,response_reads;
static jmp_buf failed;
static unsigned regs[0x1800/4],cmd[2];static unsigned char host[2][40960],filebytes[100003];
static void*allocation;static unsigned address(const void*);static unsigned*reg(unsigned);
#define WR_ADDR(p) address((const void*)(p))
#define WR_R(a) (*reg(a))
#define WR_S(a) cmd[(a)==0x1204?0:1]
static void exclusive_abort(void){longjmp(failed,1);}
static unsigned owned_owner(void){return 1;}
static unsigned owned_stopping(void){return stopping;}
static struct doom_heap*doom_arena_context(void){return &heap;}
static unsigned doom_heap_borrow(struct doom_heap*h,void*p,unsigned n){assert(p&&n);return 1;}
static unsigned doom_heap_return(struct doom_heap*h,void*p,unsigned t){return t==1;}
static void*owned_allocate(unsigned n){allocation=malloc(n);return allocation;}
static void owned_release(void*p){free(p);allocation=0;}
static unsigned runtime_lock(void){return 0;}
static void runtime_unlock(unsigned n){}
static unsigned upload_time(void){return clock_tick;}
static void doom_shared_service(void){}
static void doom_shared_yield(void){clock_tick++;if(mode==4&&clock_tick==2)stopping=1;}
static unsigned wd_idle(void){return !regs[0x1440/4]&&!regs[0x1444/4]&&cmd[0]==2;}
#include "rtems/dma/wad_ring/target.h"
static unsigned address(const void*p){return 0xc0800000u+(unsigned)((const char*)p-(const char*)allocation);}
static unsigned*reg(unsigned a){
 if(a==0x1444&&regs[0x1440/4]){
  unsigned slot=wr->slot,off=wr->desc[1]-(0x100000+slot*0x10000),len=wr->desc[4],words[16]={0};
  void*local=(char*)allocation+(wr->desc[3]-0xc0800000u);
  struct wr_record *q=(void*)(host[slot]+WR_REQUEST),*r=(void*)(host[slot]+WR_RESPONSE);
  assert(!(WR_ADDR(wr->desc)&31));assert(off+len<=WR_BYTES);assert(wr_geometry());
  words[2]=1;words[6]=6;assert(wr_isolation_snapshot(words));
  if(!transfers){unsigned k,bit,save;for(k=0;k<8;k++){save=wr->desc[k];for(bit=0;bit<32;bit++){wr->desc[k]=save^(1u<<bit);memset(words,0,sizeof words);words[2]=1;words[6]=6;assert(!wr_isolation_snapshot(words));}wr->desc[k]=save;}}
  transfers++;
  if(mode==3){regs[a/4]=0x400;return regs+a/4;}
  if(wr->desc[5]==7)memcpy(host[slot]+off,local,len);
  else {
   if(off==WR_RESPONSE&&q->w[7]&&mode!=2&&mode!=4){
    assert(wr_record_valid(q,WR_REQ_MAGIC,q->w[7],api.file_bytes));
    memset(host[slot]+WR_DATA,0,WR_BLOCK);memcpy(host[slot]+WR_DATA,filebytes+q->w[3],q->w[4]);
    *r=*q;r->w[0]=WR_RSP_MAGIC;if(mode==1)r->w[3]^=WR_BLOCK;
   }
   memcpy(local,host[slot]+off,len);
   if(off==WR_RESPONSE&&mode==6&&response_reads++==0)((struct wr_record*)local)->w[3]^=32768;
   if(off==WR_DATA&&mode==7)((unsigned char*)local)[32767]=1;
  }
  regs[0x144c/4]=WR_ADDR(wr->desc);regs[0x1450/4]=regs[0x1460/4]=regs[a/4]=0;regs[0x1464/4]=wr->desc[5];if(mode==8)wr->desc[3]^=4;
 }return regs+a/4;
}
static void reset(void){unsigned i;memset(regs,0,sizeof regs);memset(host,0xa5,sizeof host);for(i=0;i<2;i++)memset(host[i]+4096,0,192);
 cmd[0]=2;batch.sequence=batch.accepted=leases=stopping=clock_tick=mode=transfers=response_reads=0;wr=0;wr_retired=0;wr_bus[0]=wr_bus[1]=0;api.file_bytes=sizeof filebytes;
 assert(wr_control(6,0x100001)==~0u);assert(!wr_control(6,0x100000));assert(wr_control(7,0x100040)==~0u);assert(!wr_control(7,0x110000));
 for(i=0;i<sizeof filebytes;i++)filebytes[i]=(i*7)^(i>>7);
}
int main(void){unsigned char out[65536];unsigned i;
 reset();assert(offsetof(struct wr_target,desc)%32==0);
 assert(wr_read(1,1,out,65536)==-1&&!transfers);
 assert(wr_read(1,0,out,65536)==65536&&!memcmp(out,filebytes,65536)&&batch.sequence==2&&!leases&&!allocation);
 assert(wr_read(1,65536,out,sizeof filebytes-65536)==sizeof filebytes-65536&&!memcmp(out,filebytes+65536,sizeof filebytes-65536)&&batch.sequence==4);
 reset();allocation=malloc(sizeof(*wr)+31);wr=(void*)(((unsigned long)allocation+31)&~31UL);memset(wr,0,sizeof(*wr));memset(wr->guard,0xa5,4096);memset(wr->upper,0xa5,4096);
 for(i=0;i<8192;i++){unsigned char*p=i<4096?wr->guard+i:wr->upper+i-4096;*p^=1;assert(!wr_guard());*p^=1;}assert(wr_guard());free(allocation);allocation=0;wr=0;
 {unsigned char a[256],b[256];unsigned n,j;for(i=0;i<256;i++)a[i]=i;for(i=0;i<4;i++)for(j=0;j<4;j++)for(n=0;n<128;n++){memset(b,0,sizeof b);wr_copy(b+i,a+j,n);assert(!memcmp(b+i,a+j,n));}}
 reset();mode=2;assert(wr_read(1,0,out,65536)==-4&&clock_tick==500&&!wr&&!allocation&&!leases);
 reset();mode=4;assert(wr_read(1,0,out,65536)==-4&&clock_tick==2&&!wr&&!allocation&&!leases&&wr_retired);
 for(i=1;i<=3;i+=2){reset();mode=i;if(!setjmp(failed)){wr_read(1,0,out,65536);assert(0);}assert(allocation&&wr&&leases);free(allocation);allocation=0;}
 reset();mode=6;assert(wr_read(1,0,out,65536)==65536&&!memcmp(out,filebytes,65536));
 reset();mode=7;if(!setjmp(failed)){wr_read(1,65536,out,sizeof filebytes-65536);assert(0);}assert(allocation&&wr&&leases);free(allocation);allocation=0;
 reset();mode=8;if(!setjmp(failed)){wr_read(1,0,out,65536);assert(0);}assert(allocation&&wr&&leases);free(allocation);allocation=0;
 reset();stopping=1;assert(wr_read(1,0,out,65536)==-1&&!transfers);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS ring target: two-slot read, wrap/reuse, EOF padding, active lease audits, malformed completion, host timeout, hardware quarantine, 256 descriptor mutations, STOP before start and during host wait')

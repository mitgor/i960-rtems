#ifdef I960_RESIDENT_UPLOAD
#include "upload.h"
#include "../../loader/segmented/image.h"
#ifndef UPLOAD_NATIVE
#define R(a) (*(volatile unsigned int*)(a))
extern unsigned int upload_stopping(void),upload_time(void);
extern void exclusive_abort(void);
static void barrier(void){__asm__ volatile("":::"memory");}
static int sync_code(void*p,unsigned int n){unsigned int scratch;(void)p;(void)n;
 __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
 __asm__ volatile("icctl 2,0,%0":"=r"(scratch)::"memory");return 1;}
#else
#include "upload_native.h"
#endif
static struct arena app_arena;
static struct seg_image image;
static unsigned int initialized,packet_bytes,packet_words,inbox[UPLOAD_WORDS],reply[UPLOAD_REPLY],frozen[UPLOAD_REPLY];
static volatile unsigned int pending;
static unsigned int protect_tick;
static unsigned int sequence,accepted,rejected,completed,cancelled,proof_bytes,proof_checks;
static unsigned int guard(unsigned long a,unsigned int value,unsigned int write){unsigned int i;for(i=0;i<16;i++){
 if(write)R(a+4*i)=value;else if(R(a+4*i)!=value)return 0;}return 1;}
unsigned int upload_guards(void){return initialized&&guard(UPLOAD_GUARD_LO,0x31415055u,0)&&guard(UPLOAD_GUARD_HI,0x32415055u,0);}
unsigned int upload_init(void){if(initialized)return 0;
 guard(UPLOAD_GUARD_LO,0x31415055u,1);guard(UPLOAD_GUARD_HI,0x32415055u,1);
 if(!arena_init(&app_arena,(void*)UPLOAD_BASE,UPLOAD_BYTES))return 0;seg_init(&image);initialized=1;return 1;}
/* ISR/mailbox path only: no allocator, hashes, code execution or image copying. */
unsigned int upload_control(unsigned int op,unsigned int index,unsigned int value,unsigned int running){unsigned int i;
 if(op==0x74){if(index)return ~0u;for(i=0;i<UPLOAD_REPLY;i++)frozen[i]=reply[i];frozen[3]=pending;frozen[4]=image.state;return 0;}
 if(op==0x73)return index<UPLOAD_REPLY?frozen[index]:~0u;
 if(!initialized||!running||upload_stopping())return 0xfffffffeu;
 if(op==0x70){if(index||pending||value<32||value>sizeof(inbox)||(value&3))return ~0u;packet_bytes=value;packet_words=0;return 0;}
 if(op==0x71){if(pending||!packet_bytes||index!=packet_words||index>=packet_bytes/4)return ~0u;inbox[packet_words++]=value;return 0;}
 if(op==0x72){if(index||pending||!packet_bytes||packet_words!=packet_bytes/4)return ~0u;
  packet_bytes=0;barrier();pending=1;return 0;}
 return ~0u;
}
static unsigned int proof(void){unsigned int h,i,rc=0;volatile unsigned int*p;
 h=arena_alloc(&app_arena,6u*1048576u);if(!h)return 1;p=arena_pin(&app_arena,h);if(!p)return 2;
 for(i=0;i<6u*1048576u/4;i++){if(!(i&255)&&upload_stopping()){rc=3;break;}p[i]=i^0xa596317bu;}
 if(!rc)for(i=0;i<6u*1048576u/4;i++){if(!(i&255)&&upload_stopping()){rc=3;break;}if(p[i]!=(i^0xa596317bu)){exclusive_abort();return 4;}}
 if(!rc){proof_bytes=6u*1048576u;proof_checks++;}
 if(!arena_unpin(&app_arena,h)||!arena_release(&app_arena,h))exclusive_abort();return rc;
}
/* RUN is deliberately restricted to the reviewed five-word returning probe.
 * Arbitrary task launch needs a separate owned-context/runtime ABI contract. */
static unsigned int run_probe(unsigned int *value){unsigned int i;unsigned char*p;unsigned int(*fn)(unsigned int);
 static const unsigned int code[5]={0x90841000u,0x8c883000u,0xa5a5a5a5u,0x58844310u,0x0a000000u};
 if(image.state!=SEG_READY||image.manifest.count!=2||image.manifest.entry!=image.manifest.segment[0].offset||image.manifest.segment[0].flags!=SEG_RX||image.manifest.segment[0].file_bytes<sizeof(code)||image.manifest.segment[1].flags!=SEG_RW||image.manifest.segment[1].file_bytes<4)return 1;
 p=image.base+image.manifest.segment[0].offset;for(i=0;i<sizeof(code);i++)if(p[i]!=((const unsigned char*)code)[i])return 2;
 p=image.base+image.manifest.segment[1].offset;
 for(i=image.manifest.segment[1].file_bytes;i<image.manifest.segment[1].memory_bytes;i++)if(p[i])return 5;
 fn=(unsigned int(*)(unsigned int))seg_start(&image);if(!fn)return 3;
#ifndef UPLOAD_NATIVE
 *value=fn((unsigned int)(image.base+image.manifest.segment[1].offset));
#else
 *value=0xe4f1e4e1u;
#endif
 if(!seg_complete(&image))return 4;return 0;
}
void upload_step(void){unsigned int command,rc=0,value=0,n,i;
 if(!initialized)return;
 if(!upload_guards()){exclusive_abort();return;}
 if(upload_time()!=protect_tick){protect_tick=upload_time();if(!upload_protect_step()){exclusive_abort();return;}}
 if(!pending)return;
 n=packet_words*4;command=inbox[2];
 if(inbox[0]!=0x314c5055u||!inbox[1]||sequence==~0u||inbox[1]!=sequence+1||inbox[6]||inbox[7]){rc=1;goto done;}
 sequence=inbox[1];accepted++;
 if(upload_stopping()){rc=2;goto done;}
 if(command==1){struct manifest m;
  if(n!=32+43*4||inbox[3]||inbox[4]||inbox[5]){rc=3;goto done;}
  m.abi=inbox[8];m.count=inbox[9];m.entry=inbox[10];
  for(i=0;i<8;i++){struct segment *p=&m.segment[i];unsigned int *w=inbox+11+5*i;
   p->offset=w[0];p->file_bytes=w[1];p->memory_bytes=w[2];p->flags=w[3];p->crc32=w[4];}
  rc=seg_begin(&image,&app_arena,&m)?0:4;
 }else if(command==2){if(!inbox[5]||inbox[5]>SEG_CHUNK||n!=32+((inbox[5]+3)&~3u)){rc=3;goto done;}
  rc=seg_write(&image,inbox[3],inbox[4],inbox+8,inbox[5])?0:4;
 }else{
  if(n!=32||inbox[3]||inbox[4]||inbox[5]){rc=3;goto done;}
  if(command==3){value=seg_prepare(&image,sync_code);if(!value)rc=4;}
  else if(command==4)rc=run_probe(&value);
  else if(command==5){if(!seg_cancel(&image))rc=4;else cancelled++;}
  else if(command==6)value=arena_valid(&app_arena);
  else if(command==7)rc=proof();
  else rc=3;
 }
done:
 if(rc)rejected++;else completed++;
 reply[0]=0x31525055u;reply[1]=inbox[1];reply[2]=rc;reply[4]=image.state;reply[5]=value;
 reply[6]=accepted;reply[7]=rejected;reply[8]=completed;reply[9]=cancelled;
 reply[10]=proof_bytes;reply[11]=proof_checks;reply[12]=UPLOAD_BASE;reply[13]=UPLOAD_BYTES;reply[14]=sequence;reply[15]=image.handle;
 barrier();pending=0;
}
unsigned int upload_finish(void){unsigned int i;
 /* Both workers/IRQ contexts have drained before this call. */
 if(pending){pending=0;rejected++;}
 if(image.state!=SEG_EMPTY){if(!seg_cancel(&image))return 0;cancelled++;}
 reply[4]=image.state;reply[9]=cancelled;reply[15]=image.handle;
 for(i=0;i<ARENA_SLOTS;i++)if(app_arena.slot[i].span)return 0;
 return upload_guards()&&arena_valid(&app_arena)&&upload_protect_finish();
}
#endif

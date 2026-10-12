#!/usr/bin/env python3
"""Actual resident mailbox/allocator/image code under native sanitizers."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parent
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned char memory[8*1048576+128] __attribute__((aligned(16)));
#define UPLOAD_GUARD_LO ((unsigned long)memory)
#define I960_RESIDENT_UPLOAD 1
#define UPLOAD_NATIVE 1
#include "upload.c"
static void send(unsigned int seq,unsigned int command,unsigned int a,unsigned int b,unsigned int c,void*data,unsigned int bytes){
 unsigned int packet[256]={0},i;packet[0]=0x314c5055;packet[1]=seq;packet[2]=command;packet[3]=a;packet[4]=b;packet[5]=c;
 if(bytes)memcpy(packet+8,data,bytes);bytes=32+((bytes+3)&~3u);
 assert(!upload_control(0x70,0,bytes,1));
 assert(upload_control(0x71,1,0,1)==~0u);
 for(i=0;i<bytes/4;i++)assert(!upload_control(0x71,i,packet[i],1));
 assert(!upload_control(0x72,0,0,1));assert(upload_control(0x70,0,32,1)==~0u);
 upload_step();assert(!pending);assert(!upload_control(0x74,0,0,1));
 for(i=0;i<16;i++)assert(upload_control(0x73,i,0,1)==frozen[i]);
}
static void begin(unsigned int seq,struct manifest*m){unsigned int w[43],i;w[0]=m->abi;w[1]=m->count;w[2]=m->entry;
 for(i=0;i<8;i++){w[3+5*i]=m->segment[i].offset;w[4+5*i]=m->segment[i].file_bytes;w[5+5*i]=m->segment[i].memory_bytes;w[6+5*i]=m->segment[i].flags;w[7+5*i]=m->segment[i].crc32;}
 send(seq,1,0,0,0,w,sizeof(w));}
int main(void){struct manifest m={0};unsigned int data=0x41544144,seq=0;unsigned int code[5]={0x90841000,0x8c883000,0xa5a5a5a5,0x58844310,0x0a000000};
 assert(upload_control(0x70,0,32,1)==0xfffffffe);assert(upload_init());assert(!upload_init());
 assert(upload_control(0x70,0,1028,1)==~0u);assert(upload_control(0x72,0,0,1)==~0u);
 send(++seq,7,0,0,0,0,0);assert(!reply[2]&&reply[10]==6291456);
 m.abi=1;m.count=2;m.segment[0]=(struct segment){0,20,20,1,seg_crc32(0,code,20)};m.segment[1]=(struct segment){32,4,8192,2,seg_crc32(0,&data,4)};
 begin(++seq,&m);assert(!reply[2]);
 send(seq,6,0,0,0,0,0);assert(reply[2]==1); /* no replay */
 send(++seq,3,0,0,0,0,0);assert(reply[2]==4); /* incomplete */
 send(++seq,2,0,0,20,code,20);assert(!reply[2]);send(++seq,2,1,0,4,&data,4);assert(!reply[2]);
 while(image.state!=SEG_READY){send(++seq,3,0,0,0,0,0);assert(!reply[2]);}
 send(++seq,4,0,0,0,0,0);assert(!reply[2]&&reply[5]==0xe4f1e4e1);
 send(++seq,5,0,0,0,0,0);assert(!reply[2]&&image.state==SEG_EMPTY);
 begin(++seq,&m);assert(!reply[2]);stopping=1;assert(upload_control(0x70,0,32,1)==0xfffffffe);assert(upload_finish());stopping=0;
 begin(++seq,&m);assert(!reply[2]);code[0]^=1;
 send(++seq,2,0,0,20,code,20);send(++seq,2,1,0,4,&data,4);
 while(image.state!=SEG_QUARANTINED)send(++seq,3,0,0,0,0,0);
 assert(reply[2]==4&&!upload_finish());assert(!arena_release(&app_arena,image.handle));
 memory[0]^=1;assert(!upload_guards());
 puts("PASS resident UPL1: bounds, sequence, busy inbox, six-MiB proof, BSS, probe gate, STOP cleanup, checksum quarantine, guard failure");
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.c').write_text(prefix)
 (p/'upload_native.h').write_text('''#define R(a) (*(unsigned int*)(unsigned long)(a))
static unsigned int stopping,now;
static unsigned int upload_stopping(void){return stopping;}
static unsigned int upload_time(void){return ++now;}
static void barrier(void){}
static int sync_code(void*p,unsigned int n){return 1;}
static void exclusive_abort(void){assert(0);}
unsigned int upload_protect_step(void){return 1;}
unsigned int upload_protect_finish(void){return 1;}
''')
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-g','-I'+str(p),'-I'+str(r),str(p/'test.c'),str(r.parents[1]/'loader/segmented/arena.c'),str(r.parents[1]/'loader/segmented/image.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
 # Recompile the same code with deliberately padded internal C structs.
 # Wire decoding must remain field based on compilers with different layouts.
 core=r.parents[1]/'loader/segmented'
 header=(core/'image.h').read_text().replace('flags,crc32;};','flags,crc32;} __attribute__((aligned(16)));')
 (p/'image.h').write_text(header);(p/'image.c').write_text((core/'image.c').read_text());(p/'arena.h').write_text((core/'arena.h').read_text())
 (p/'upload.c').write_text((r/'upload.c').read_text().replace('"../../loader/segmented/image.h"','"image.h"'))
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-g','-I'+str(p),'-I'+str(r),str(p/'test.c'),str(core/'arena.c'),str(p/'image.c'),'-o',str(p/'padded')],check=True)
 subprocess.run([str(p/'padded')],check=True)

 # Opt-in Doom libc uses the SAME arena while a prepared image remains pinned.
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);source=prefix.replace('#include "upload.c"','#define I960_DOOM_HEAP 1\n#include "upload.c"\n#include "doom_heap_proof.c"')
 source=source.replace('send(++seq,4,0,0,0,0,0);assert(!reply[2]', 'send(++seq,8,0,0,0,0,0);assert(!reply[2]&&reply[5]==0x444c4942);\n send(++seq,4,0,0,0,0,0);assert(!reply[2]')
 (p/'test.c').write_text(source)
 (p/'upload_native.h').write_text('#define R(a) (*(unsigned int*)(unsigned long)(a))\nstatic unsigned int stopping,now;\nstatic unsigned int upload_stopping(void){return stopping;}\nstatic unsigned int upload_time(void){return ++now;}\nstatic void barrier(void){}\nstatic int sync_code(void*p,unsigned int n){return 1;}\nstatic void exclusive_abort(void){assert(0);}\nunsigned int upload_protect_step(void){return 1;}\nunsigned int upload_protect_finish(void){return 1;}\n')
 runtime=r.parents[1]/'game/doom/runtime'
 subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-g','-I'+str(p),'-I'+str(r),str(p/'test.c'),str(core/'arena.c'),str(core/'image.c'),str(runtime/'heap.c'),str(runtime/'libc.c'),'-o',str(p/'doom')],check=True)
 subprocess.run([str(p/'doom')],check=True)
 print('PASS Doom libc proof with pinned image and retained-buffer STOP drain')

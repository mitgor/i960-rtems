#!/usr/bin/env python3
"""Real admission/arena core with explicitly modeled entry (no ISA execution)."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('admission',type=Path);a=p.parse_args();r=Path(__file__).resolve().parent
source=r'''
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define I960_DOOM_SHARED 1
#define I960_DOOM_ENGINE 1
#define I960_DOOM_RUNTIME 1
#define I960_DOOM_OWNED 1
#define ENGINE_GATE_NATIVE 1
unsigned upload_stopping(void);
#include "engine_gate.c"
static struct doom_runtime_owned api;
static unsigned mode,aborted,begins,ends,yields,stop;
static unsigned char memory[8*1048576] __attribute__((aligned(16)));
const struct doom_runtime_owned*doom_runtime_owned_api(void){return &api;}
unsigned doom_runtime_owned_begin(void){begins++;return mode!=6;}
unsigned doom_runtime_owned_end(void){ends++;return 1;}
unsigned upload_stopping(void){return stop;}
void doom_shared_yield(void){yields++;}
int doom_shared_enter(void*p){(void)p;return 1;}
void doom_shared_leave(void*p){(void)p;}
void exclusive_abort(void){aborted++;}
static int sync(void*p,unsigned n){(void)p;(void)n;return 1;}
unsigned engine_native_call(struct seg_image*s,const struct doom_runtime_owned*a){unsigned row[12]={0x454e4750,1,6291456,123,456,1,1,6300000,4,0,1,0},i;(void)a;
 if(mode==4){row[6]=0;row[9]=2;}
 for(i=0;i<12;i++)store(s->base+ENGINE_RESULT+4*i,row[i]);if(mode==5)s->base[0]^=1;return mode==4?0x454e4702:0x454e4700;}
int main(int argc,char**argv){struct arena arena;struct seg_image image;struct manifest m;unsigned i,n,v,rc;FILE*f;unsigned char block[1024];assert(argc==3);
 for(mode=0;mode<8;mode++){memset(&arena,0,sizeof arena);assert(arena_init(&arena,memory,sizeof memory));seg_init(&image);memset(&m,0,sizeof m);m.abi=1;m.count=4;m.entry=ENGINE_ENTRY;
 for(i=0;i<4;i++){struct segment*s=m.segment+i;const unsigned*g=engine_geometry[i];s->offset=g[0];s->file_bytes=g[1];s->memory_bytes=g[2];s->flags=g[3];}
 assert(seg_begin(&image,&arena,&m));
 for(i=0;i<2;i++){f=fopen(argv[1],"rb");assert(f);assert(!fseek(f,engine_geometry[i][0],SEEK_SET));for(n=0;n<engine_geometry[i][1];){unsigned k=engine_geometry[i][1]-n;if(k>1024)k=1024;assert(fread(block,1,k,f)==k);assert(seg_write(&image,i,n,block,k));image.manifest.segment[i].crc32=seg_crc32(image.manifest.segment[i].crc32,block,k);n+=k;}fclose(f);}
 f=fopen(argv[2],"rb");assert(f);for(n=0;n<ENGINE_SITES*4;){unsigned k=ENGINE_SITES*4-n;if(k>1024)k=1024;assert(fread(block,1,k,f)==k);assert(seg_write(&image,3,n,block,k));image.manifest.segment[3].crc32=seg_crc32(image.manifest.segment[3].crc32,block,k);n+=k;}fclose(f);
 while((rc=seg_prepare(&image,sync))==1){}assert(rc==2);
 aborted=begins=ends=yields=stop=0;
 if(mode==1)image.base[0]^=1;if(mode==2)image.base[ENGINE_META]^=1;if(mode==3)image.base[engine_geometry[2][0]]=1;if(mode==7)stop=1;
 rc=engine_run(&image,sync,&v);
 if(mode==0||mode==4){assert(!rc&&!aborted&&begins==1&&ends==1&&image.state==SEG_EMPTY&&arena_valid(&arena));}
 else if(mode==5||mode==6){assert(rc==7&&aborted==1&&image.state==SEG_QUARANTINED);}
 else {assert(rc==2&&!begins&&!aborted&&image.state==SEG_READY);assert(seg_cancel(&image));}
 }
 puts("PASS: compiled SHA identity, metadata/BSS/STOP refusals, modeled normal/cancel cleanup, post-code and failed-scope quarantine; no i960 execution");return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);(t/'test.c').write_text(source)
 subprocess.run(['gcc','-m32','-no-pie','-std=c11','-Os','-g','-fsanitize=address,undefined','-I'+str(r),'-I'+str(a.admission),str(t/'test.c'),str(r/'../../loader/digest/sha256.c'),str(r/'../../loader/segmented/image.c'),str(r/'../../loader/segmented/arena.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test'),str(a.admission/'template.bin'),str(a.admission/'relocations.bin')],check=True)

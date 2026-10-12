#!/usr/bin/env python3
"""Real probe + replay service: instant replies fail its clock-liveness check."""
import subprocess,tempfile
from pathlib import Path
from runtime_replay import polled_service
root=Path(__file__).resolve().parents[2]
src=r'''
#include <assert.h>
#include <errno.h>
#include <string.h>
#include <time.h>
#include "game/doom/runtime/entry/probe.c"
static unsigned now,replayed,delayed,elapsed;
static unsigned char data[1024],buffer[1024];
static void runtime_service(void){replayed++;}
static int modeled_sleep(const struct timespec*t,struct timespec*remaining){
 assert(t->tv_sec==0&&t->tv_nsec==10000000);now+=10;elapsed++;return 0;
}
#define nanosleep modeled_sleep
'''+polled_service()+r'''
static void*alloc(unsigned n){assert(n==1024);return buffer;}
static void release(void*p){assert(p==buffer);}
static unsigned ticks(void){return now;}
static int read_data(unsigned file,unsigned off,void*p,unsigned n){
 if(file!=1||off>1024||n>512||p!=buffer)return -1;
 if(off==1024)return 0;
 if(delayed)doom_shared_service();else runtime_service();
 if(n>1024-off)n=1024-off;memcpy(p,data+off,n);return n;
}
int main(void){unsigned i,h=2166136261u;
 struct doom_runtime_v1 a={.magic=DOOM_API_MAGIC,.version=DOOM_API_VERSION,
 .bytes=sizeof(a),.features=DOOM_API_FEATURES,.pointer_bytes=sizeof(void*),
 .little_endian=1,.max_read=512,.file_id=1,.file_bytes=1024,
 .allocate=alloc,.release=release,.ticks_ms=ticks,.read=read_data};
 memcpy(data,"IWAD",4);data[4]=1;data[9]=1;
 for(i=0;i<12;i++)h=(h^data[i])*16777619u;
 for(i=256;i<768;i++)h=(h^data[i])*16777619u;
 for(i=987;i<1024;i++)h=(h^data[i])*16777619u;
 assert(doom_runtime_probe(&a)==3&&now==0&&replayed==3);
 delayed=1;assert(doom_runtime_probe(&a)==h&&now==30&&elapsed==3&&replayed==6);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 t=Path(d);(t/'test.c').write_text(src)
 subprocess.run(['cc','-std=c11','-fsanitize=address,undefined','-I'+str(root),str(t/'test.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test')],check=True)
print('PASS: actual probe rejects instant replies; replay service advances modeled transport time and preserves exact oracle')

#!/usr/bin/env python3
"""Exercise real frame ownership/IRQ code against a simulated host and clock."""
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parents[2]
code=r'''
#include <assert.h>
#include <string.h>
#include "game/doom/runtime/owned/api.h"
#define ENGINE_PLAYABLE 1
static unsigned now,stop,mode,calls;
static unsigned char memory[65536];
static unsigned word(const unsigned char*p){unsigned v;memcpy(&v,p,4);return v;}
static void doom_shared_yield(void){}
#include "rtems/residentnet/engine_play.h"
static unsigned owner(void){return 1;}
static unsigned stopping(void){return stop;}
static unsigned clock_ms(void){return now;}
void doom_shared_service(void){unsigned i,j,second;calls++;
 if(mode==1){stop=1;return;}if(mode==2){now=60000;return;}
 assert(engine_play_control(0,0)==1);
 assert(engine_frame_control(0x6e,0,0)==~0u);
 assert(engine_frame_control(0x6c,0,2)==~0u);
 assert(!engine_frame_control(0x6c,0,1));
 assert(engine_frame_control(0x6d,0,65536)==~0u);
 assert(engine_frame_control(0x6d,0,1)==~0u);
 assert(!engine_frame_control(0x6d,0,0));
 for(i=0;i<256;i++)assert(engine_frame_control(0x6e,i,0)==word(memory+4*i));
 assert(engine_frame_control(0x6e,256,0)==~0u);
 for(j=0;j<65536;j+=1024){
  assert(!engine_frame_control(0x6d,0,j));
  for(i=0;i<128;i++){second=0xdeadbeef;assert(engine_frame_pair(i,0,&second)==word(memory+j+8*i));assert(second==word(memory+j+8*i+4));}
 }
 second=123;assert(engine_frame_pair(128,0,&second)==~0u&&second==123);
 assert(engine_frame_pair(0,1,&second)==~0u&&second==123);
 assert(engine_frame_control(0x6c,0,2)==~0u);assert(engine_frame_pair(0,0,&second)==~0u&&second==123);
 assert(!engine_frame_control(0x6c,0,1));assert(engine_frame_pair(0,0,&second)==~0u);
 assert(!engine_frame_control(0x6d,0,0));
 assert(engine_play_control(1,2)==~0u);
 for(i=0;i<31;i++)assert(!engine_play_control(2,i));
 assert(engine_play_control(2,31)==~0u);assert(engine_play_control(2,512)==~0u);
 assert(!engine_play_control(1,1));assert(engine_frame_pair(0,0,&second)==~0u);assert(engine_frame_control(0x6e,0,0)==~0u);
}
int main(void){struct doom_runtime_owned a;unsigned i;memset(&a,0,sizeof a);a.owner=owner;a.stopping=stopping;a.io.ticks_ms=clock_ms;play_api=&a;play_allowed=memory;
 for(i=0;i<65536;i++)memory[i]=(unsigned char)(i^(i>>8)^(i>>13));
 assert(!engine_play_mark(100,(unsigned long)memory+1,65536,1));
 assert(engine_play_mark(100,(unsigned long)memory,65536,1)==1&&calls==1&&!play_frame);
 for(i=0;i<31;i++)assert(engine_play_mark(101,0,0,0)==(int)i+2);
 assert(engine_play_mark(101,0,0,0)==1);
 assert(engine_play_control(1,1)==~0u);
 mode=1;assert(engine_play_mark(100,(unsigned long)memory,65536,2)==-1&&!play_frame);
 stop=0;mode=2;assert(engine_play_mark(100,(unsigned long)memory,65536,3)==-1&&!play_frame);
 play_api=0;assert(engine_frame_finish());return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 s=Path(d)/'test.c';s.write_text(code);exe=Path(d)/'test'
 subprocess.run(['gcc','-m32','-no-pie','-Wall','-Wextra','-I'+str(r),str(s),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS immutable frame, stale ACK, bounds, bounded key FIFO, STOP, timeout, final release')

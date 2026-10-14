#!/usr/bin/env python3
"""Actual two-slot publication: backpressure, stale ACK, bounds, STOP and timeout."""
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
code=r'''
#include <assert.h>
#include <string.h>
#include "game/doom/runtime/owned/api.h"
#define ENGINE_PLAYABLE 1
#define ENGINE_PLAY_DOUBLE 1
static unsigned now,stop,mode,calls;
static unsigned char memory[131072];
static unsigned word(const unsigned char*p){unsigned v;memcpy(&v,p,4);return v;}
static void doom_shared_yield(void){}
#include "rtems/residentnet/engine_play.h"
static unsigned owner(void){return 1;}
static unsigned stopping(void){return stop;}
static unsigned clock_ms(void){return now;}
void doom_shared_service(void){unsigned g=play_sequence,i;calls++;
 if(mode==1){stop=1;return;}if(mode==2){now+=60000;return;}
 assert(play_frame==memory+((g-1)&1)*65536);
 for(i=0;i<65536;i++)assert(play_frame[i]==(unsigned char)g);
 assert(engine_play_control(1,g+1)==~0u);
 assert(engine_play_control(1,g)==0);
}
int main(void){struct doom_runtime_owned a;unsigned g;memset(&a,0,sizeof a);a.owner=owner;a.stopping=stopping;a.io.ticks_ms=clock_ms;play_api=&a;play_allowed=memory;
 for(g=1;g<=32;g++){
  unsigned char*p=memory+((g-1)&1)*65536;memset(p,g,65536);
  assert(!engine_play_mark(100,(unsigned long)p+1,65536,g));
  assert(engine_play_mark(100,(unsigned long)p,65536,g)==1);
  assert(play_frame==p&&play_sequence==g&&!play_ack&&calls==g-1);
 }
 mode=1;assert(engine_play_mark(100,(unsigned long)memory,65536,33)==-1&&!play_frame);
 stop=0;mode=0;memset(memory,33,65536);assert(engine_play_mark(100,(unsigned long)memory,65536,33)==1);
 mode=2;assert(engine_play_mark(100,(unsigned long)memory+65536,65536,34)==-1&&!play_frame);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['gcc','-m32','-no-pie','-fsanitize=address,undefined','-I'+str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS 32 alternating immutable slots, one-frame backpressure, stale ACK/bounds, STOP and timeout')

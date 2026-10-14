#!/usr/bin/env python3
"""Actual adapter plus actual two-slot ownership; exercise every mode transition."""
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[3]
s=(root/'game/doom/runtime/platform/port.c').read_text();draw=s[s.index('void DG_DrawFrame(void)'):s.index('\nint doom_platform_key(')]
code=r'''
#include <assert.h>
#include <string.h>
#include <setjmp.h>
#include "game/doom/runtime/startup/checkpoint_api.h"
#define ENGINE_PLAYABLE 1
#define ENGINE_PLAY_DOUBLE 1
#define DOOM_VISIBLE 1
#define DOOM_PLAY 1
#define DOOM_DOUBLE_BUFFER 1
#define DOOM_FRAME_PROFILE 1
#define DOOM_PRESENT_TEST 1
static unsigned now;
static unsigned char doom_platform_frames[2][65536],scratch[64000],*DG_ScreenBuffer=scratch;
static struct {unsigned frames,frame_hash,palette_hash;} stats;
static struct {unsigned char r,g,b;} colors[256];
static unsigned clock_ms(void){return now+=10;}
static unsigned owner(void){return 1;}static unsigned stopping(void){return 0;}
static unsigned word(const unsigned char*p){unsigned v;memcpy(&v,p,4);return v;}
static void doom_shared_yield(void){}
void doom_shared_service(void);
#include "rtems/residentnet/engine_play.h"
static struct doom_runtime_checkpoint api;
static const struct doom_runtime_owned*owned=&api.owned;
static const struct doom_runtime_v1*io=&api.owned.io;
#include "game/doom/runtime/platform/presentation.h"
static unsigned started,startup;
static jmp_buf failure;static unsigned fail_publication;
static int publish(unsigned a,unsigned b,unsigned c,unsigned d){return fail_publication?-1:engine_play_mark(a,b,c,d);}
static void fatal(unsigned code){assert(fail_publication&&code==210);longjmp(failure,1);}
static void doom_platform_mark(unsigned a,unsigned b,unsigned c,unsigned d){(void)b;(void)c;(void)d;present_mark(a);}
void doom_shared_service(void){unsigned i;assert(play_frame!=DG_ScreenBuffer);
 for(i=0;i<64000;i++)assert(play_frame[i]==(unsigned char)play_sequence);
 assert(engine_play_control(1,play_sequence+1)==~0u);
 assert(engine_play_control(1,play_sequence)==0);
}
'''+draw+r'''
int main(void){unsigned g,i,mode;api.owned.owner=owner;api.owned.stopping=stopping;api.owned.io.ticks_ms=clock_ms;api.mark=publish;play_api=owned;play_allowed=doom_platform_frames[0];present_scratch=scratch;DG_ScreenBuffer=(present_mode(1)&2)?doom_platform_frames[0]:scratch;
 for(g=1;g<=64;g++){
  assert(DG_ScreenBuffer!=play_frame);memset(DG_ScreenBuffer,g,64000);
  for(i=37;i<=44;i++)present_mark(i);present_mark(80);present_mark(96);present_mark(98);
  DG_DrawFrame();mode=present_mode(g);assert(stats.frames==g&&play_frame==doom_platform_frames[(g-1)&1]);
  for(i=0;i<64000;i++)assert(play_frame[i]==(unsigned char)g);
  assert(word(play_frame+PRESENT_OFFSET)==PRESENT_MAGIC&&word(play_frame+PRESENT_OFFSET+12)==mode);
  assert((stats.frame_hash!=0)==!!(mode&1));
  assert(DG_ScreenBuffer==((present_mode(g+1)&2)?doom_platform_frames[g&1]:scratch));
 }
 {unsigned char*before=DG_ScreenBuffer;fail_publication=1;if(!setjmp(failure)){DG_DrawFrame();assert(0);}assert(DG_ScreenBuffer==before);}
 return 0;
}
'''
# Header names are deliberately derived from the real ABI, not a substitute.
code=code.replace('api.owned','api.base')
assert 'struct doom_runtime_owned base;' in (root/'game/doom/runtime/startup/checkpoint_api.h').read_text()
with tempfile.TemporaryDirectory() as d:
 p=Path(d)
 for config in ('#define DOOM_PRESENT_TEST 1','', '#define DOOM_NO_FNV 1','#define DOOM_DIRECT_FRAME 1','#define DOOM_NO_FNV 1\n#define DOOM_DIRECT_FRAME 1'):
  (p/'test.c').write_text(code.replace('#define DOOM_PRESENT_TEST 1',config))
  subprocess.run(['gcc','-m32','-no-pie','-fsanitize=address,undefined','-I'+str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
  subprocess.run([str(p/'test')],check=True)
print('PASS actual adapter/ownership: 320 frames, all FNV/direct modes and transitions, immutable prior slot, exact ACK, pointer rotation')

#!/usr/bin/env python3
"""Run actual WAD and framebuffer DMA code against the same modeled DMA1."""
import subprocess,tempfile
from pathlib import Path
from test_target import s,r
s=s.replace('#include "rtems/residentnet/engine_play.h"',r'''
#define WD_R(a) FD_R(a)
#define WD_S(a) FD_S(a)
#define WD_ADDR(p) FD_ADDR(p)
#define WAD_REQUEST 1
static struct {unsigned state,sequence,fragments,expected;} batch;
static unsigned char wad_stage[12288],wad_host[4096];
static unsigned owned_owner(void){return 1;}
static void exclusive_abort(void){longjmp(failed,1);}
#include "rtems/dma/wad_target.h"
#include "rtems/residentnet/engine_play.h"
''')
s=s.replace('unsigned wad_dma_isolation_snapshot(unsigned*w){(void)w;return 0;}','')
s=s.replace(' if(p==fd_desc)', ' if(p==wd_desc)return 0xc0f80200;\n if(p==wad_stage+4096)return 0xc0901000;\n if(p==fd_desc)')
s=s.replace('   if(pp_active){assert', '''   if(wd_phase==1){assert(wd_desc[0]==0&&wd_desc[1]==0x300000&&wd_desc[4]==4096&&wd_desc[5]==6);
    memcpy(wad_stage+4096,wad_host,4096);regs[0x144c/4]=addr(wd_desc);
   }else if(pp_active){assert''')
start=s.index('int main(void)')
s=s[:start]+r'''
int main(void){struct doom_runtime_owned api;unsigned i,w[17];
 memset(&api,0,sizeof api);api.owner=owner;api.stopping=stopping;api.io.ticks_ms=ticks;
 cmd[0]=2;regs[0x104c/4]=0x13ffc;memset(hosts,165,sizeof hosts);
 assert(!pp_control(8,0x101000)&&!pp_control(9,0x201000)&&!pp_control(10,1));
 play_api=&api;play_allowed=frames[0];publish(1);assert(fd_phase==1);
 frame_dma_wad_barrier();assert(fd_phase==2&&play_ack&&wd_idle());check(1);
 memset(wad_stage,165,sizeof wad_stage);for(i=0;i<4096;i++)wad_host[i]=i*31;
 wd_buffer=wad_stage;batch.state=WAD_REQUEST;batch.sequence=1;
 assert(!wd_control(1,0x300000,1)&&!wd_control(2,1,1));wd_step();
 assert(wd_phase==2&&wd_idle()&&!memcmp(wad_host,wad_stage+4096,4096));
 assert(!wd_control(5,1,1));wd_release();batch.state=0;
 assert(!wd_phase&&!wd_buffer);publish(2);pp_service();check(2);check(1);
 stop=1;play_clear();assert(!play_frame&&fd_idle());return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(s)
 subprocess.run(['gcc','-m32','-no-pie','-O1','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(r),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS real frame kick -> task drain/ACK -> real WAD read/ACK -> next frame -> STOP on one DMA1')

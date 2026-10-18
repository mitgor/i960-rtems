#!/usr/bin/env python3
"""Compile the actual target idle/rearm functions with hostile lifecycle fixtures.

Run on the Linux build host with gcc -m32. MMIO and RTEMS scheduling are mocked;
this is a policy test, not a hardware coherency or interrupt timing proof.
"""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--cc',default='gcc');p.add_argument('--keyboard-fifo',action='store_true');a=p.parse_args()
src=Path(__file__).with_name('app.c').read_text()
functions=src[src.index('static unsigned int reusable_audit('):src.index('/* PCI sideband never submits')]
preamble=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "arena.h"
#define DOOM_REUSABLE 1
#define STOP 0x504f5453u
#define ARENA_BASE 0xc0810000u
#define ENGINE_META 128u
#define ENGINE_SITES 4u
#define ENGINE_TEXT 64u
#include "lifetime.h"
static unsigned int engine_running,zone_loaned,switch_fault,control[16],switch_threads[4],switch_active[4];
static unsigned int _ISR_Nest_level,_Thread_Dispatch_disable_level,bridge[32],dma_phase,dma_completed,transport_frame;
static unsigned int live[16],wad_wire[16],wad_seq,key_seen,game_run,game_idle,engine_invoked,admitted;
static unsigned int upload_bytes,wad_ready,frame_ready,engine_text_live,engine_metadata_sha[8];
static unsigned char switch_irq_areas[4][8192],inbound[16],image[256],*image_base=image,*frame_base;
static struct arena doom_arena;
static struct arena_slot fixed_slots[7];
static struct irq_lifetime life[4];
static void *_Thread_Executing=(void*)0x1234;
static int arena_ok=1,digest_ok=1;
int arena_valid(struct arena*a){return arena_ok;}
static unsigned int regs[16];
static unsigned int*reg(unsigned addr){
 switch(addr){
 case 0xff008100:return regs;
 case 0xff008108:return regs+1;
 case 0xff00810c:return regs+2;
 case 0xff008110:return regs+3;
 case 0xff008114:return regs+4;
 case 0x1400:return regs+5;
 case 0x1410:return regs+6;
 case 0x1420:return regs+7;
 case 0x1404:return regs+8;
 case 0x140c:return regs+9;
 case 0x1424:return regs+10;
 default:assert(0);return regs;
 }}
#define REG(a) (*reg(a))
static void mask31(void){}
static void priority0(void){}
static unsigned int dma_busy_mask(void){return regs[5]|regs[6];}
static void dma_peer_check(void){}
static unsigned int dma_desc_addr(void){return 0x1000;}
static unsigned int byte_fnv(const void *p,unsigned n){const unsigned char*b=p;unsigned h=2166136261u;while(n--)h=(h^*b++)*16777619u;return h;}
static unsigned int digest_equal(const void*p,unsigned n,const void*sha){return digest_ok;}
static unsigned int little_word(const unsigned char*p){return (unsigned)p[0]|(unsigned)p[1]<<8|(unsigned)p[2]<<16|(unsigned)p[3]<<24;}
'''
checks=r'''
static void reset(void){
 memset(&doom_arena,0,sizeof doom_arena);memset(life,0,sizeof life);
 memset(switch_active,0,sizeof switch_active);memset(switch_irq_areas,0xa5,sizeof switch_irq_areas);
 memset(bridge,0,sizeof bridge);memset(control,0,sizeof control);memset(live,0,sizeof live);memset(wad_wire,0,sizeof wad_wire);
 memset(regs,0,sizeof regs);memset(fixed_slots,0,sizeof fixed_slots);
 engine_running=zone_loaned=switch_fault=_ISR_Nest_level=_Thread_Dispatch_disable_level=dma_phase=0;
 game_run=1;game_idle=engine_invoked=admitted=wad_ready=frame_ready=1;upload_bytes=144;
 transport_frame=dma_completed=65;wad_seq=wad_wire[0]=5045;live[10]=98;live[12]=key_seen=97;
 switch_threads[0]=(unsigned)_Thread_Executing;life[0].entries=life[0].returns=10;
 /* A suspended peer IRQ is allowed; it never belongs to the reloaded image. */
 switch_active[1]=life[1].live=1;life[1].entries=9;life[1].returns=8;
 live[2]=live[5]=65;live[6]=live[9]=64;
 regs[1]=0xc0000002u;regs[2]=0xffc00001u;regs[3]=0xc0400002u;regs[4]=0xffe00001u;regs[9]=0x1020;regs[10]=7;
 arena_ok=digest_ok=1;engine_text_live=byte_fnv(image,64);
 {unsigned words[4]={65,5045,2,98};memcpy(inbound,words,16);}
}
static unsigned call(unsigned run){return rearm_engine(run,16,byte_fnv(inbound,16),1);}
int main(void){unsigned i;
 reset();assert(call(0)==40&&admitted);assert(call(1)==0);
 assert(game_run==2&&!admitted&&!engine_invoked&&!upload_bytes&&!zone_loaned);
 assert(bridge[23]==98&&key_seen==98&&live[12]==98&&transport_frame==65&&dma_completed==65&&wad_seq==5045);
 assert(life[1].live&&life[1].entries==9&&life[1].returns==8);assert(call(1)==40);
 reset();assert(rearm_engine(1,16,byte_fnv(inbound,16),0)==0&&admitted&&game_run==1&&key_seen==97);
 reset();inbound[0]++;assert(call(1)==42&&admitted);
 reset();inbound[4]++;assert(call(1)==43&&admitted);
 reset();inbound[12]++;assert(call(1)==44&&admitted);
 for(i=0;i<13;i++){
  reset();switch(i){
   case 0:zone_loaned=1;break;
   case 1:doom_arena.slot[7].span=32;break;
   case 2:doom_arena.slot[0].generation++;break;
   case 3:live[5]--;break;
   case 4:dma_phase=1;break;
   case 5:regs[9]=0;break;
   case 6:life[0].live=1;break;
   case 7:switch_irq_areas[2][8191]=0;break;
   case 8:regs[3]=0xc0800002u;break;
   case 9:arena_ok=0;break;
   case 10:digest_ok=0;break;
   case 11:wad_wire[9]=0x444e4550u;break;
   case 12:control[3]=STOP;break;
  }
  assert(call(1)==45&&admitted&&engine_invoked&&game_run==1&&key_seen==97);
 }
 puts("actual rearm policy: stale identities, DMA/ACK/WAD, loan/leak, fixed pins, IRQ, cache, digest and terminal STOP rejection passed");
}
'''
if a.keyboard_fifo:
    preamble += '\n#define DOOM_KEY_FIFO_SUPPORT 1\n#include "key_fifo.h"\nstatic struct key_fifo_state keyboard;\nstatic unsigned key_wire[96];\n'
    checks=checks.replace('transport_frame=dma_completed=65;',
        'kf_init(&keyboard,key_wire,1);keyboard.cursor=key_wire[5]=97;key_wire[4]=98;transport_frame=dma_completed=65;')
    checks=checks.replace(' puts("actual rearm policy:',r'''
 reset();keyboard.mode=key_wire[14]=1;key_wire[4]=live[10]=113;
 {unsigned seq,base;for(seq=98;seq<=113;seq++){
   base=16+((seq-1)&15)*4;key_wire[base]=seq;key_wire[base+1]=1;
   key_wire[base+2]=448;key_wire[base+3]=~seq;}
  {unsigned words[4]={65,5045,2,113};memcpy(inbound,words,16);}}
 assert(rearm_engine(1,16,byte_fnv(inbound,16),0)==0&&keyboard.cursor==97&&!keyboard.discarded);
 key_wire[21]=0;
 assert(call(1)==44&&admitted&&keyboard.cursor==97&&!keyboard.discarded);
 key_wire[21]=1;
 assert(call(1)==0&&key_seen==113&&keyboard.cursor==113&&keyboard.discarded==16&&key_wire[7]==2);
 puts("actual FIFO rearm: all 16 pending old-run keys classified, corrupt descriptor rejected before mutation");
 puts("actual rearm policy:''')
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp);(path/'test.c').write_text(preamble+functions+checks)
    root=Path(__file__).resolve().parents[3]
    subprocess.run([a.cc,'-m32','-O1','-g','-fsanitize=address,undefined',
        '-I'+str(root/'loader/segmented'),'-I'+str(Path(__file__).parent),str(path/'test.c'),'-o',str(path/'test')],check=True)
    subprocess.run([str(path/'test')],check=True)

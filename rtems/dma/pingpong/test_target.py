#!/usr/bin/env python3
"""Actual opt-in target with modeled DMA registers, STOP and slot ownership."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parents[3]
s=r'''
#include <assert.h>
#include <string.h>
#include <setjmp.h>
#include "game/doom/runtime/owned/api.h"
#define ENGINE_PLAYABLE 1
#define ENGINE_PLAY_DOUBLE 1
#define ENGINE_PINGPONG 1
#define I960_DOOM_DMA 1
static unsigned regs[1536],cmd[2],stop,locked,hold,now;
static unsigned char frames[2][65536],hosts[2][73728];static jmp_buf failed;
static unsigned*reg(unsigned);static unsigned addr(const volatile void*);
#define FD_R(a) (*reg(a))
#define FD_S(a) cmd[(a)==0x1204?0:1]
#define FD_ADDR(p) addr(p)
#define FD_FATAL() longjmp(failed,1)
#define FD_LOCK() (locked=1,0)
#define FD_UNLOCK(pc) (locked=0)
static unsigned word(const unsigned char*p){unsigned v;memcpy(&v,p,4);return v;}
unsigned upload_time(void){return now/10;}
void doom_shared_service(void){}
static void doom_shared_yield(void){now+=10;}
#include "rtems/residentnet/engine_play.h"
static unsigned addr(const volatile void*p){
 if(p==fd_desc)return 0xc0f80000;
 if(p==PP_NEXT)return 0xc0f80020;
 if(p==pp_marker)return 0xc0f80100;
 if(p==frames[0])return 0xc0800000;
 if(p==frames[1])return 0xc0810000;
 assert(0);return 0;
}
static unsigned*reg(unsigned a){
 if(a==0x1444&&regs[0x1440/4]){
  if(hold)regs[a/4]=0x400;
  else{
   if(pp_active){assert(fd_desc[0]==addr(PP_NEXT)&&fd_desc[1]==pp_bus[pp_slot]&&fd_desc[4]==65536);
   assert(PP_NEXT[0]==0&&PP_NEXT[1]==pp_bus[pp_slot]+69600&&PP_NEXT[4]==32);
   memcpy(hosts[pp_slot]+4096,play_frame,65536);memcpy(hosts[pp_slot]+73696,(const void*)pp_marker,32);
   regs[0x144c/4]=addr(PP_NEXT);}
   else{assert(fd_desc[0]==0);memcpy(hosts[0]+4096,play_frame,65536);regs[0x144c/4]=addr(fd_desc);}
   regs[0x1450/4]=regs[0x1460/4]=regs[a/4]=0;regs[0x1464/4]=7;
  }
 }return regs+a/4;
}
static unsigned runtime_error;
#define PP_AUDIT_LOCK() (locked=1,0)
#define PP_AUDIT_UNLOCK(pc) (locked=0)
static void engine_snapshot(unsigned*w){unsigned i;assert(locked);memset(w,0,16*4);for(i=0;i<6;i++)w[i]=regs[(0x1400+(i/2)*64+(i%2)*4)/4];w[6]=cmd[0];}
#include "rtems/dma/pingpong/audit_report.h"
static unsigned owner(void){return 1;}
static unsigned stopping(void){return stop;}
static unsigned ticks(void){return now;}
static void publish(unsigned g){unsigned i,slot=(g-1)&1;
 for(i=0;i<65536;i++)frames[slot][i]=(i*13)^(i>>8)^(g*37);
 assert(engine_play_mark(100,(unsigned)frames[slot],65536,g)==1);
}
static void check(unsigned g){unsigned i,slot=(g-1)&1,*m=(unsigned*)(hosts[slot]+73696);
 assert(m[0]==PP_MAGIC&&m[1]==g&&m[2]==slot&&m[6]==~g&&m[7]==g);
 for(i=0;i<65536;i++)assert(hosts[slot][4096+i]==(unsigned char)((i*13)^(i>>8)^(g*37)));
 for(i=0;i<4096;i++)assert(hosts[slot][i]==165);
 for(i=69632;i<73696;i++)assert(hosts[slot][i]==165);
}
int main(void){struct doom_runtime_owned api;unsigned i,w[17],old;
 memset(&api,0,sizeof api);api.owner=owner;api.stopping=stopping;api.io.ticks_ms=ticks;
 cmd[0]=2;regs[0x104c/4]=0x13ffc;memset(hosts,165,sizeof hosts);
 assert(!engine_play_control(8,0x101000));assert(engine_play_control(9,0x102000)==~0u);
 assert(!engine_play_control(9,0x201000));
 /* The opt-in build must still service host-started DMA before activation. */
 play_api=&api;play_allowed=frames[0];publish(1);
 assert(!engine_play_control(6,1)&&!engine_play_control(3,0x101000)&&!engine_play_control(4,1));
 pp_service();assert(fd_phase==2&&!play_ack);assert(!engine_play_control(1,1));play_clear();play_sequence=0;fd_report[2]=0;
 assert(!engine_play_control(10,1));
 assert(engine_play_control(10,1)==~0u);play_api=&api;play_allowed=frames[0];
 publish(1);assert(fd_phase==1&&fd_stage==7&&!play_ack);
 /* Full system report recognizes only the exact owned lease. */
 pp_engine_report(w);assert(!locked&&!w[16]&&!w[2]&&w[6]==2&&pp_system_audits==1);
 old=PP_NEXT[1];PP_NEXT[1]^=1;pp_engine_report(w);assert(w[16]==256&&w[2]==1);PP_NEXT[1]=old;runtime_error=0;
 regs[0x1400/4]=1;pp_engine_report(w);assert(w[16]==256&&w[0]==1);regs[0x1400/4]=0;runtime_error=0;
 /* ISR peer checks the exact two-descriptor lease without mutating global state. */
 memset(w,0,sizeof w);w[2]=1;w[6]=6;assert(frame_dma_isolation_snapshot(w));
 for(i=0;i<8;i++){old=PP_NEXT[i];PP_NEXT[i]^=1;w[2]=1;w[6]=6;assert(!frame_dma_isolation_snapshot(w));PP_NEXT[i]=old;}
 pp_service();check(1);assert(play_ack&&fd_phase==2);publish(2);pp_service();check(2);
 publish(3);assert(fd_phase==2&&!play_ack);for(i=0;i<100;i++)pp_service();check(1);check(2);assert(pp_stalls>=100);
 assert(engine_play_control(11,3)==~0u);assert(!engine_play_control(11,1));assert(engine_play_control(11,1)==~0u);
 pp_service();assert(fd_phase==1);pp_service();check(3);check(2);
 assert(!engine_play_control(11,2));publish(4);assert(fd_phase==1);
 /* STOP after kick must finish DMA in task context before clearing the source pin. */
 stop=1;play_clear();assert(fd_phase==2&&!play_frame);check(4);assert(!locked);
 /* A stalled consumer hits the existing bounded wait; neither host slot changes. */
 stop=0;play_sequence=4;play_ack=1;play_frame=frames[1];publish(5);
 assert(fd_phase==2&&!play_ack);assert(play_wait()==-1&&!play_frame);check(3);check(4);
 /* Bounded DMA timeout quarantines instead of releasing the source. */
 stop=0;assert(!engine_play_control(11,3));play_sequence=4;play_ack=1;play_frame=frames[1];publish(5);hold=1;
 if(!setjmp(failed)){fd_step();assert(0);}assert(fd_phase==1&&play_frame&&fd_report[13]==5);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(s)
 subprocess.run(['gcc','-m32','-no-pie','-O1','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(r),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS actual target: chained DMA, independent slots, stalls, stale/duplicate release, STOP quiescence, stalled-consumer bound, timeout quarantine, exact lease tampering')

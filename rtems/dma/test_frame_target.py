#!/usr/bin/env python3
"""Actual play pin and DMA state machine: native modeled register effects."""
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
code=r'''
#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include "game/doom/runtime/owned/api.h"
#define ENGINE_PLAYABLE 1
#define I960_DOOM_DMA 1
static unsigned regs[0x1800/4],cmd[2],stop,mode,writes,locked,inject;
static unsigned lock(void);static void unlock(unsigned);
#define FD_LOCK() lock()
#define FD_UNLOCK(pc) unlock(pc)
static unsigned char memory[65536],host[65536];static jmp_buf failed;
static unsigned*reg(unsigned);
static unsigned addr(const volatile void*);
#define FD_R(a) (*reg(a))
#define FD_S(a) cmd[(a)==0x1204?0:1]
#define FD_ADDR(p) addr(p)
#define FD_FATAL() longjmp(failed,1)
static unsigned word(const unsigned char*p){unsigned v;memcpy(&v,p,4);return v;}
static void doom_shared_yield(void){}
void doom_shared_service(void){}
#include "rtems/residentnet/engine_play.h"
static unsigned lock(void){if(inject==1){inject=0;assert(!engine_play_control(4,1));}assert(!locked);locked=1;return 20u<<16;}
static void unlock(unsigned pc){assert(locked&&pc==(20u<<16));locked=0;if(inject==2){inject=0;assert(engine_play_control(4,1)==~0u);}}
static unsigned addr(const volatile void*p){return p==(const volatile void*)fd_desc?0xc0f80000:0xc0800000;}
static unsigned*reg(unsigned a){assert(a!=0x1448);
 if(a==0x1444&&regs[0x1440/4]){
  writes++;if(mode==1)regs[a/4]=0x400;else if(mode==2)regs[a/4]=8;
  else {assert(fd_desc[0]==0&&fd_desc[1]==0x101000&&fd_desc[2]==0&&fd_desc[3]==0xc0800000&&fd_desc[4]==65536&&fd_desc[5]==7);
   memcpy(host,memory,65536);regs[0x144c/4]=addr(fd_desc);regs[0x1450/4]=regs[0x1460/4]=regs[a/4]=0;regs[0x1464/4]=7;
   if(mode==3)memory[555]^=1;
   if(mode==4)fd_desc[6]^=1;
   if(mode==5)stop=1;
  }
 }return regs+a/4;
}
static unsigned isolation_words[16];
static void engine_snapshot(unsigned *w){memcpy(w,isolation_words,sizeof isolation_words);}
#define EREG(a) FD_R(a)
#define ESHORT(a) FD_S(a)
#include "rtems/residentnet/scsi_target.h"
static void isolation_test(void){unsigned w[16],saved[8],i,j,old;
 for(i=0;i<8;i++)saved[i]=fd_desc[i];
 /* Simulate a scheduled peer at every published DMA transition. */
 fd_phase=1;play_ack=0;
 for(i=4;i<=10;i++){
  fd_stage=i;memset(w,0,sizeof w);w[2]=i>=6&&i<=9;w[3]=w[2]?0x400:0;w[6]=i==4?2:6;w[8]=0x242;w[9]=0x13ffc;
  memcpy(isolation_words,w,sizeof w);scsi_stop.verified=1;scsi_stop.before=0x202;
  assert(scsi_target_verified());
  assert(frame_dma_isolation_snapshot(w));assert(!scsi_stop_postcheck(w,0x202));
 }
 fd_stage=7;
 for(i=0;i<8;i++)for(j=0;j<32;j++){
  fd_desc[i]=saved[i]^(1u<<j);memset(w,0,sizeof w);w[2]=1;w[6]=6;
  assert(!frame_dma_isolation_snapshot(w));fd_desc[i]=saved[i];
 }
 for(i=0;i<7;i++)for(j=0;j<32;j++){
  memset(w,0,sizeof w);w[2]=1;w[6]=6;w[8]=0x242;w[9]=0x13ffc;
  w[i]^=1u<<j;
  /* CSR active and channel1 enable are the only intentional variables. */
  if(i==3&&j==10)continue;
  assert(!frame_dma_isolation_snapshot(w));
 }
 for(i=7;i<12;i++){if(i==10)continue;memset(w,0,sizeof w);w[2]=1;w[6]=6;w[8]=0x242;w[9]=0x13ffc;
  w[i]^=i==7?2:i==8?0x40:i==9?4:1;
  assert(frame_dma_isolation_snapshot(w)&&scsi_stop_postcheck(w,0x202));
 }
 old=fd_phase;fd_phase=2;assert(!frame_dma_isolation_snapshot(w));fd_phase=old;
 old=play_sequence;play_sequence++;assert(!frame_dma_isolation_snapshot(w));play_sequence=old;
 play_ack=1;assert(!frame_dma_isolation_snapshot(w));play_ack=0;
 fd_stage=13;fd_phase=2;
}
static unsigned stopping(void){return stop;}
static unsigned crc(const unsigned char*p){unsigned c=~0u,i,j;for(i=0;i<65536;i++){c^=p[i];for(j=0;j<8;j++)c=(c>>1)^(0xedb88320u&-(c&1));}return ~c;}
static void reset(void){unsigned i;static struct doom_runtime_owned a;memset(&a,0,sizeof a);a.stopping=stopping;play_api=&a;
 memset(regs,0,sizeof regs);memset(fd_report,0,sizeof fd_report);cmd[0]=2;cmd[1]=0;regs[0x104c/4]=0x13ffc;stop=mode=writes=fd_phase=fd_destination=locked=inject=fd_isolation_checks=fd_no_crc=0;
 play_frame=play_allowed=memory;play_sequence=1;play_ack=0;for(i=0;i<65536;i++)memory[i]=(i*7)^(i>>8);
}
static void submit(void){assert(!engine_play_control(3,0x101000));assert(!engine_play_control(4,1));assert(fd_phase==1&&!writes);
 assert(engine_play_control(1,1)==~0u&&!play_ack);assert(engine_play_control(3,0x102000)==~0u);assert(engine_play_control(4,1)==~0u);
}
int main(void){unsigned i;
 reset();assert(engine_play_control(4,1)==~0u);assert(engine_play_control(3,0xfffffff0)==~0u);assert(engine_play_control(5,16)==0);
 submit();fd_step();assert(fd_phase==2&&writes&&cmd[0]==2&&!regs[0x1440/4]);assert(!memcmp(memory,host,65536));isolation_test();assert(fd_report[5]==crc(memory)&&fd_report[6]==crc(host));
 assert(engine_play_control(4,1)==~0u);assert(!engine_play_control(1,1)&&play_ack);
 for(i=1;i<=4;i++){reset();submit();mode=i;if(!setjmp(failed)){fd_step();assert(0);}assert(fd_phase==1&&play_frame&&fd_report[13]&&cmd[0]==2&&!play_ack);}
 reset();submit();stop=1;if(!setjmp(failed)){fd_step();assert(0);}assert(!writes&&play_frame&&fd_phase==1);
 reset();submit();mode=5;fd_step();assert(stop&&fd_phase==2&&play_frame&&!play_ack);
 reset();submit();if(!setjmp(failed)){play_clear();assert(0);}assert(play_frame&&fd_phase==1);
 reset();assert(!engine_play_control(3,0x101000));inject=1;if(!setjmp(failed)){play_clear();assert(0);}assert(locked&&play_frame&&fd_phase==1);
 reset();assert(!engine_play_control(3,0x101000));inject=2;play_clear();assert(!locked&&!play_frame&&!fd_phase&&!inject);
 reset();assert(!engine_play_control(6,1));submit();assert(engine_play_control(6,0)==~0u);fd_step();assert(fd_report[14]==1&&!fd_report[5]&&!fd_report[6]&&fd_phase==2);
 reset();assert(engine_play_control(6,2)==~0u);
 reset();regs[0x1400/4]=1;submit();if(!setjmp(failed)){fd_step();assert(0);}assert(!writes&&play_frame);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code);subprocess.run(['cc','-std=c99','-Wall','-Wextra','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(root),str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
print('PASS actual atomic frame release, interrupt-boundary submission, frame pin, pending ACK/mutation refusal, exact DMA, independent CRC, stale generation, STOP, timeout/error/source/descriptor quarantine')

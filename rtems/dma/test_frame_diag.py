#!/usr/bin/env python3
"""Execute actual failure-only diagnostic helper against modeled MMIO."""
import subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include <stdint.h>
struct blob{void*data;unsigned size;};
struct experiment{unsigned char*bar;unsigned frame_dma_fault[100];struct blob frame_dma_fault_blob;unsigned mu_failed,ready;};
static unsigned regs[16],now,mode,word_index,writes,sleeps;
#define jiffies now
#define msecs_to_jiffies(n) (n)
#define time_after_eq(a,b) ((a)>=(b))
#define ODB 0x2c
#define record(...) ((void)0)
#define debugfs_create_blob(...) ((void)0)
static void usleep_range(unsigned a,unsigned b){assert(a==50&&b==100);now++;sleeps++;}
static void writel(unsigned v,void*p){assert(p==&regs[5]&&(v&0xff00ffff)==0x9100002a);word_index=(v>>16)&255;assert(word_index<96);writes++;regs[5]=v;}
static unsigned readl(void*p){unsigned off=((unsigned*)p-regs)*4;
 if(off==0x14)return mode==1?regs[5]:0;
 if(off==0x1c)return 0x9200002a|(word_index<<16);
 if(off==0x18)return word_index==0?(mode==2?0x31525845:0x31464d4e):word_index==1?(mode==3?43:42):word_index*7;
 if(off==0x28)return mode==4?0:0x1fb;
 if(off==0x34)return 0xff;
 if(off==ODB)return mode==5?1:0;
 assert(0);return 0;
}
#include "frame_diag_host.h"
int main(void){unsigned m,i;for(m=0;m<6;m++){
 struct experiment d={0};d.bar=(unsigned char*)regs;d.mu_failed=1;mode=m;now=writes=sleeps=0;
 frame_dma_terminal(&d,42);assert(d.mu_failed==1&&d.ready==0&&d.frame_dma_fault[0]==0x31464446&&d.frame_dma_fault[1]==42);
 assert(d.frame_dma_fault_blob.data==d.frame_dma_fault&&d.frame_dma_fault_blob.size==400);
 if(!m){assert(writes==96&&d.frame_dma_fault[2]==96&&!d.frame_dma_fault[3]);for(i=2;i<96;i++)assert(d.frame_dma_fault[4+i]==i*7);}
 else {assert(d.frame_dma_fault[3]&&writes<=2&&sleeps<=2000);if(m==1)assert(writes==1&&sleeps==2000);}
}return 0;}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code);subprocess.run(['cc','-fsanitize=address,undefined','-I'+str(here),str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
print('PASS diagnostic helper: exact frozen 96-word report, wrong magic/epoch, mask/doorbell, bounded silence; poison retained, only read-request writes')

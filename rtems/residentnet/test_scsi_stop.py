#!/usr/bin/env python3
"""Simulated exact stop sequence: no claim of physical SCSI reset success."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
static unsigned int regs[16],writes,mode,snapshots;
static void snapshot(unsigned int*w){memcpy(w,regs,sizeof(regs));snapshots++;if(mode==3&&snapshots>1&&snapshots%3==0)w[7]=2;}
static unsigned int read16(unsigned int a){assert(a==0x103e);return regs[8];}
static unsigned int read32(unsigned int a){assert(a==0x104c);return regs[9];}
static void write16(unsigned int a,unsigned int v){assert(a==0x103e&&v&0x40&&!(v&0x400));writes++;if(mode!=1)regs[8]=v;if(mode!=2)regs[7]=0;regs[9]=0;}
static void write32(unsigned int a,unsigned int v){assert(a==0x104c&&(v&0x13ffc)==0x13ffc);writes++;regs[9]=v;}
#define SCSI_STOP_SNAPSHOT snapshot
#define SCSI_STOP_READ16 read16
#define SCSI_STOP_READ32 read32
#define SCSI_STOP_WRITE16 write16
#define SCSI_STOP_WRITE32 write32
#include "scsi_stop.h"
static void init(void){memset(regs,0,sizeof(regs));regs[6]=2;regs[7]=18;regs[8]=0x602;regs[9]=0x13ffc;writes=snapshots=mode=0;}
int main(void){struct scsi_stop_state s;unsigned int i,j,checks=0,w[16];
 init();memset(&s,0,sizeof(s));assert(scsi_stop_hold(&s,0)==1&&!writes&&!s.written);
 for(i=0;i<6;i++)for(j=0;j<32;j++){init();regs[i]=1u<<j;memset(&s,0,sizeof(s));assert(scsi_stop_hold(&s,0x31504353)==2&&!writes&&!s.written);checks++;}
 init();memset(&s,0,sizeof(s));assert(!scsi_stop_hold(&s,0x31504353)&&s.written&&s.verified&&s.polls==3&&writes==2);
 assert(scsi_stop_hold(&s,0x31504353)==5&&writes==2);
 memcpy(w,regs,sizeof(w));for(i=0;i<6;i++)for(j=0;j<32;j++){w[i]=1u<<j;assert(scsi_stop_postcheck(w,s.before));w[i]=0;checks++;}
 for(j=1;j<=3;j++){init();mode=j;memset(&s,0,sizeof(s));assert(scsi_stop_hold(&s,0x31504353)==6&&s.written&&!s.verified&&s.polls==4096&&writes==2);}
 init();regs[11]=1;memset(&s,0,sizeof(s));assert(scsi_stop_hold(&s,0x31504353)==4&&!writes);
 assert(checks==384);
 puts("384 DMA bit faults rejected; unknown topology/NMI denied; W1C preserved; 3 stable snapshots required; 3 bounded failures retain reset; repeated entry denied");
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'stop.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)

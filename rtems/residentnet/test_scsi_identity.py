#!/usr/bin/env python3
"""Actual target identity adapter with simulated fixed registers."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned int addresses[]={0xc011e22c,0xc0060000,0xc01107d8,0xc0083104,0xc0083108,0xc008302c,0xc0083030,0xc0083038,0xc008303c,0xc0083040,0x1298,0x1700,0x12a8,0x12b0};
static unsigned int values[]={0xc0110780,1,1,0x000c1000,2,0x88000000,0xfff00000,0x88002000,0,0x10,0x16,0,0x1000c,0x000c1000};
static unsigned int*reg(unsigned int a){unsigned int i;for(i=0;i<14;i++)if(addresses[i]==a)return &values[i];assert(0);return 0;}
#define EREG(a) (*reg(a))
#define ESHORT(a) (*(unsigned short*)reg(a))
static void engine_snapshot(unsigned int*w){memset(w,0,64);}
#include "scsi_target.h"
int main(void){unsigned int i,j,n=0;
 assert(scsi_target_identity()&&values[12]==0x1000c);
 for(i=0;i<10;i++)for(j=0;j<(i==4?16:32);j++){values[i]^=1u<<j;assert(!scsi_target_identity());values[i]^=1u<<j;n++;}
 for(j=0;j<32;j++){values[13]^=1u<<j;assert(!scsi_target_identity()&&values[12]==0x1000c);values[13]^=1u<<j;n++;}
 values[11]=1;assert(!scsi_target_identity());values[11]=0;
 values[10]=2;assert(!scsi_target_identity());values[10]=0x16;
 assert(scsi_target_identity()&&!scsi_stop.written&&!scsi_target_verified());
 printf("%u metadata/config identity bit faults rejected; selector restored after mismatch; no reset writes from identity reads\n",n);
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'identity.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

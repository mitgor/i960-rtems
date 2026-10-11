#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned int memory[65536],mask=65535,bad=~0u,flipped,boundary=1,writes;
static unsigned int indexof(unsigned int a){assert(a>=0xc0200000u&&a<0xc0240000u&&!(a&3));return (a-0xc0200000u)/4;}
static unsigned int readword(unsigned int a){unsigned int i=indexof(a);return memory[i&mask]^(i==bad?flipped:0);}
static void writeword(unsigned int a,unsigned int v){memory[indexof(a)&mask]=v;writes++;}
#define RP_READ readword
#define RP_WRITE writeword
#define RP_SYNC() ((void)0)
#define RP_BOUNDARY() boundary
#include "ram_probe.h"
int main(void){struct ram_probe_report r;unsigned int i;
 assert(ram_probe_run(&r,0)==1&&!writes);
 assert(!ram_probe_run(&r,1)&&r.passes==4&&r.checked==262144);
 for(i=0;i<16;i++){mask=65535^(1u<<i);assert(ram_probe_run(&r,1)==2);}mask=65535;
 for(i=0;i<32;i++){bad=32768;flipped=1u<<i;assert(ram_probe_run(&r,1)==2&&r.address==0xc0220000u);}bad=~0u;
 boundary=0;assert(ram_probe_run(&r,1)==3&&!r.passes);
 puts("Actual fixed 256 KiB probe: four patterns; 16 alias bits, 32 data faults, changed boundary and missing admission rejected");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'probe.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

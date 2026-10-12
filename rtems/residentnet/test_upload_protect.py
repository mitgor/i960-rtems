#!/usr/bin/env python3
"""Exercise actual protected-page code against a modeled 16 MiB DRAM map."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parent
s=(r/'upload_protect.c').read_text().replace('#define R(a) (*(volatile unsigned int*)(a))','#define R(a) mem[((a)-0xc0000000u)/4]')
s=s.replace('(unsigned int)upload_code_start','0xc0f94000u').replace('(unsigned int)upload_code_end','0xc0f95880u')
prefix='''#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#define I960_RESIDENT_UPLOAD 1
static unsigned int mem[4194304],polls;
void exclusive_drain_poll(void){polls++;}
'''
main='''int main(int argc,char**argv){unsigned int targets[]={0xc0f2c000,0xc0f94000,0xc0f9bff0,0xc0f9c000,0xc0fac000,0xc0fe8000,0xc0fffffc};unsigned int i,w[6],mode=atoi(argv[1]);
 for(i=0;i<4194304;i++)mem[i]=i*17;upload_protect_init();assert(upload_protect_all());upload_protect_report(w);assert(w[0]==135&&w[2]==0);
 if(mode<7){R(targets[mode])^=1;assert(!upload_protect_all());upload_protect_report(w);assert(w[2]==2&&w[3]<=targets[mode]&&targets[mode]-w[3]<4096);}
 else{R(0xc0f4c010)^=1;assert(upload_protect_finish());assert(polls==135);}
 return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.c').write_text(prefix+s+main)
 subprocess.run(['cc','-O2','-fsanitize=address,undefined','-I'+str(r),str(p/'test.c'),'-o',str(p/'test')],check=True)
 for mode in range(8):subprocess.run([str(p/'test'),str(mode)],check=True)
print('PASS protected pages: immutable monitor, stage two, BIO, saved tail, cache descriptors, DRAM top; mutable exclusion and drain polls')

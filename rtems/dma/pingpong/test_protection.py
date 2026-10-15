#!/usr/bin/env python3
"""Actual protection table: all 145 pages, corruption and old-capacity refusal."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parents[3]
s=r'''
#include <assert.h>
#include <sys/mman.h>
#include <string.h>
#define I960_RESIDENT_UPLOAD 1
#define I960_DOOM_ENGINE 1
void exclusive_drain_poll(void){}
__asm__(".globl upload_code_start,upload_code_end,engine_code_start,engine_code_end\n"
 "upload_code_start=0xc0f94000\nupload_code_end=0xc0f9ae90\nengine_code_start=0xc0f8c000\nengine_code_end=0xc0f90120\n");
#include "rtems/residentnet/upload_protect.c"
int main(void){unsigned w[6],i;
 assert(mmap((void*)0xc0f2c000,0xd4000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0xc0f2c000);
 upload_protect_init();upload_protect_report(w);
#ifdef I960_PINGPONG
 assert(w[0]==145&&w[2]==0&&upload_protect_all());
 for(i=0;i<count;i++){unsigned a=addresses[i];R(a)^=1;error=0;next=i;assert(!upload_protect_step()&&error==2&&bad==a);R(a)^=1;error=0;assert(upload_protect_all());}
#else
 assert(w[0]==144&&w[2]==1&&!upload_protect_all());
#endif
 return 0;}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(s)
 for flags in ([],['-DI960_PINGPONG']):
  subprocess.run(['gcc','-m32','-no-pie','-fno-pie','-O1','-I'+str(r),*flags,str(p/'test.c'),'-o',str(p/'test')],check=True)
  subprocess.run([str(p/'test')],check=True)
print('PASS protection capacity: legacy rejects page 145; expanded table detects mutation in every protected page')

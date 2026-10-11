#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include "ram_transfer.h"
#include "ram.h"
int main(void){struct ram_transfer_evidence e={0x31504353,1,1,1,1,1,1,1};unsigned int *p=(unsigned int*)&e,i,j,n;
 assert(ram_transfer_range(&e,0xc0200040,0x3ff80));
 for(i=0;i<8;i++)for(j=0;j<32;j++){p[i]^=1u<<j;assert(!ram_transfer_range(&e,0xc0200040,4));p[i]^=1u<<j;}
 for(n=0;n<0x40080;n++){
  unsigned int expected=n>=0x40&&n<0x3ffc0;
  assert(ram_transfer_range(&e,0xc0200000+n,1)==expected);
 }
 assert(!ram_transfer_range(&e,0xc0200040,0));
 assert(!ram_transfer_range(&e,0xc0200040,0xffffffff));
 assert(!ram_transfer_range(&e,0xffffffff,4));
 assert(!ram_transfer_range(&e,0xc0200040,0x3ff81));
 assert(!ram_reclaim(0xc0200040,4)); /* live grant MUST remain closed */
 assert(ram_owned(0xc0f4c010,4));
 puts("256 missing/corrupt proof bits rejected; all candidate byte boundaries checked; zero/overflow/guards denied; live external RAM grant remains closed");}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'ram.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
code='''#include <assert.h>
#include <stdio.h>
#include "board.h"
#include "ram.h"
int main(void){unsigned int w[7]={6,0xc0110780,0xc000d540,0xc004fc40,0x1000000,0xc0f2c000,0x80000},i,j;
 assert(!resident_board_admit(w));
 for(i=0;i<7;i++)for(j=0;j<32;j++){w[i]^=1u<<j;assert(resident_board_admit(w));w[i]^=1u<<j;}
 assert(!ram_reclaim(0xc0fac000,0x3c000));
 puts("224 identity bit flips rejected; adjacent firmware cache cannot be reclaimed");}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-I',str(root),'-fsanitize=address,undefined',str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

#!/usr/bin/env python3
"""Exercise actual fault table installation, readback and corruption rejection."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
static unsigned int table[64],writes,fail=~0u;
static unsigned int readword(unsigned int a){assert(a>=0xc0000800u&&a<0xc0000900u&&!(a&3));return table[(a-0xc0000800u)/4];}
static void writeword(unsigned int a,unsigned int v){unsigned int i=(a-0xc0000800u)/4;assert(i<64);writes++;if(i!=fail)table[i]=v;}
#define FO_READ readword
#define FO_WRITE writeword
#include "fault_owner.h"
int main(void){unsigned int i,j;
 assert(fault_table_install(0xc0f30001)==1&&!writes);
 assert(!fault_table_install(0xc0f30000)&&writes==64&&fault_table_valid(0xc0f30000));
 for(i=0;i<64;i++)for(j=0;j<32;j++){table[i]^=1u<<j;assert(!fault_table_valid(0xc0f30000));table[i]^=1u<<j;}
 for(i=0;i<64;i++){table[i]^=1;fail=i;assert(fault_table_install(0xc0f30000)==2);fail=~0u;assert(!fault_table_install(0xc0f30000));}
 puts("Actual table installer: 2048 corruption bits and 64 failed writes rejected; local entries reserved words zero");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'fault.c';p.write_text(code);exe=p.with_suffix('')
 subprocess.run(['cc','-fsanitize=address,undefined','-I',str(root),str(p),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

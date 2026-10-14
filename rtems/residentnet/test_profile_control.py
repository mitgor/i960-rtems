#!/usr/bin/env python3
"""Execute actual upload ioctl allowlist; timing must not expose DMA writes."""
import subprocess,tempfile
from pathlib import Path
s=Path(__file__).with_name('upload_host.h').read_text();a=s.index(' if(op==10){if(');b=s.index('\n if(op==9||op==11)',a)
code='''#include <assert.h>
#include <errno.h>
#define I960_DOOM_DMA 1
static int check(unsigned index,unsigned value,unsigned reserved){unsigned w[264]={0},op=10,i;int rc=0;w[8]=index;w[9]=value;w[10]=reserved;
'''+s[a:b]+'''
free:return rc;}
int main(void){unsigned i;for(i=0;i<5;i++)assert(!check(7,i,0));assert(check(7,5,0)==-EINVAL);assert(check(7,0,1)==-EINVAL);assert(check(3,0x100000,0)==-EINVAL);assert(check(4,1,0)==-EINVAL);assert(check(6,1,0)==-EINVAL);assert(check(255,0,0)==-EINVAL);assert(!check(5,16,0));assert(!check(0,0,0));assert(check(0,1,0)==-EINVAL);return 0;}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(code);subprocess.run(['gcc',str(p/'t.c'),'-o',str(p/'t')],check=True);subprocess.run([str(p/'t')],check=True)
print('PASS actual ioctl allowlist: five read-only timing words; addresses/submissions/CRC control/invalid indices/reserved words refused')

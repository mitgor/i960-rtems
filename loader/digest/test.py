#!/usr/bin/env python3
"""Independent SHA256 vectors, padding/chunk boundaries and bounded length."""
import hashlib,subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
source='''#include <assert.h>
#include <stdio.h>
#include "sha256.h"
int main(void){struct sha256 s;unsigned char p[127],out[32];unsigned n;sha256_init(&s);while((n=fread(p,1,sizeof p,stdin)))assert(sha256_update(&s,p,n));sha256_finish(&s,out);assert(fwrite(out,1,32,stdout)==32);s.bytes=0x1fffffff;assert(!sha256_update(&s,p,1));return 0;}
'''
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);(t/'test.c').write_text(source);subprocess.run(['cc','-std=c99','-fsanitize=address,undefined','-I'+str(r),str(t/'test.c'),str(r/'sha256.c'),'-o',str(t/'test')],check=True)
 for n in (0,1,3,55,56,63,64,65,127,128,129,1024,52452,430580):
  data=(bytes(i%251 for i in range(n)));assert subprocess.check_output([str(t/'test')],input=data)==hashlib.sha256(data).digest()
print('PASS SHA256: independent vectors, padding/chunk boundaries, manifest-sized data, length overflow refusal')

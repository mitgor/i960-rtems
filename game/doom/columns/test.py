#!/usr/bin/env python3
"""32-bit ASan/UBSan kernel oracle and generated-vector freshness check."""
from pathlib import Path
import subprocess,tempfile
r=Path(__file__).resolve().parent
before=(r/'vectors.h').read_bytes()
subprocess.run(['python3',str(r/'generate_vectors.py')],check=True)
assert before==(r/'vectors.h').read_bytes()
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'main.c').write_text('''
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "column.h"
#include "../bounded_column.h"
void doom_platform_safe(void){}
static unsigned rng=17657;
static unsigned next(void){rng=rng*1664525u+1013904223u;return rng;}
int main(void){
 unsigned char *a=malloc(64032),*b=malloc(64032),src[256],map[256];
 unsigned t,i,frac;struct doom_column_job j;
 assert(doom_column_selftest() && doom_column_cases==96);
 for(i=0;i<256;i++){src[i]=next();map[i]=next();}
 j.source=src;j.map=map;
 for(t=0;t<10000;t++){
  memset(a,165,64032);memset(b,165,64032);
  j.dst=a+16;j.dst2=(t&1)?a+23:0;j.count=next()%201;
  j.frac=next();j.step=next();j.post_length=(int)(next()%257)-1;
  frac=j.frac;
  for(i=0;i<j.count;i++){
   unsigned char v=map[src[R_ColumnIndex((int)frac,j.post_length,1)]];
   b[16+320*i]=v;if(j.dst2)b[23+320*i]=v;frac+=j.step;
  }
  doom_column_c(&j);assert(!memcmp(a,b,64032));
 }
 free(a);free(b);return 0;
}
''')
 subprocess.run(['gcc','-m32','-no-pie','-std=gnu99','-O2','-fsanitize=address,undefined','-I'+str(r),str(p/'main.c'),str(r/'column.c'),str(r/'selftest.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS 96 Python vectors and 10000 randomized guarded comparisons to original index semantics')

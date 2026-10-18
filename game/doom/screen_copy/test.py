#!/usr/bin/env python3
"""Exact fixed-size presentation copy under address/undefined sanitizers."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[3]
s=r'''
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "game/doom/screen_copy/HEADER"
int main(void){unsigned a,b,i,k;unsigned char *s,*d;
 for(a=0;a<8;a++)for(b=0;b<8;b++)for(k=0;k<4;k++){
  s=malloc(64000+a);d=malloc(64000+b);assert(s&&d);
  for(i=0;i<64000+a;i++)s[i]=(i*37+(i>>8)+k*61);
  memset(d,0xa5,64000+b);doom_screen_copy(d+b,s+a);
  for(i=0;i<b;i++)assert(d[i]==0xa5);
  for(i=0;i<64000;i++)assert(d[b+i]==(unsigned char)((i+a)*37+((i+a)>>8)+k*61));
  for(i=0;i<64000+a;i++)assert(s[i]==(unsigned char)(i*37+(i>>8)+k*61));
  free(s);free(d);
 }return 0;}
'''
with tempfile.TemporaryDirectory() as t:
 p=Path(t)
 for header in ('copy.h','wide.h'):
  (p/'test.c').write_text(s.replace('HEADER',header))
  subprocess.run(['cc','-std=c99','-Os','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
  subprocess.run([str(p/'test')],check=True)
print('PASS: both 64,000-byte copies, all 64 byte alignments, source unchanged, prefix guards intact')

#!/usr/bin/env python3
"""Test the actual pinned Newlib speed paths with sanitizers on Linux host32."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--newlib',type=Path,required=True);a=p.parse_args()
s=r'''
#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
void *fast_memcpy(void*,const void*,size_t);void *fast_memset(void*,int,size_t);
int main(void){unsigned n,a,b,i,c;unsigned char src[4160],dst[4160];
 for(i=0;i<sizeof(src);i++)src[i]=(unsigned char)(i*17);
 for(n=0;n<=4096;n++)for(a=0;a<8;a++)for(b=0;b<8;b++){
  for(i=0;i<sizeof(dst);i++)dst[i]=165;
  assert(fast_memcpy(dst+16+a,src+16+b,n)==dst+16+a);
  for(i=0;i<sizeof(dst);i++)assert(dst[i]==(i>=16+a&&i<16+a+n?src[16+b+i-16-a]:165));
 }
 for(c=0;c<256;c++)for(a=0;a<8;a++)for(n=0;n<=1024;n++){
  for(i=0;i<sizeof(dst);i++)dst[i]=165;
  assert(fast_memset(dst+16+a,c,n)==dst+16+a);
  for(i=0;i<sizeof(dst);i++)assert(dst[i]==(i>=16+a&&i<16+a+n?c:165));
 }
 long page=sysconf(_SC_PAGESIZE);unsigned char*x=mmap(0,page*3,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0),*y=mmap(0,page*3,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
 assert(x!=MAP_FAILED&&y!=MAP_FAILED);assert(!mprotect(x+page,page,PROT_READ|PROT_WRITE)&&!mprotect(y+page,page,PROT_READ|PROT_WRITE));
 for(n=0;n<=4096;n++){fast_memset(x+2*page-n,42,n);fast_memcpy(y+2*page-n,x+2*page-n,n);for(i=0;i<n;i++)assert(y[2*page-n+i]==42);}
 munmap(x,page*3);munmap(y,page*3);return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 d=Path(d);objs=[];flags=['-m32','-O2','-fno-builtin','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-sanitize-recover=all']
 for fn in ('memcpy','memset'):
  obj=d/(fn+'.o');subprocess.run(['gcc',*flags,'-D'+fn+'=fast_'+fn,'-I'+str(a.newlib/'newlib/libc/include'),'-c',str(a.newlib/'newlib/libc/string'/(fn+'.c')),'-o',str(obj)],check=True);objs.append(str(obj))
 (d/'test.c').write_text(s);subprocess.run(['gcc',*flags,'-no-pie',str(d/'test.c'),*objs,'-o',str(d/'test')],check=True);subprocess.run([str(d/'test')],check=True)
print('PASS actual Newlib speed paths: all alignments/lengths, all fill values, exact guard-page ends, ASan/UBSan')

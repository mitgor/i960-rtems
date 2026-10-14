#!/usr/bin/env python3
"""Execute the actual producer: independently check every byte and STOP exit."""
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <string.h>
#include "engine.c"
static unsigned stop,frames,mode;
static unsigned owner(void){return 1;}
static unsigned stopping(void){return stop;}
static int mark(unsigned stage,unsigned x,unsigned n,unsigned g){unsigned i;
 assert(stage==100&&x==(unsigned)doom_platform_frames[0]&&n==65536&&g==frames+1);
 for(i=0;i<n;i++)assert(doom_platform_frames[0][i]==(unsigned char)((13*i)^(i/256)^(37*g)));
 if(mode&&g==17){stop=1;return -1;}
 frames=g;if(g==256)stop=1;return 1;
}
int main(void){struct doom_runtime_checkpoint a;unsigned k;
 memset(&a,0,sizeof a);a.base.magic=DOOM_OWNED_MAGIC;a.base.version=DOOM_CHECKPOINT_VERSION;a.base.bytes=sizeof a;a.base.owner=owner;a.base.stopping=stopping;a.mark=mark;
 for(k=0;k<2;k++){stop=frames=0;mode=k;memset((void*)doom_engine_result,0,sizeof doom_engine_result);
 assert(doom_engine_entry(&a.base)==0x454e4702);assert(frames==(k?16:256));assert(doom_engine_result[5]==frames);assert(doom_engine_result[9]==2&&doom_engine_result[10]==1&&doom_engine_result[11]==210);}
 a.base.version=0;assert(doom_engine_entry(&a.base)==1);return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['cc','-O1','-Wno-pointer-to-int-cast','-fsanitize=address,undefined','-fno-sanitize-recover=all','-I'+str(r),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
print('PASS actual stress producer: 256 exact complete frames, cancellation while pinned, STOP and invalid API')

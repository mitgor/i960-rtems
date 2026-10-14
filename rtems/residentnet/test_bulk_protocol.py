#!/usr/bin/env python3
"""Compile the actual kernel frame-request body; test sequencing and uncertainty."""
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
h=(r/'upload_host.h').read_text();begin=h.index(' if(op==11){\n  rc=');end=h.index('\n else\n#endif',begin)
source=r'''
#include <assert.h>
#include <errno.h>
#include <string.h>
static unsigned calls,fail_call,select_fail;
static int packet_exchange(void*d,unsigned token,unsigned value,unsigned*v,unsigned deadline){
 unsigned op=token>>24,index=(token>>16)&255;assert((token&65535)==42);calls++;
 if(calls==fail_call)return -ETIMEDOUT;
 if(calls==1){assert(op==0x6c&&!index&&value==7);*v=select_fail;}
 else if(calls==2){assert(op==0x6d&&!index&&value==1024);*v=0;}
 else assert(0);return 0;
}
static int frame_pair_exchange(void*d,unsigned token,unsigned*first,unsigned*second,unsigned deadline){
 unsigned index=(token>>16)&255;calls++;assert(token>>24==0x6f&&(token&65535)==42&&index==calls-3);
 if(calls==fail_call)return -ETIMEDOUT;
 *first=(2*index)^0xdeadbeefu;*second=(2*index+1)^0xdeadbeefu;return 0;
}
static int run(void){unsigned w[264]={0},op=11,epoch=42,v,deadline=1,n=8,i;void*d=0;int rc=0;
 w[8]=7;w[9]=1024;
 /*BODY*/
 assert(n==1024&&calls==130);for(i=0;i<256;i++)assert(w[8+i]==(i^0xdeadbeefu));return 0;
 uncertain:return 1;
 unlock:return 2;
}
int main(void){assert(!run());calls=0;select_fail=1;assert(run()==2&&calls==1);select_fail=0;
 for(fail_call=1;fail_call<=130;fail_call++){calls=0;assert(run()==1&&calls==fail_call);}return 0;}
'''.replace('/*BODY*/',h[begin:end])
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp);(t/'test.c').write_text(source);subprocess.run(['cc','-std=c11','-fsanitize=address,undefined',str(t/'test.c'),'-o',str(t/'test')],check=True);subprocess.run([str(t/'test')],check=True)
print('PASS actual 130-exchange paired frame request, generation refusal and uncertainty at every exchange')

#include <assert.h>
#include <stdio.h>
static unsigned selector,reads,writes,badmeta,badid,badrestore;
static unsigned rd(unsigned a){
 switch(a){
 case 0xc0384e78:return badmeta?0:0x10161077;
 case 0xc0384ba0:return 16;
 case 0xc0384b8c:return 0x8bf00000;
 case 0xc0384b90:return 0xfff00000;
 case 0x12a8:return badrestore&&writes>1?0:selector;
 case 0x12b0:
  assert(reads<5);assert(selector==((unsigned[]){0x10000,0x10004,0x10008,0x10010,0x10014})[reads]);reads++;
  return selector==0x10000?(badid?0xffffffff:0x10161077):selector;
 default:assert(0);return 0;
 }
}
static void wr(unsigned a,unsigned v){assert(a==0x12a8);writes++;selector=v;}
#define Q_READ(a) rd(a)
#define Q_WRITE(a,v) wr(a,v)
#include "qlogic_config.h"
int main(void){unsigned r[1024],i;
 for(i=0;i<1024;i++)r[i]=0xa5a5a5a5;
 selector=0x12345678;at_qlogic_snapshot(r,12,3,0);
 assert(reads==5&&writes==6&&selector==0x12345678&&r[325]==0&&r[328]==5);
 for(i=0;i<320;i++)assert(r[i]==0xa5a5a5a5);
 for(i=340;i<1024;i++)assert(r[i]==0xa5a5a5a5);
 reads=writes=0;badmeta=1;at_qlogic_snapshot(r,12,4,0);assert(!reads&&!writes&&r[325]==1);
 badmeta=0;badid=1;at_qlogic_snapshot(r,12,5,1);assert(reads==1&&writes==2&&r[325]==3&&selector==0x12345678);
 badid=0;badrestore=1;reads=writes=0;at_qlogic_snapshot(r,12,6,1);assert(r[325]==4);
 puts("QLogic: fixed reads, selector-only writes, mismatch/refusal/restore paths, report bounds passed");
 return 0;
}

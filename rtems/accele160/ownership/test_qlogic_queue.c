#include <assert.h>
#include <stdio.h>
static unsigned reads,badmeta,badptr;
static unsigned qr_read(unsigned a);
#define QR_READ(a) qr_read(a)
#include "qlogic_queue.h"
static unsigned qr_read(unsigned a){unsigned i;
 if(a==0xc0384e78)return badmeta==1?0:0x10161077;
 if(a==0xc0384ba0)return badmeta==2?0:16;
 if(a==0xc0384b8c)return badmeta==3?0:0x8bf00000;
 if(a==0xc03e5bc8)return badptr?0xdeadbeef:0xc0600d00;
 assert(!badmeta&&!badptr);assert(reads<14);i=reads++;
 assert(a==at_qr_addresses[i]);return a;
}
int main(void){unsigned r[1024],i;
 for(i=0;i<1024;i++)r[i]=0xa5a5a5a5;
 at_qlogic_queue(r,23,4,0);assert(reads==14&&r[357]==0&&r[359]==14);
 for(i=0;i<352;i++)assert(r[i]==0xa5a5a5a5);
 for(i=384;i<1024;i++)assert(r[i]==0xa5a5a5a5);
 for(i=0;i<14;i++)assert(r[360+i]==at_qr_addresses[i]);
 for(badmeta=1;badmeta<=3;badmeta++){reads=0;at_qlogic_queue(r,23,5,1);assert(!reads&&r[357]==1&&!r[359]);}
 badmeta=0;badptr=1;at_qlogic_queue(r,23,6,1);assert(!reads&&r[357]==2&&r[358]==0xdeadbeef);
 puts("QLogic RAM: fixed ordered reads, all metadata/pointer refusals and page boundaries passed");return 0;
}

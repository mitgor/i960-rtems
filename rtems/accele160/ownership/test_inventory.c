#include <assert.h>
#include <stdio.h>
static unsigned reads;
static unsigned read_reg(unsigned a){
 assert(a!=0x1404&&a!=0x1444&&a!=0x1484&&a!=0x1804);
 reads++;return a^0x96016000u;
}
#define REG(a) read_reg(a)
#include "inventory.h"
int main(void){unsigned page[1024],i;
 for(i=0;i<1024;i++)page[i]=0xa5a5a5a5;
 at_engine_snapshot(page,123,7,1);assert(reads==48);
 for(i=0;i<256;i++)assert(page[i]==0xa5a5a5a5);
 for(i=312;i<1024;i++)assert(page[i]==0xa5a5a5a5);
 assert(page[256]==0x31474e45&&page[258]==123&&page[259]==7&&page[260]==1);
 for(i=0;i<48;i++)assert(page[264+i]==(at_engine_regs[i]^0x96016000u));
 puts("inventory: 48 reads, no event status, report boundaries intact");return 0;
}

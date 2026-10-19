#include <assert.h>
#include "policy.h"
int main(void){unsigned int n,s,t,m;
 for(n=0;n<3;n++)for(s=0;s<4;s++)for(t=0;t<2;t++)for(m=0;m<12;m++)
 assert(at_request(n,s,t?AT_TRIGGER:0,2,m)==(n==2&&s==1&&t&&((m>=1&&m<=4)||(m>=6&&m<=10))));
 assert(!at_request(0,1,AT_TRIGGER,0,1));
 assert(AT_RECORD+4096==AT_STACK&&AT_STACK+4096==AT_END);
 for(n=0;n<3;n++)assert(at_dma_offsets[n]!=4);
 return 0;
}

/* Replay the exact kernel acceptance predicate over hardware reports. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "report.h"
int main(void){unsigned int w[64],x[64],n=0;
 while(fread(w,sizeof(w),1,stdin)==1){assert(ownership_report_valid(w,w[2],w[3]));n++;
  memcpy(x,w,sizeof(x));x[35]=1;assert(!ownership_report_valid(x,x[2],x[3]));
  memcpy(x,w,sizeof(x));x[36]=1;assert(!ownership_report_valid(x,x[2],x[3]));
  assert(!ownership_report_valid(w,w[2]+1,w[3]));
  if(w[5]){memcpy(x,w,sizeof(x));x[10]=1;assert(!ownership_report_valid(x,x[2],x[3]));
   memcpy(x,w,sizeof(x));x[48]=3;assert(!ownership_report_valid(x,x[2],x[3]));
   memcpy(x,w,sizeof(x));x[23]&=~2u;assert(!ownership_report_valid(x,x[2],x[3]));}
 }
 assert(n);printf("%u real reports and damaged-report rejection passed\n",n);return 0;
}

#include <assert.h>
#include <limits.h>
#include <string.h>
#include <stdio.h>
#include "system_info.h"
int main(void){char out[4096],tiny[8];struct info_writer w={out,sizeof(out),0,0},small={tiny,sizeof(tiny),0,0};
 system_info(&w,90061,UINT_MAX,3,4,5,2);
 assert(!w.failed&&w.used<3200&&strstr(out,"1d 1h 1m 1s"));
 assert(strstr(out,"4294967295")&&strstr(out,"Not measured")&&strstr(out,"Unavailable"));
 memset(tiny,0x55,sizeof(tiny));system_info(&small,0,0,0,0,0,0);assert(small.failed&&small.used==7&&tiny[7]==0);
 puts("System info: uptime formatting, maximum counters and bounded overflow passed");
}

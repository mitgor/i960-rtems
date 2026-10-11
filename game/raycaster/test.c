#include "ray.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static void put(unsigned char*p,unsigned int v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;}
int main(void){unsigned char in[32]={0},out[4866],*s=calloc(1,ray_size()),*before=malloc(ray_size());unsigned int i,j;
 put(in,RAY_MAGIC);put(in+16,1);memset(out,0xa5,sizeof(out));
 assert(!ray_request(s,in,32,out+1,4864));memcpy(before,s,ray_size());
 put(in+4,1);put(in+8,81);assert(ray_request(s,in,32,out+1,4864)==1);assert(!memcmp(s,before,ray_size()));
 put(in+8,80);assert(ray_request(s,in,32,out+1,4863)==2);assert(!memcmp(s,before,ray_size()));
 for(i=0;i<2000;i++){put(in+12,i%16);put(in+8,i%80+1);assert(!ray_request(s,in,32,out+1,4864));for(j=65;j<4865;j++)assert(out[j]<10);}
 assert(out[0]==0xa5&&out[4865]==0xa5);
 put(in+4,3);put(in+8,0);put(in+12,0);put(in+24,128);
 for(i=0;i<9;i++){put(in+20,i);assert(!ray_request(s,in,32,out+1,4864));}
 free(s);free(before);puts("Raycaster ASan/UBSan: bounds, invalid requests, 2000 partial movement batches, benchmark kinds passed");return 0;
}

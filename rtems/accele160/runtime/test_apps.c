#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "app_service.h"
static unsigned char in[300],out[400];
static unsigned call(unsigned op,unsigned id,unsigned gen,unsigned n){as_put(in,AS_MAGIC);as_put(in+4,1);as_put(in+8,op);as_put(in+12,id);as_put(in+16,gen);return as_call(in,n,out,sizeof(out));}
int main(void){
 assert(call(1,1,0,20)==48&&as_word(out+8)==0&&as_word(out+16)==1);
 assert(call(1,2,0,20)==48&&as_word(out+8)==0);
 as_step(20);assert(as_apps[0].updates==1&&as_apps[1].updates==1);
 memcpy(in+20,"hello",5);assert(call(4,2,1,25)==53&&!memcmp(out+48,"HELLO",5));
 assert(call(2,1,0,20)==48&&as_word(out+8)==4&&as_apps[0].running);
 assert(call(2,1,1,20)==48&&!as_word(out+8));as_step(20);assert(as_apps[0].updates==1&&as_apps[1].updates==2);
 assert(call(2,1,1,20)==48&&as_apps[0].stops==1);
 assert(call(1,1,1,20)==48&&as_word(out+16)==2);
 assert(call(2,1,1,20)==48&&as_word(out+8)==4&&as_apps[0].running);
 assert(call(4,2,1,277)==48&&as_word(out+8)==1);
 assert(call(9,2,1,20)==48&&as_word(out+8)==3);
 assert(call(1,3,0,20)==48&&as_word(out+8)==2);
 memset(out,0xa5,sizeof(out));assert(as_call(in,20,out,303)==0xffffffffu&&out[0]==0xa5);
 memset(in+20,'a',256);assert(call(4,2,1,276)==304);for(unsigned i=0;i<256;i++)assert(out[48+i]=='A');
 as_apps[0].running=0;as_apps[0].generation=~0u;assert(call(1,1,~0u,20)==48&&as_word(out+8)==6&&!as_apps[0].running);
 puts("bounded apps: concurrent progress, echo, independent stop, stale generation, idempotent stop and bounds passed");
}

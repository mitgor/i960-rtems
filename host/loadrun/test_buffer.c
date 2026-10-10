#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "buffer_io.h"
#define payload buffer_payload
#include "buffer_demo.c"
#undef payload
static unsigned char before[0x80000],after[0x80000];
static void setup(unsigned int mode,unsigned int capacity)
{
    unsigned char *b=before+BIO_OFFSET;
    memset(before,0,sizeof(before));
    bio_put(b,BIO_MAGIC);bio_put(b+4,1);bio_put(b+8,123);bio_put(b+12,4);
    bio_put(b+16,capacity);bio_put(b+20,BIO_PENDING);
    b[BIO_INPUT]=mode;memcpy(b+BIO_INPUT+1,"abc",3);
    memset(b+BIO_GUARD1,0xa5,16);memset(b+BIO_OUTPUT,0xcc,BIO_OUTPUT_MAX);memset(b+BIO_GUARD2,0x5a,16);
    assert(bio_request_valid(b));memcpy(after,before,sizeof(before));
}
int main(void)
{
    unsigned int i;
    unsigned char *b=after+BIO_OFFSET;
    setup(0,8192);assert(!buffer_payload((unsigned long)b));
    assert(bio_word(b+24)==29);
    assert(!memcmp(b+BIO_OUTPUT,"Hello from the real i960!\nABC",29));
    assert(bio_response_valid(before,after,sizeof(before)));
    b[BIO_GUARD1]^=1;assert(!bio_response_valid(before,after,sizeof(before)));b[BIO_GUARD1]^=1;
    b[BIO_OUTPUT+29]^=1;assert(!bio_response_valid(before,after,sizeof(before)));b[BIO_OUTPUT+29]^=1;
    bio_put(b+28,122);assert(!bio_response_valid(before,after,sizeof(before)));
    setup(0,28);assert(!buffer_payload((unsigned long)b));assert(bio_word(b+20)==2);
    setup(0,29);assert(!buffer_payload((unsigned long)b));assert(bio_word(b+24)==29);
    setup(1,8192);assert(!buffer_payload((unsigned long)b));assert(bio_word(b+24)==1920);
    assert(bio_response_valid(before,after,sizeof(before)));
    for(i=0;i<1920;i++) assert(b[BIO_OUTPUT+i]>=32 && b[BIO_OUTPUT+i]<=126);
    setup(1,16);assert(!buffer_payload((unsigned long)b));assert(bio_word(b+20)==2 && !bio_word(b+24));
    assert(bio_response_valid(before,after,sizeof(before)));
    bio_put(b+24,17);assert(!bio_response_valid(before,after,sizeof(before)));
    for(i=0;i<8;i++) {
        setup(0,8192);bio_put(b+4*i,i==2?0:0xffffffff);
        if(i!=5) {assert(!bio_request_valid(b));assert(buffer_payload((unsigned long)b)==1);}
    }
    setup(0,8192);b[32]=1;assert(!bio_request_valid(b));
    setup(0,8192);b[BIO_GUARD2]=0;assert(!bio_request_valid(b));
    setup(0,8192);bio_put(b+8,0);assert(!bio_request_valid(b));
    return 0;
}

#include "updater.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>

static unsigned char *flash, *target, *buffer;
static unsigned int writes, last_offset;

static int mock_write(unsigned int offset,const unsigned char *bytes,
                      unsigned int length,void *context)
{
    int fail=*(int *)context;
    assert(offset>=0x40000u&&offset<0xc0000u&&!(offset&0xffffu));
    assert(length==0x10000u);
    if (fail==1) return 1;
    memcpy(flash+offset,bytes,fail==2?1024u:length);
    if (fail==0) { ++writes;last_offset=offset; }
    return 0;
}

static void feed(accele160_updater *u)
{
    unsigned int i;
    for (i=0;i<ACCELE160_UPDATE_CHUNKS;++i)
        assert(accele160_update_chunk(u,i,target+i*4096u,4096u,
            accele160_fnv32(target+i*4096u,4096u))==ACCELE160_UPDATE_OK);
}

int main(void)
{
    accele160_updater u={0};
    unsigned char base_hash[32],target_hash[32],wrong_hash[32],abc[32];
    unsigned int i;
    int fail=0;
    flash=malloc(0x100000u);target=malloc(0x100000u);buffer=malloc(0x100000u);
    assert(flash&&target&&buffer);
    accele160_sha256((const unsigned char *)"abc",3u,abc);
    { const unsigned char known[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,
        0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,0xb0,0x03,0x61,0xa3,
        0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
      assert(memcmp(abc,known,32)==0); }
    for (i=0;i<0x100000u;++i) flash[i]=(unsigned char)(i*13u+i/257u);
    memcpy(target,flash,0x100000u);
    target[0x51000u]^=0x55u;target[0x51fffu]^=0x11u;
    accele160_sha256(flash,0x100000u,base_hash);
    { const unsigned char known[32]={0xd8,0x38,0x8b,0xe8,0x2d,0xd7,0x9f,0x2e,
        0x18,0xd9,0x3a,0x24,0x76,0xc5,0x28,0xda,0x8c,0xff,0xdb,0x0a,
        0xcb,0xb2,0x41,0xf4,0x57,0x3e,0xf7,0xb5,0xd7,0xd0,0x52,0x0e};
      assert(memcmp(base_hash,known,32)==0); }
    accele160_sha256(target,0x100000u,target_hash);
    memcpy(wrong_hash,base_hash,32);wrong_hash[0]^=1;
    assert(accele160_update_begin(&u,buffer,flash,wrong_hash,target_hash)==ACCELE160_UPDATE_BASE_HASH);
    assert(accele160_update_begin(&u,buffer,flash,base_hash,target_hash)==ACCELE160_UPDATE_OK);
    assert(accele160_update_chunk(&u,1,target+4096u,4096u,
        accele160_fnv32(target+4096u,4096u))==ACCELE160_UPDATE_SEQUENCE);
    assert(accele160_update_chunk(&u,0,target,4096u,0u)==ACCELE160_UPDATE_CHUNK_HASH);
    target[0]^=1;
    assert(accele160_update_chunk(&u,0,target,4096u,
        accele160_fnv32(target,4096u))==ACCELE160_UPDATE_PROTECTED);
    target[0]^=1;
    assert(accele160_update_abort(&u)==ACCELE160_UPDATE_OK);
    assert(u.state==0u&&u.next_chunk==0u&&u.buffer==0&&u.flash==0);
    memcpy(wrong_hash,target_hash,32);wrong_hash[0]^=1;
    assert(accele160_update_begin(&u,buffer,flash,base_hash,wrong_hash)==ACCELE160_UPDATE_OK);
    feed(&u);
    assert(accele160_update_seal(&u)==ACCELE160_UPDATE_IMAGE_HASH);
    assert(accele160_update_abort(&u)==ACCELE160_UPDATE_OK);
    assert(accele160_update_begin(&u,buffer,flash,base_hash,target_hash)==ACCELE160_UPDATE_OK);
    feed(&u);
    assert(accele160_update_seal(&u)==ACCELE160_UPDATE_OK);
    assert(accele160_update_apply(&u,0,&fail)==ACCELE160_UPDATE_NO_WRITER);
    buffer[0x51000u]^=1;
    assert(accele160_update_apply(&u,mock_write,&fail)==ACCELE160_UPDATE_IMAGE_HASH);
    buffer[0x51000u]^=1;
    flash[0x20000u]^=1;
    assert(accele160_update_apply(&u,mock_write,&fail)==ACCELE160_UPDATE_BASE_HASH);
    flash[0x20000u]^=1;
    fail=1;
    assert(accele160_update_apply(&u,mock_write,&fail)==ACCELE160_UPDATE_WRITE_FAILED);
    assert(u.state==4u);
    assert(accele160_update_abort(&u)==ACCELE160_UPDATE_STATE);
    assert(u.state==4u);
    assert(accele160_update_apply(&u,mock_write,&fail)==ACCELE160_UPDATE_STATE);
    memset(&u,0,sizeof(u));fail=2;
    assert(accele160_update_begin(&u,buffer,flash,base_hash,target_hash)==ACCELE160_UPDATE_OK);
    feed(&u);
    assert(accele160_update_seal(&u)==ACCELE160_UPDATE_OK);
    assert(accele160_update_apply(&u,mock_write,&fail)==ACCELE160_UPDATE_VERIFY_FAILED);
    assert(u.state==4u);
    assert(accele160_update_abort(&u)==ACCELE160_UPDATE_STATE);
    memset(&u,0,sizeof(u));fail=0;
    assert(accele160_update_begin(&u,buffer,flash,base_hash,target_hash)==ACCELE160_UPDATE_OK);
    feed(&u);
    assert(accele160_update_seal(&u)==ACCELE160_UPDATE_OK);
    assert(accele160_update_apply(&u,mock_write,&fail)==ACCELE160_UPDATE_OK);
    assert(writes==1u&&last_offset==0x50000u);
    assert(memcmp(flash,target,0x100000u)==0);
    free(flash);free(target);free(buffer);
    return 0;
}

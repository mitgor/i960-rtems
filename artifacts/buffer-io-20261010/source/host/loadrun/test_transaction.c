#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
#define STAGING_BASE 0xc0f2c000u
#define IMAGE_WINDOW 0x80000u
#define MAX_READ 0xf000u
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define min_t(t,a,b) ((t)(a)<(t)(b)?(t)(a):(t)(b))
#define record(...) ((void)0)
#define cpu_to_le32(x) (x)
#define msleep(x) ((void)(x))
#include "load_policy.h"
#include "buffer_io.h"
#define payload buffer_payload
#include "buffer_demo.c"
#undef payload
#include "rom_exec.h"
#include "stage_data.h"
struct firmware { size_t size;const u8 *data; };
struct capture {u8 *data;};
struct experiment {
    struct firmware *payload;
    bool runtime_verified,exec_armed,load_armed,exec_dirty,stage_dirty,pending;
    u16 exec_expected_status,exec_last_status;
    u8 dma_buf[MAX_READ];
    u8 runner_code[EXEC_FLASH_SIZE];const u8 *upload_data;
    struct capture capture[54],stage[8];
};
static unsigned int payload_argument=10,entry_offset;
static bool buffer_io;
static u8 original[IMAGE_WINDOW],card[0x82000],table[4];
static int calls,fail_at,timeout_mode,executions,corrupt;
static unsigned int sp_word(const u8 *b) {return (u32)b[0]|(u32)b[1]<<8|(u32)b[2]<<16|(u32)b[3]<<24;}
static void put(u8 *b,u32 n) {b[0]=n;b[1]=n>>8;b[2]=n>>16;b[3]=n>>24;}
static int sp_profile(const u8 *b) {return b[0]==42;}
static int load_digest(const void *data,unsigned int size,u8 out[32])
{
    const u8 *b=data;u32 x=2166136261u;unsigned int i;
    if(size==IMAGE_WINDOW && !memcmp(b,original,size)) {memcpy(out,stage_candidate_sha256,32);return 0;}
    for(i=0;i<size;i++) x=(x^b[i])*16777619u;
    for(i=0;i<32;i+=4) put(out+i,x);
    return 0;
}
static u8 *address(u32 off,unsigned int size)
{
    if(off==EXEC_TABLE_OFFSET) {assert(size==4);return table;}
    assert(off<=sizeof(card)-size);return card+off;
}
static int issue(struct experiment *d,u8 op,u16 count,u32 off,u8 pattern,unsigned int slot)
{
    int status=0;u8 *b;
    (void)pattern;assert(!d->pending);calls++;
    if(op==0x21) {
        assert(d->upload_data);
        assert(load_upload_allowed(count,off,d->payload->size,d->runtime_verified,d->load_armed)||exec_upload_allowed(count,off,d->runtime_verified,d->exec_armed));
        memcpy(address(off,count),d->upload_data,count);
    } else if(op==0x20) {
        b=address(off,count);memcpy(d->dma_buf,b,count);if(slot<54) memcpy(d->capture[slot].data,b,count);
    } else if(op==0x1c) d->capture[3].data[0]=42;
    else {
        assert(op==0x6f);
        if(sp_word(table)==0xfefe001c) status=0x17e;
        else if(sp_word(table)==EXEC_RAM_ADDRESS) status=0x17d;
        else {
            assert(sp_word(table)==EXEC_FLASH_ADDRESS);executions++;
            assert(sp_word(card+EXEC_FLASH_OFFSET+16)==payload_argument);
            assert(sp_word(card+EXEC_FLASH_OFFSET+24)==STAGING_BASE+entry_offset);
            if(buffer_io) {
                assert(buffer_payload((unsigned long)(card+BIO_OFFSET))==0);
                if(corrupt==1)put(card+BIO_OFFSET+28,41);
                if(corrupt==2)put(card+BIO_OFFSET+24,8193);
                if(corrupt==3)card[BIO_OFFSET+BIO_GUARD2]^=1;
                if(corrupt==4)card[0]^=1;
                if(corrupt==5)card[BIO_OFFSET+BIO_OUTPUT+29]^=1;
                if(corrupt==6)card[BIO_IMAGE_SIZE+4]^=1;
            }
            put(card+LOAD_RESULT_OFFSET,buffer_io?0:55);put(card+LOAD_RESULT_OFFSET+4,0x52554e31);
            put(table,0xfefe001c);status=0x17f;
        }
        d->exec_last_status=status;
    }
    if(calls==fail_at) {d->pending=timeout_mode;return -EIO;}
    if(op==0x6f && d->exec_expected_status!=0xffff && status!=d->exec_expected_status) return -EIO;
    return 0;
}
static int read_pair(struct experiment *d,u32 addr,u16 n,unsigned int slot)
{
    int rc=issue(d,0x20,n,addr-STAGING_BASE,0xa5,slot);
    if(!rc) rc=issue(d,0x20,n,addr-STAGING_BASE,0x5a,slot+1);
    if(!rc && memcmp(d->capture[slot].data,d->capture[slot+1].data,n)) rc=-ENODATA;
    return rc;
}
static int exec_upload(struct experiment *d,const u8 *data,u16 n,u32 off,unsigned int slot)
{
    int rc;d->upload_data=data;rc=issue(d,0x21,n,off,0xa5,slot);d->upload_data=NULL;return rc;
}
static int stage_read_pair(struct experiment *d,unsigned int slot,const u8 *expected,const char *label)
{
    unsigned int pass,off;u8 hash[32];int rc;(void)label;
    for(pass=0;pass<2;pass++) for(off=0;off<IMAGE_WINDOW;off+=MAX_READ) {
        u16 n=min_t(u32,MAX_READ,IMAGE_WINDOW-off);
        rc=issue(d,0x20,n,off,pass?0x5a:0xa5,54);if(rc)return rc;
        memcpy(d->stage[slot+pass].data+off,card+off,n);
    }
    if(memcmp(d->stage[slot].data,d->stage[slot+1].data,IMAGE_WINDOW))return -ENODATA;
    load_digest(d->stage[slot].data,IMAGE_WINDOW,hash);
    return memcmp(hash,expected,32)?-ENODATA:0;
}
#include "transaction_under_test.h"
static int one(int fail,int timeout,unsigned int size)
{
    struct experiment d={0};struct firmware fw;unsigned int i;int rc,n;
    u8 *payload=calloc(1,size);
    if(buffer_io) {
        u8 *b=payload+BIO_OFFSET;
        put(b,BIO_MAGIC);put(b+4,1);put(b+8,42);put(b+12,4);put(b+16,8192);put(b+20,BIO_PENDING);
        b[BIO_INPUT]=0;memcpy(b+BIO_INPUT+1,"abc",3);
        memset(b+BIO_GUARD1,0xa5,16);memset(b+BIO_OUTPUT,0xcc,BIO_OUTPUT_MAX);memset(b+BIO_GUARD2,0x5a,16);
        assert(bio_request_valid(b));
    }
    memset(card,0,sizeof(card));memcpy(card,original,IMAGE_WINDOW);put(table,0xfefe001c);
    calls=executions=0;fail_at=fail;timeout_mode=timeout;
    fw.size=size;fw.data=payload;d.payload=&fw;d.runtime_verified=true;
    for(i=0;i<54;i++)d.capture[i].data=calloc(1,128);
    for(i=0;i<8;i++)d.stage[i].data=calloc(1,IMAGE_WINDOW);
    rc=run_stage(&d);n=calls;
    assert(executions<=1);
    if(fail || corrupt)assert(rc);else assert(!rc && executions==1 && !d.stage_dirty && !d.exec_dirty);
    if(d.pending)assert(calls==fail);
    if(corrupt && corrupt<6)assert(!d.stage_dirty && !d.exec_dirty && !d.pending);
    if(corrupt==6)assert(d.stage_dirty && !d.pending);
    if(!d.stage_dirty && !d.exec_dirty) {
        assert(!memcmp(card,original,IMAGE_WINDOW));assert(sp_word(table)==0xfefe001c);
        for(i=IMAGE_WINDOW;i<sizeof(card);i++)assert(!card[i]);
    }
    assert(!d.load_armed && !d.exec_armed && !d.upload_data);
    for(i=0;i<54;i++)free(d.capture[i].data);
    for(i=0;i<8;i++)free(d.stage[i].data);
    free(payload);return n;
}
int main(int argc,char **argv)
{
    int i,n,legacy_n;FILE *f;assert(argc==2);
    f=fopen(argv[1],"rb");assert(f);assert(fread(original,1,IMAGE_WINDOW,f)==IMAGE_WINDOW);fclose(f);
    assert(load_valid(4,0));assert(load_valid(65536,65532));
    assert(!load_valid(0,0)&&!load_valid(65540,0)&&!load_valid(4,4)&&!load_valid(8,1)&&!load_valid(5,0));
    assert(!load_upload_allowed(4,0xfffffffc,64,1,1));
    assert(!load_upload_allowed(4,64,64,1,1));
    assert(!load_upload_allowed(4,0,64,0,1));
    assert(!load_upload_allowed(4,0,64,1,0));
    n=one(0,0,64);legacy_n=n;
    for(i=1;i<=n;i++){one(i,0,64);one(i,1,64);}
    one(0,0,65536);
    buffer_io=true;payload_argument=BIO_BASE;
    n=one(0,0,BIO_IMAGE_SIZE);
    for(i=1;i<=n;i++){one(i,0,BIO_IMAGE_SIZE);one(i,1,BIO_IMAGE_SIZE);}
    for(corrupt=1;corrupt<=6;corrupt++)one(0,0,BIO_IMAGE_SIZE);
    corrupt=0;
    printf("buffer transaction: %d command-boundary faults passed\n",2*n);
    printf("runtime transaction: %d command-boundary faults plus maximum upload passed\n",2*legacy_n);
    return 0;
}

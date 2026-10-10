/* Native integration model: compiles the generated run_stage unchanged;
 * replaces only MMIO, CPU execution, allocation and SHA256 with exact-image models. */
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define IMAGE_WINDOW 0x80000u
#define MAX_READ 0xf000u
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define min_t(t,a,b) ((t)(a)<(t)(b)?(t)(a):(t)(b))
#define record(...) ((void)0)
#include "one_shot.h"
#include "stage_data.h"
struct capture { u8 *data; };
struct experiment {
    struct po_state program;
    bool runtime_verified,stage_armed,stage_dirty,pending,exec_dirty,exec_armed;
    const u8 *upload_data;
    u8 *dma_buf;
    struct capture capture[54],stage[6];
};
static u8 stock[IMAGE_WINDOW],candidate[IMAGE_WINDOW],ram[IMAGE_WINDOW],flash[IMAGE_WINDOW];
static int program_enable,cpu_error,cpu_dirty,submit_mode,readback_error;
static int calls,fail_at,timeout_mode,uploads,restores,program_calls,fresh_copies,allocated;
static int sp_profile(const u8 *p) { return p[0]==42; }
static int stage_hash(struct experiment *d,const u8 *b,const u8 *hash,const char *label)
{
    (void)d;(void)label;
    return memcmp(b, hash==stage_stock_sha256 ? stock:candidate,IMAGE_WINDOW) ? -ENODATA:0;
}
static int issue(struct experiment *d,u8 op,u16 count,u32 off,u8 pat,unsigned int slot)
{
    assert(!d->pending);(void)slot;
    calls++;
    if(op==0x21) {
        assert(!d->program.submitted);
        assert(stage_upload_allowed(count,off,d->runtime_verified,d->stage_armed));
        uploads++;
        if(!memcmp(d->upload_data,stock+off,count)) restores++;
        memcpy(ram+off,d->upload_data,count);
    } else if(op==0x20) {
        if(!allocated) { assert(d->program.completed);memcpy(ram,flash,IMAGE_WINDOW);allocated=1;fresh_copies++; }
        memset(d->dma_buf,pat,65536);memcpy(d->dma_buf,ram+off,count);
        if(d->program.submitted && readback_error) d->dma_buf[0]^=1;
    } else { assert(op==0x1c);d->capture[3].data[0]=42; }
    if(calls==fail_at) {d->pending=timeout_mode;return -EIO;}
    return 0;
}
static int run_rom_exec(struct experiment *d)
{
    d->exec_dirty=cpu_dirty;
    return cpu_error ? -EIO:0;
}
static int run_program_once(struct experiment *d);
#include "transaction_under_test.h"

static int program_submit(void *ctx,struct po_state *s)
{
    struct experiment *d=ctx;
    program_calls++;
    if(submit_mode==1) return -EBUSY;
    s->submitted=1;
    if(submit_mode==2) {d->pending=true;return -ETIMEDOUT;}
    s->completed=1;
    if(submit_mode==3) return -EIO;
    memcpy(flash,ram,IMAGE_WINDOW);
    allocated=0; /* Stock callback frees the allocation. */
    return 0;
}
static int program_readback(void *ctx)
{
    struct experiment *d=ctx;
    int rc;
    d->stage_armed=false;
    rc=stage_read_pair(d,4,stage_candidate_sha256,"fresh-flash");
    if(!rc) d->stage_dirty=false;
    return rc;
}
#include "program_flow_under_test.h"

static void one(int enable,int cpu_fail,int dirty,int mode,int corrupt,int fail,int timeout)
{
    struct experiment d={0};
    unsigned int i;int rc;
    program_enable=enable;cpu_error=cpu_fail;cpu_dirty=dirty;submit_mode=mode;
    readback_error=corrupt;fail_at=fail;timeout_mode=timeout;
    calls=uploads=restores=program_calls=fresh_copies=0;allocated=1;
    memcpy(ram,stock,IMAGE_WINDOW);memcpy(flash,stock,IMAGE_WINDOW);
    d.runtime_verified=true;d.dma_buf=calloc(1,65536);d.capture[3].data=calloc(1,512);
    for(i=0;i<6;i++) d.stage[i].data=calloc(1,IMAGE_WINDOW);
    rc=run_stage(&d);
    assert(!d.stage_armed && !d.upload_data);
    if(fail || cpu_fail || mode || corrupt) assert(rc!=0);else assert(rc==0);
    if(d.program.submitted) {
        assert(program_calls==1 && uploads==3 && !restores);
        if(d.program.verified) {
            assert(!d.stage_dirty && !memcmp(flash,candidate,IMAGE_WINDOW) && fresh_copies==1);
        } else assert(d.stage_dirty);
    } else if(!d.pending && !dirty) {
        assert(!memcmp(ram,stock,IMAGE_WINDOW));
    }
    if(d.pending) assert(calls==fail || mode==2);
    if(!enable || cpu_fail || fail) {
        /* A readback failure is reachable after programming; preflight errors aren't. */
        if(!enable || cpu_fail || (fail && fail<=39)) assert(!program_calls);
    }
    for(i=0;i<6;i++) free(d.stage[i].data);
    free(d.dma_buf);free(d.capture[3].data);
}
int main(int argc,char **argv)
{
    FILE *f;int i;
    assert(argc==3);
    f=fopen(argv[1],"rb");assert(f);assert(fread(stock,1,IMAGE_WINDOW,f)==IMAGE_WINDOW);fclose(f);
    f=fopen(argv[2],"rb");assert(f);assert(fread(candidate,1,IMAGE_WINDOW,f)==IMAGE_WINDOW);fclose(f);
    one(0,0,0,0,0,0,0);one(1,0,0,0,0,0,0);
    one(1,1,0,0,0,0,0);one(1,1,1,0,0,0,0);
    one(1,0,0,1,0,0,0);one(1,0,0,2,0,0,0);one(1,0,0,3,0,0,0);
    one(1,0,0,0,1,0,0);
    for(i=1;i<=57;i++) {one(1,0,0,0,0,i,0);one(1,0,0,0,0,i,1);}
    puts("transaction: 122 success/failure scenarios; rollback boundary and fresh-allocation model passed");
    return 0;
}

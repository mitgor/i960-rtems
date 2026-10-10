"""Exercise the actual staging transaction with simulated completion failures."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

class StageTests(unittest.TestCase):
    def test_archived_live_result(self):
        from validate_stage import validate
        directory = ROOT/'artifacts/staging-rehearsal-20261010'
        self.assertEqual(validate(directory),json.loads((directory/'validation.json').read_text()))

    def test_plan_and_failure_paths(self):
        plan = json.loads((ROOT/'artifacts/romhook-20261010/stage-plan/stage-plan.json').read_text())
        stock = ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin'
        candidate = ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin'
        source = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define IMAGE_WINDOW 0x80000u
#define MAX_READ 0xf000u
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define min_t(t,a,b) ((t)(a)<(t)(b)?(t)(a):(t)(b))
#define record(...) ((void)0)
#include "stage_data.h"
struct capture { u8 *data; };
struct experiment {
    bool runtime_verified, stage_armed, stage_dirty, pending;
    const u8 *upload_data;
    u8 *dma_buf;
    struct capture capture[54], stage[6];
};
static u8 stock[IMAGE_WINDOW], candidate[IMAGE_WINDOW], card[IMAGE_WINDOW];
static int calls, fail_at, timeout_mode, corrupt_at;
static int sp_profile(const u8 *p) { return p[0] == 42; }
static int stage_hash(struct experiment *d, const u8 *data, const u8 *hash, const char *label)
{
    (void)d; (void)label;
    return memcmp(data, hash == stage_stock_sha256 ? stock : candidate, IMAGE_WINDOW) ? -ENODATA : 0;
}
static int issue(struct experiment *d, u8 op, u16 count, u32 off, u8 pat, unsigned int slot)
{
    assert(!d->pending);
    ++calls;
    (void)slot;
    memset(d->dma_buf, pat, 65536);
    if (op == 0x21) {
        assert(stage_upload_allowed(count,off,d->runtime_verified,d->stage_armed));
        assert(d->stage_dirty);
        memcpy(card + off, d->upload_data, count);
    } else if (op == 0x20) {
        assert(count && count <= MAX_READ && off <= IMAGE_WINDOW-count);
        memcpy(d->dma_buf, card + off, count);
        if (calls == corrupt_at) d->dma_buf[0] ^= 1;
    } else {
        assert(op == 0x1c);
        d->capture[3].data[0] = 42;
    }
    if (calls == fail_at) {
        d->pending = timeout_mode;
        return -EIO;
    }
    return 0;
}
'''
        # Compile the production read/upload/rollback code unchanged. Replace only
        # kernel crypto with exact full-image comparison in this userspace model.
        source += 'static int stage_read_pair' + (HERE/'stage_rehearsal.h').read_text().split('static int stage_read_pair',1)[1]
        source += r'''
static int one(int fail, int timeout, int corrupt)
{
    struct experiment d = {0};
    unsigned int i;
    int rc;
    memcpy(card,stock,IMAGE_WINDOW);
    calls=0; fail_at=fail; timeout_mode=timeout; corrupt_at=corrupt;
    d.runtime_verified=true;
    d.dma_buf=calloc(1,65536);
    d.capture[3].data=calloc(1,512);
    for(i=0;i<6;i++) d.stage[i].data=calloc(1,IMAGE_WINDOW);
    rc=run_stage(&d);
    if (fail || corrupt) assert(rc != 0); else assert(rc == 0);
    assert(!d.stage_armed && !d.upload_data);
    if (d.pending) { assert(calls == fail); if (fail > 18 && fail <= 60) assert(d.stage_dirty); }
    else {
        assert(!memcmp(card,stock,IMAGE_WINDOW));
        /* Failed final read verification must retain dirty even after physical restoration. */
        if (fail >= 43 && fail <= 60) assert(d.stage_dirty);
        else assert(!d.stage_dirty);
    }
    free(d.dma_buf); free(d.capture[3].data);
    for(i=0;i<6;i++) free(d.stage[i].data);
    return calls;
}
int main(int argc, char **argv)
{
    FILE *f; unsigned int i; int n;
    assert(argc==3);
    f=fopen(argv[1],"rb"); assert(f); assert(fread(stock,1,IMAGE_WINDOW,f)==IMAGE_WINDOW); fclose(f);
    f=fopen(argv[2],"rb"); assert(f); assert(fread(candidate,1,IMAGE_WINDOW,f)==IMAGE_WINDOW); fclose(f);
    for(i=0;i<ARRAY_SIZE(stage_patches);i++) {
        const struct stage_patch *p=&stage_patches[i];
        assert(!memcmp(stock+p->offset,p->before,p->size));
        assert(!memcmp(candidate+p->offset,p->after,p->size));
        assert(!stage_upload_allowed(p->size,p->offset,0,1));
        assert(!stage_upload_allowed(p->size,p->offset,1,0));
        assert(!stage_upload_allowed(p->size+4,p->offset,1,1));
        assert(!stage_upload_allowed(p->size,p->offset+4,1,1));
    }
    n=one(0,0,0); assert(n==61);
    for(i=1;i<=(unsigned int)n;i++) { one(i,0,0); one(i,1,0); }
    one(0,0,1); one(0,0,22);
    puts("stage: success, 122 completion failures, and preimage/candidate corruption verified");
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/'stage.c'
            src.write_text(source)
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-I',str(HERE),str(src),'-o',str(Path(tmp)/'stage')],check=True)
            subprocess.run([str(Path(tmp)/'stage'),str(stock),str(candidate)],check=True)
        import hashlib
        self.assertEqual(hashlib.sha256(stock.read_bytes()).hexdigest(),plan['stock_sha256'])
        self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(),plan['candidate_sha256'])

if __name__ == '__main__':
    unittest.main()

// SPDX-License-Identifier: GPL-2.0
/* Controlled PG experiments: Enquiry2, LoadImage, and opt-in fixed scratch upload.
 * No opcode 0x22, reset, maintenance mode, or arbitrary opcode interface.
 * Read direction recovered from vendor dataflow: see VENDOR-READ-PATH.md.
 * Results/captures are exported via debugfs; captures are NOT validated dumps.
 * On uncertain completion, DMA allocation and module are retained until reboot.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/io.h>
#include <linux/iopoll.h>
#include <linux/dma-mapping.h>
#include <linux/debugfs.h>
#include <linux/slab.h>
#include <linux/delay.h>
#include <crypto/hash.h>
#include "stage_data.h"
#include "staging_pointer.h"
#include "ram_scratch.h"
#include <linux/firmware.h>
#include <linux/miscdevice.h>
#include <linux/mutex.h>
#include <linux/uaccess.h>
#include <linux/kref.h>
#include <linux/ktime.h>
#include "load_policy.h"
#include "buffer_io.h"
#include "rom_exec.h"

#define IDB 0x20
#define ODB 0x2c
#define IRQMASK 0x34
#define MBOX 0x1000
#define STATUS_ID 0x1018
#define STATUS 0x101a
#define DMA_SIZE 65536u
#define MAX_READ 0xf000u
/* PG 512 KiB profile: bootstrap C000C600, source FEF80000.
 * Fresh live capture places BIOS at 0x28000 and firmware at 0x30000.
 * See SNAPSHOT-RECOVERY.md; coverage still requires image validation. */
#define IMAGE_WINDOW 0x80000u
#define WAIT_US 2000000u

static char *bdf = "0000:37:09.1";
static bool attempt;
static bool pointer_check;
static bool runtime_check;
static bool scratch_check;
static bool dram_hook_check;
static bool rom_table_check;
static bool rom_exec_check;
static char *firmware_name;
static unsigned int payload_argument;
static unsigned int entry_offset;
static bool buffer_io;
module_param(buffer_io, bool, 0444);
module_param(firmware_name, charp, 0444);
module_param(payload_argument, uint, 0444);
module_param(entry_offset, uint, 0444);
static bool stage_check;
module_param(stage_check, bool, 0444);
MODULE_PARM_DESC(stage_check, "Full paired staging read, three pinned RAM patches, full verification and restoration; no programming");
static bool flash_map_check;
module_param(flash_map_check, bool, 0444);
MODULE_PARM_DESC(flash_map_check, "Read-only exact FEFB0200/FEFC8200/FEFE0000 live mapping comparison");
module_param(rom_exec_check, bool, 0444);
MODULE_PARM_DESC(rom_exec_check, "Fixed reversible RAM dispatch + physically mapped flash RET probe");
module_param(rom_table_check, bool, 0444);
MODULE_PARM_DESC(rom_table_check, "Fixed read-only opcode-0x6f dispatch-word observation");
module_param(dram_hook_check, bool, 0444);
MODULE_PARM_DESC(dram_hook_check, "Fixed read-only 64-byte C0120000 hook-site observation");
module_param(scratch_check, bool, 0444);
MODULE_PARM_DESC(scratch_check, "Fixed 16-byte RAM scratch write/read/restore after runtime checks");
module_param(runtime_check, bool, 0444);
module_param(pointer_check, bool, 0444);
MODULE_PARM_DESC(pointer_check, "Fixed four-byte staging pointer verification; no arbitrary offsets");
static unsigned int length = 512;
static unsigned int flash_offset;
module_param(bdf, charp, 0444);
module_param(attempt, bool, 0444);
module_param(length, uint, 0444);
module_param(flash_offset, uint, 0444);
MODULE_PARM_DESC(attempt, "Attempt two bounded LoadImage reads; see VENDOR-READ-PATH.md");

struct capture {
    struct debugfs_blob_wrapper blob;
    u8 *data;
};
struct experiment {
    struct kref refs;
    struct mutex session_lock;
    struct miscdevice misc;
    bool owned, removed, ready, runner_uncertain, response_ready, misc_registered;
    u32 sequence, steps, output_length;
    bool output_valid;
    const struct firmware *payload;
    bool load_armed;
    u8 runner_code[EXEC_FLASH_SIZE];
    struct pci_dev *pdev;
    void __iomem *bar;
    void *dma_buf;
    dma_addr_t dma;
    u32 saved_irq;
    u16 saved_command;
    bool stage_armed, stage_dirty;
    bool pending, pinned, pointer_armed, pointer_verified, runtime_verified, scratch_armed, scratch_dirty, dram_hook_armed, rom_table_armed, flash_map_armed, exec_armed, exec_dirty;
    const u8 *upload_data;
    u16 exec_expected_status;
    u16 exec_last_status;
    u32 audit_address, audit_length;
    u8 tag;
    struct dentry *directory;
    struct capture capture[54];
    struct capture stage[8];
    char result[65536];
    struct debugfs_blob_wrapper result_blob;
    size_t used;
};

#define record(d, fmt, ...) do { \
    (d)->used += scnprintf((d)->result + (d)->used, \
        sizeof((d)->result) - (d)->used, fmt, ##__VA_ARGS__); \
    dev_info(&(d)->pdev->dev, fmt, ##__VA_ARGS__); \
} while (0)

static unsigned int changed(const u8 *p, size_t n, u8 pattern)
{
    unsigned int count = 0;
    while (n--) if (*p++ != pattern) count++;
    return count;
}

static int issue(struct experiment *d, u8 opcode, u16 count, u32 offset,
                 u8 pattern, unsigned int slot)
{
    u32 input, output, words[3];
    u16 status, returned;
    int rc;
    unsigned int changes, guard;
    if (d->pending) return -EPERM;
    if (opcode != 0x1c && opcode != 0x20 && opcode != 0x21 && opcode != 0x6f) return -EPERM;
    if (opcode == 0x6f && (!d->exec_armed || !d->exec_dirty || count || offset)) return -EPERM;
    if (opcode == 0x21 && (!d->upload_data ||
        (!scratch_allowed(opcode,count,offset,d->runtime_verified,d->scratch_armed) &&
         !exec_upload_allowed(count,offset,d->runtime_verified,d->exec_armed) &&
         !load_upload_allowed(count,offset,d->payload->size,d->runtime_verified,d->load_armed)))) return -EPERM;
    if (opcode == 0x20 && !sp_allowed(count, offset, d->pointer_armed) &&
        !(runtime_check && sp_runtime_allowed(count, offset, d->pointer_verified) &&
          d->audit_length && count == d->audit_length &&
          offset == d->audit_address - STAGING_BASE) &&
        !sp_dram_hook_allowed(count, offset, d->runtime_verified, d->dram_hook_armed) &&
        !sp_rom_table_allowed(count, offset, d->runtime_verified, d->rom_table_armed) &&
        !(d->runtime_verified && d->flash_map_armed && count == 64 &&
          (offset == 0xfefb0200u - STAGING_BASE ||
           offset == 0xfefc8200u - STAGING_BASE ||
           offset == 0xfefe0000u - STAGING_BASE)) &&
        !exec_read_allowed(count, offset, d->runtime_verified, d->exec_armed) &&
        !scratch_allowed(opcode,count,offset,d->runtime_verified,d->scratch_armed)) return -EPERM;
    /* Unknown stale completions are refused, not attributed to this command. */
    output = readl(d->bar + ODB);
    if (output & 1) {
        record(d, "refused stale completion: ODB=%08x id=%04x status=%04x\n",
               output, readw(d->bar + STATUS_ID), readw(d->bar + STATUS));
        return -EBUSY;
    }
    rc = readl_poll_timeout(d->bar + IDB, input, !(input & 3), 50, WAIT_US);
    if (rc) { record(d, "refused busy/init input: IDB=%08x\n", input); return rc; }
    d->tag++;
    memset(d->dma_buf, pattern, DMA_SIZE);
    if (opcode == 0x21) memcpy(d->dma_buf, d->upload_data, count);
    words[0] = opcode | ((u32)d->tag << 8) | ((u32)count << 16);
    words[1] = offset;
    words[2] = lower_32_bits(d->dma);
    record(d, "submit op=%02x id=%u len=%u offset=%08x dma=%08x pattern=%02x mailbox=%08x,%08x,%08x,00\n",
           opcode, d->tag, count, offset, words[2], pattern, words[0], words[1], words[2]);
    writel(words[0], d->bar + MBOX);
    writel(words[1], d->bar + MBOX + 4);
    writel(words[2], d->bar + MBOX + 8);
    writeb(0, d->bar + MBOX + 12);
    dma_wmb();
    d->pending = true;
    writel(1, d->bar + IDB);
    rc = readl_poll_timeout(d->bar + ODB, output, output & 1, 50, WAIT_US);
    if (rc) {
        record(d, "uncertain completion: timeout ODB=%08x IDB=%08x; retaining DMA/module\n",
               output, readl(d->bar + IDB));
        return rc;
    }
    returned = readw(d->bar + STATUS_ID);
    status = readw(d->bar + STATUS);
    if ((returned & 0xff) != d->tag) {
        record(d, "uncertain completion: expected-id=%u observed-id=%04x status=%04x; retaining DMA/module\n",
               d->tag, returned, status);
        return -EPROTO;
    }
    dma_rmb();
    /* PG status consumption sequence, with 32-bit doorbell accesses. */
    writel(1, d->bar + ODB);
    writel(2, d->bar + IDB);
    readl(d->bar + IDB); /* flush posted acknowledgments */
    d->pending = false;
    changes = changed(d->dma_buf, opcode == 0x1c ? 512 : count, pattern);
    guard = changed((u8 *)d->dma_buf + (opcode == 0x1c ? 512 : count),
                    DMA_SIZE - (opcode == 0x1c ? 512 : count), pattern);
    record(d, "complete op=%02x id=%04x status=%04x changed=%u guard-changed=%u head=%*ph\n",
           opcode, returned, status, changes, guard, 16, d->dma_buf);
    /* ARRAY_SIZE is a deliberate no-small-capture slot for full-image reads. */
    if (slot < ARRAY_SIZE(d->capture))
        memcpy(d->capture[slot].data, d->dma_buf, d->capture[slot].blob.size);
    if (guard) return -EOVERFLOW;
    if (opcode == 0x6f) {
        d->exec_last_status = status;
        if (d->exec_expected_status == 0xffff)
            return (status == 0x0104 || status == 0x017d || status == 0x017e || status == 0x017f) ? 0 : -EIO;
        return status == d->exec_expected_status ? 0 : -EIO;
    }
    if (status) return -EIO;
    if (opcode == 0x1c) {
        const u8 *b = d->dma_buf;
        if (!changes || b[4] != 4 || b[5] != 7) {
            record(d, "Enquiry2 did not validate as firmware 4.07; refusing image read\n");
            return -ENODATA;
        }
    }
    return 0;
}

static int run_pointer(struct experiment *d)
{
    static const u8 prefix[16] = {0x50,0x4b,3,4,0x0a,0,0,0,6,0,0xf4,0x9d,0x82,0x27,0x90,0x2a};
    int rc;
    if (!sp_profile(d->capture[0].data)) return -EINVAL;
    rc = issue(d, 0x20, 512, 0, 0xa5, 4);
    if (rc) return rc;
    rc = issue(d, 0x20, 512, 0, 0x5a, 5);
    if (rc) return rc;
    if (memcmp(d->capture[4].data, prefix, sizeof(prefix)) ||
        memcmp(d->capture[4].data, d->capture[5].data, 512)) return -ENODATA;
    d->pointer_armed = true;
    rc = issue(d, 0x20, 4, POINTER_OFFSET, 0xa5, 1);
    if (rc) goto disarm;
    if (sp_word(d->capture[1].data) != STAGING_BASE) { rc = -ENODATA; goto disarm; }
    rc = issue(d, 0x20, 4, POINTER_OFFSET, 0x5a, 2);
    if (rc) goto disarm;
    if (sp_word(d->capture[2].data) != STAGING_BASE) { rc = -ENODATA; goto disarm; }
    d->pointer_armed = false;
    rc = issue(d, 0x1c, 0, 0, 0x5a, 3);
    if (!rc && !sp_profile(d->capture[3].data)) rc = -ENODATA;
    if (!rc) d->pointer_verified = true;
    if (!rc) record(d, "VERIFIED staging pointer=%08x at local=c0112a70\n", STAGING_BASE);
 disarm:
    d->pointer_armed = false;
    return rc;
}

static int read_pair(struct experiment *d, u32 address, u16 count, unsigned int slot)
{
    int rc;
    d->audit_address = address;
    d->audit_length = count;
    rc = issue(d, 0x20, count, address - STAGING_BASE, 0xa5, slot);
    if (!rc) rc = issue(d, 0x20, count, address - STAGING_BASE, 0x5a, slot+1);
    d->audit_length = 0;
    if (!rc && memcmp(d->capture[slot].data, d->capture[slot+1].data, count)) rc = -ENODATA;
    return rc;
}

static int run_runtime(struct experiment *d)
{
    static const u8 code[16] = {0x06,0x1e,0x80,0x5c,0x5c,0x27,0,9,0,0x30,0xf0,0x82,0x98,0x5d,0x0a,0xc0};
    u32 board, alias;
    int rc = read_pair(d, 0xc004a2e0, 16, 6);
    if (rc) return rc;
    if (memcmp(code, d->capture[6].data, 16)) return -ENODATA;
    rc = read_pair(d, 0xc011e22c, 8, 8);
    if (rc) return rc;
    board = sp_word(d->capture[8].data);
    alias = sp_word(d->capture[8].data+4);
    record(d, "runtime board=%08x alias=%08x\n", board, alias);
    if (board != 0xc0110780 || alias != 0xc1000000) return -ERANGE;
    rc = read_pair(d, board, 512, 10);
    if (rc) return rc;
    record(d, "runtime callbacks read=%08x write=%08x program=%08x\n",
           sp_word(d->capture[10].data+0xe0), sp_word(d->capture[10].data+0xe4),
           sp_word(d->capture[10].data+0xec));
    if (sp_word(d->capture[10].data+0xe0)!=0xc004ce90 ||
        sp_word(d->capture[10].data+0xe4)!=0xc004ced0 ||
        sp_word(d->capture[10].data+0xec)!=0xc004cf80) return -ENODATA;
    rc = issue(d, 0x1c, 0, 0, 0x5a, 3);
    if (!rc && !sp_profile(d->capture[3].data)) rc = -ENODATA;
    if (!rc) d->runtime_verified = true;
    return rc;
}

static int run_scratch(struct experiment *d)
{
    int rc, first_rc, restore_rc;
    if (!d->runtime_verified) return -EPERM;
    d->scratch_armed = true;
    rc = read_pair(d, STAGING_BASE + SCRATCH_REGION_OFFSET, SCRATCH_REGION_SIZE, 12);
    if (rc) goto done;
    if (scratch_matches(d->capture[12].data,d->capture[12].data,scratch_pattern)) {
        rc = -ENODATA; goto done; /* An already matching region cannot prove the write. */
    }
    d->upload_data = scratch_pattern;
    d->scratch_dirty = true; /* Conservative even if the submission later fails. */
    first_rc = issue(d, 0x21, SCRATCH_WRITE_SIZE, SCRATCH_WRITE_OFFSET, 0xa5, 18);
    if (d->pending) { rc = first_rc; goto done; }
    if (!first_rc) {
        first_rc = read_pair(d, STAGING_BASE+SCRATCH_REGION_OFFSET, SCRATCH_REGION_SIZE, 14);
        if (!first_rc && !scratch_matches(d->capture[12].data,d->capture[14].data,scratch_pattern))
            first_rc = -ENODATA;
    }
    if (d->pending) { rc = first_rc; goto done; }
    /* Restore after every known-complete write attempt, including failed validation. */
    d->upload_data = d->capture[12].data + 16;
    restore_rc = issue(d, 0x21, SCRATCH_WRITE_SIZE, SCRATCH_WRITE_OFFSET, 0x5a, 19);
    if (!restore_rc) restore_rc = read_pair(d, STAGING_BASE+SCRATCH_REGION_OFFSET, SCRATCH_REGION_SIZE, 16);
    if (!restore_rc && memcmp(d->capture[12].data,d->capture[16].data,SCRATCH_REGION_SIZE))
        restore_rc = -ENODATA;
    if (!restore_rc) {
        d->scratch_dirty = false;
        record(d, "RESTORED scratch region original 64 bytes\n");
    }
    rc = restore_rc ? restore_rc : first_rc;
    if (!rc) {
        rc = issue(d, 0x1c, 0, 0, 0x5a, 3);
        if (!rc && !sp_profile(d->capture[3].data)) rc = -ENODATA;
        if (!rc) record(d, "VERIFIED RAM scratch write/readback/restore local=c0fac010 length=16\n");
    }
 done:
    d->scratch_armed = false;
    d->upload_data = NULL;
    return rc;
}

static int run_dram_hook(struct experiment *d)
{
    int rc;
    if (!d->runtime_verified) return -EPERM;
    d->dram_hook_armed = true;
    rc = read_pair(d, DRAM_HOOK_ADDRESS, DRAM_HOOK_SIZE, 20);
    d->dram_hook_armed = false;
    if (!rc) record(d, "OBSERVED hook-site local=c0120000 length=64; occupancy is not ownership\n");
    return rc;
}

static int run_rom_table(struct experiment *d)
{
    int rc;
    if (!d->runtime_verified) return -EPERM;
    d->rom_table_armed = true;
    rc = read_pair(d, ROM_TABLE_ADDRESS, 4, 22);
    d->rom_table_armed = false;
    if (!rc && sp_word(d->capture[22].data) != 0xc001fe98u) rc = -ENODATA;
    if (!rc) record(d, "VERIFIED stock opcode-6f table word local=c001f9bc value=c001fe98; fetch/cache untested\n");
    return rc;
}

static int run_flash_map(struct experiment *d)
{
    int rc;
    if (!d->runtime_verified) return -EPERM;
    d->flash_map_armed = true;
    rc = read_pair(d, 0xfefb0200u, 64, 24);
    if (!rc) rc = read_pair(d, 0xfefc8200u, 64, 26);
    if (!rc) rc = read_pair(d, 0xfefe0000u, 64, 28);
    d->flash_map_armed = false;
    if (!rc) record(d, "OBSERVED paired live FEFB0200/FEFC8200/FEFE0000 windows; inspect captures against pinned image; instruction fetch untested\n");
    return rc;
}

static int exec_upload(struct experiment *d, const u8 *data, u16 count,
                       u32 offset, unsigned int slot)
{
    int rc;
    d->upload_data = data;
    rc = issue(d, 0x21, count, offset, 0xa5, slot);
    d->upload_data = NULL;
    return rc;
}

static int exec_region_matches(const u8 *before, const u8 *after,
                               const u8 *code, size_t code_size)
{
    return !memcmp(after, code, code_size) &&
           !memcmp(after + code_size, before + code_size,
                   EXEC_REGION_SIZE - code_size);
}

static int run_rom_exec(struct experiment *d)
{
    int rc = 0, test_rc = 0, restore_rc = 0, step;
    bool ram_attempted = false, flash_attempted = false, table_attempted = false;
    if (!d->runtime_verified) return -EPERM;
    d->exec_armed = true;
    rc = read_pair(d, EXEC_TABLE_ADDRESS, 4, 22);
    if (rc) goto done;
    if (sp_word(d->capture[22].data) != 0xc001fe98u) { rc = -ENODATA; goto done; }
    rc = read_pair(d, EXEC_RAM_ADDRESS, EXEC_REGION_SIZE, 24);
    if (rc) goto done;
    rc = read_pair(d, EXEC_FLASH_ADDRESS, EXEC_REGION_SIZE, 26);
    if (rc) goto done;
    if (!memcmp(d->capture[24].data, exec_ram_code, EXEC_RAM_SIZE) ||
        !memcmp(d->capture[26].data, exec_flash_code, EXEC_FLASH_SIZE)) {
        rc = -ENODATA; goto done;
    }

    d->exec_dirty = true; /* Conservative from the first possible RAM write. */
    ram_attempted = true;
    test_rc = exec_upload(d, exec_ram_code, EXEC_RAM_SIZE, EXEC_RAM_OFFSET, 28);
    if (d->pending || test_rc) goto restore;
    test_rc = read_pair(d, EXEC_RAM_ADDRESS, EXEC_REGION_SIZE, 29);
    if (test_rc || !exec_region_matches(d->capture[24].data, d->capture[29].data,
                                        exec_ram_code, EXEC_RAM_SIZE)) {
        if (!test_rc) test_rc = -ENODATA;
        goto restore;
    }
    table_attempted = true;
    test_rc = exec_upload(d, exec_ram_pointer, 4, EXEC_TABLE_OFFSET, 31);
    if (d->pending || test_rc) goto restore;
    test_rc = read_pair(d, EXEC_TABLE_ADDRESS, 4, 32);
    if (test_rc || sp_word(d->capture[32].data) != EXEC_RAM_ADDRESS) {
        if (!test_rc) test_rc = -ENODATA;
        goto restore;
    }
    d->exec_expected_status = 0x017e;
    test_rc = issue(d, 0x6f, 0, 0, 0xa5, 34);
    if (d->pending || test_rc) goto restore;
    record(d, "VERIFIED changed RAM dispatch word executed returning RAM stub status=017e\n");

    flash_attempted = true;
    test_rc = exec_upload(d, exec_flash_code, EXEC_FLASH_SIZE, EXEC_FLASH_OFFSET, 35);
    if (d->pending || test_rc) goto restore;
    test_rc = read_pair(d, EXEC_FLASH_ADDRESS, EXEC_REGION_SIZE, 36);
    if (test_rc || !exec_region_matches(d->capture[26].data, d->capture[36].data,
                                        exec_flash_code, EXEC_FLASH_SIZE)) {
        if (!test_rc) test_rc = -ENODATA;
        goto restore;
    }
    test_rc = exec_upload(d, exec_flash_pointer, 4, EXEC_TABLE_OFFSET, 38);
    if (d->pending || test_rc) goto restore;
    test_rc = read_pair(d, EXEC_TABLE_ADDRESS, 4, 39);
    if (test_rc || sp_word(d->capture[39].data) != EXEC_FLASH_ADDRESS) {
        if (!test_rc) test_rc = -ENODATA;
        goto restore;
    }
    d->exec_expected_status = 0xffff;
    test_rc = issue(d, 0x6f, 0, 0, 0x5a, 41);
    if (d->pending || test_rc) goto restore;
    if (d->exec_last_status == 0x017e) {
        d->exec_expected_status = 0x017f;
        test_rc = issue(d, 0x6f, 0, 0, 0xa5, 52);
        if (d->pending || test_rc) goto restore;
    } else if (d->exec_last_status != 0x017f) {
        test_rc = -ENODATA;
        goto restore;
    }
    record(d, "VERIFIED post-startup callx to mapped stock flash RET returned status=017f\n");

restore:
    if (d->pending) { rc = test_rc; goto done; }
    /* Restore dispatch before changing either code site. Try every restoration
     * after a known-complete failure; retain the module if any check fails. */
    if (table_attempted) {
        step = exec_upload(d, d->capture[22].data, 4, EXEC_TABLE_OFFSET, 42);
        if (d->pending) { rc = test_rc ? test_rc : step; goto done; }
        step = read_pair(d, EXEC_TABLE_ADDRESS, 4, 43);
        if (!step && memcmp(d->capture[22].data, d->capture[43].data, 4)) step = -ENODATA;
        if (step) { restore_rc = step; rc = test_rc ? test_rc : restore_rc; goto done; }
        d->exec_expected_status = 0xffff;
        step = issue(d, 0x6f, 0, 0, 0xa5, 51);
        if (step) { restore_rc = step; rc = test_rc ? test_rc : restore_rc; goto done; }
        if (d->exec_last_status != 0x0104) {
            d->exec_expected_status = 0x0104;
            step = issue(d, 0x6f, 0, 0, 0x5a, 53);
            if (step) { restore_rc = step; rc = test_rc ? test_rc : restore_rc; goto done; }
        }
        record(d, "VERIFIED restored stock dispatch status=0104 before clearing RAM stubs\n");
    }
    if (ram_attempted) {
        step = exec_upload(d, d->capture[24].data, EXEC_RAM_SIZE, EXEC_RAM_OFFSET, 45);
        if (d->pending) { rc = test_rc ? test_rc : step; goto done; }
        step = read_pair(d, EXEC_RAM_ADDRESS, EXEC_REGION_SIZE, 46);
        if (!step && memcmp(d->capture[24].data, d->capture[46].data, EXEC_REGION_SIZE)) step = -ENODATA;
        if (step && !restore_rc) restore_rc = step;
    }
    if (d->pending) { rc = test_rc ? test_rc : restore_rc; goto done; }
    if (flash_attempted) {
        step = exec_upload(d, d->capture[26].data, EXEC_FLASH_SIZE, EXEC_FLASH_OFFSET, 48);
        if (d->pending) { rc = test_rc ? test_rc : step; goto done; }
        step = read_pair(d, EXEC_FLASH_ADDRESS, EXEC_REGION_SIZE, 49);
        if (!step && memcmp(d->capture[26].data, d->capture[49].data, EXEC_REGION_SIZE)) step = -ENODATA;
        if (step && !restore_rc) restore_rc = step;
    }
    if (!restore_rc) {
        d->exec_dirty = false;
        record(d, "RESTORED dispatch and both RAM sites to their original bytes\n");
    }
    rc = restore_rc ? restore_rc : test_rc;
    if (!d->pending) {
        step = issue(d, 0x1c, 0, 0, 0x5a, 3);
        if (!step && !sp_profile(d->capture[3].data)) step = -ENODATA;
        if (!rc) rc = step;
    }
done:
    d->exec_armed = false;
    d->upload_data = NULL;
    return rc;
}

#include "stage_rehearsal.h"

static int run(struct experiment *d)
{
    int rc, image_rc = 0, post_rc;
    rc = issue(d, 0x1c, 0, 0, 0xa5, 0);
    if (rc) return rc;
    if (pointer_check) {
        rc = run_pointer(d);
        if (!rc && runtime_check) rc = run_runtime(d);
        if (!rc && dram_hook_check) rc = run_dram_hook(d);
        if (!rc && rom_table_check) rc = run_rom_table(d);
        if (!rc && flash_map_check) rc = run_flash_map(d);
        if (!rc && rom_exec_check) rc = run_rom_exec(d);
        if (!rc && scratch_check) rc = run_scratch(d);
        if (!rc && stage_check) rc = run_stage(d);
        return rc;
    }
    if (!attempt) return rc;
    image_rc = issue(d, 0x20, length, flash_offset, 0xa5, 1);
    if (d->pending) return image_rc;
    if (!image_rc) image_rc = issue(d, 0x20, length, flash_offset, 0x5a, 2);
    if (d->pending) return image_rc;
    post_rc = issue(d, 0x1c, 0, 0, 0x5a, 3);
    if (post_rc) return post_rc;
    if (image_rc) return image_rc;
    if (memcmp(d->capture[1].data, d->capture[2].data, length)) {
        record(d, "NO VERIFIED TRANSFER: captures differ with sentinel pattern\n");
        return -ENODATA;
    }
    record(d, "candidate read: repeated captures match; still requires image/coverage validation\n");
    return 0;
}

static const struct pci_device_id ids[] = {
    { PCI_DEVICE(0x1069, 0x0010) }, { }
};
MODULE_DEVICE_TABLE(pci, ids);

static void free_captures(struct experiment *d)
{
    unsigned int i;
    for (i = 0; i < 54; i++) kfree(d->capture[i].data);
    for (i = 0; i < ARRAY_SIZE(d->stage); i++) kvfree(d->stage[i].data);
}

/* A file reference owns the session. Synchronous operations serialize with
 * release/remove; file_operations.owner holds the module through final close.
 * An uncertain transaction additionally pins module/DMA until reboot. */
static void session_free(struct kref *ref)
{
    struct experiment *d=container_of(ref,struct experiment,refs);
    free_captures(d);release_firmware(d->payload);kfree(d);
}
static void session_pin(struct experiment *d)
{
    if(!d->pinned && (d->pending || d->exec_dirty || d->stage_dirty)) {
        __module_get(THIS_MODULE);pci_dev_get(d->pdev);d->pinned=true;
        record(d,"SESSION FAILED: retained DMA/module; reboot required\n");
    }
}
static void session_log_start(struct experiment *d)
{ d->used=0;d->result[0]=0; }
static void session_log_end(struct experiment *d)
{ d->result_blob.size=d->used; }
static int session_file_open(struct inode *inode,struct file *file)
{
    struct miscdevice *misc=file->private_data;
    struct experiment *d=container_of(misc,struct experiment,misc);
    int rc;
    mutex_lock(&d->session_lock);
    if(d->owned || d->removed || d->pinned) {rc=-EBUSY;goto out;}
    session_log_start(d);d->sequence=0;d->response_ready=false;
    rc=session_open(d);
    if(rc) {session_close(d);session_pin(d);}
    else {kref_get(&d->refs);d->owned=true;file->private_data=d;}
    session_log_end(d);
out:
    mutex_unlock(&d->session_lock);return rc;
}
static ssize_t session_file_write(struct file *file,const char __user *buf,size_t count,loff_t *pos)
{
    struct experiment *d=file->private_data;u8 *request;int rc;
    if(count!=BIO_SIZE) return -EINVAL;
    request=memdup_user(buf,count);if(IS_ERR(request)) return PTR_ERR(request);
    mutex_lock(&d->session_lock);
    if(d->removed || !d->ready || d->pinned) {rc=-EIO;goto out;}
    if(d->response_ready) {rc=-EBUSY;goto out;}
    if(!bio_request_valid(request) || bio_word(request+8)<=d->sequence) {rc=-EINVAL;goto out;}
    session_log_start(d);rc=session_step(d,request);
    if(rc) {d->ready=false;session_close(d);session_pin(d);}
    else {
        d->response_ready=true;
        d->stage[6].blob.size=d->output_length;d->stage[7].blob.size=d->output_length;
    }
    session_log_end(d);
out:
    mutex_unlock(&d->session_lock);kfree(request);return rc?rc:count;
}
static ssize_t session_file_read(struct file *file,char __user *buf,size_t count,loff_t *pos)
{
    struct experiment *d=file->private_data;int rc;
    if(count!=BIO_SIZE) return -EINVAL;
    mutex_lock(&d->session_lock);
    if(d->removed || d->pinned) rc=-EIO;
    else if(!d->response_ready) rc=-EAGAIN;
    else if(copy_to_user(buf,d->stage[6].data+BIO_OFFSET,BIO_SIZE)) rc=-EFAULT;
    else {d->response_ready=false;rc=BIO_SIZE;}
    mutex_unlock(&d->session_lock);return rc;
}
static int session_file_release(struct inode *inode,struct file *file)
{
    struct experiment *d=file->private_data;int rc=0;
    mutex_lock(&d->session_lock);
    if(!d->removed && !d->pinned) {
        session_log_start(d);rc=session_close(d);session_pin(d);session_log_end(d);
    }
    d->owned=false;
    mutex_unlock(&d->session_lock);
    kref_put(&d->refs,session_free);
    return rc;
}
static const struct file_operations session_fops={
    .owner=THIS_MODULE,.open=session_file_open,.write=session_file_write,
    .read=session_file_read,.release=session_file_release,.llseek=no_llseek,
};

static int probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    static const char *names[] = {
        "enquiry-before.bin", "read-a5.bin", "read-5a.bin", "enquiry-after.bin",
        "control-a5.bin", "control-5a.bin", "code-a5.bin", "code-5a.bin",
        "globals-a5.bin", "globals-5a.bin", "board-a5.bin", "board-5a.bin",
        "scratch-before-a5.bin", "scratch-before-5a.bin", "scratch-test-a5.bin",
        "scratch-test-5a.bin", "scratch-restored-a5.bin", "scratch-restored-5a.bin",
        "upload-test.bin", "upload-restore.bin", "dram-hook-a5.bin", "dram-hook-5a.bin",
        "rom-table-a5.bin", "rom-table-5a.bin",
        "exec-ram-before-a5.bin", "exec-ram-before-5a.bin",
        "exec-flash-before-a5.bin", "exec-flash-before-5a.bin",
        "exec-ram-upload.bin", "exec-ram-after-a5.bin", "exec-ram-after-5a.bin",
        "exec-table-ram-upload.bin", "exec-table-ram-a5.bin", "exec-table-ram-5a.bin",
        "exec-ram-completion.bin", "exec-flash-upload.bin",
        "exec-flash-after-a5.bin", "exec-flash-after-5a.bin",
        "exec-table-flash-upload.bin", "exec-table-flash-a5.bin", "exec-table-flash-5a.bin",
        "exec-flash-completion.bin", "exec-table-restore-upload.bin",
        "exec-table-restored-a5.bin", "exec-table-restored-5a.bin",
        "exec-ram-restore-upload.bin", "exec-ram-restored-a5.bin", "exec-ram-restored-5a.bin",
        "exec-flash-restore-upload.bin", "exec-flash-restored-a5.bin",
        "exec-flash-restored-5a.bin", "exec-stock-completion.bin",
        "exec-flash-followup.bin", "exec-stock-followup.bin"
    };
    struct experiment *d;
    unsigned int i;
    int rc;
    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;
    if (!stage_check || !firmware_name) return -EINVAL;
    if (stage_check && (!runtime_check || scratch_check || dram_hook_check ||
                        rom_table_check || rom_exec_check || flash_map_check)) return -EINVAL;
    if (scratch_check && !runtime_check) return -EINVAL;
    if (dram_hook_check && (!runtime_check || scratch_check)) return -EINVAL;
    if (rom_table_check && (!runtime_check || scratch_check || dram_hook_check || rom_exec_check || flash_map_check)) return -EINVAL;
    if (rom_exec_check && (!runtime_check || scratch_check || dram_hook_check || rom_table_check || flash_map_check)) return -EINVAL;
    if (flash_map_check && (!runtime_check || scratch_check || dram_hook_check || rom_table_check || rom_exec_check)) return -EINVAL;
    if (runtime_check && !pointer_check) return -EINVAL;
    if (pointer_check && (attempt || length != 512 || flash_offset)) return -EINVAL;
    if (!length || length > MAX_READ || (length & 3) ||
        (flash_offset & 3) || flash_offset > IMAGE_WINDOW - length) return -EINVAL;
    if (!(pci_resource_flags(pdev, 0) & IORESOURCE_MEM) ||
        pci_resource_len(pdev, 0) < 0x2000) return -ENODEV;
    d = kzalloc(sizeof(*d), GFP_KERNEL);
    if (!d) return -ENOMEM;
    d->pdev = pdev;
    mutex_init(&d->session_lock);
    kref_init(&d->refs);
    rc = request_firmware(&d->payload, firmware_name, &pdev->dev);
    if (rc) goto free_state;
    if (d->payload->size > LOAD_MAX || !load_valid(d->payload->size, entry_offset)) { rc=-EINVAL; goto free_state; }
    if (buffer_io && (d->payload->size != BIO_IMAGE_SIZE || entry_offset >= 0x20000u ||
        payload_argument != BIO_BASE || !bio_request_valid(d->payload->data+BIO_OFFSET))) {
        rc=-EINVAL; goto free_state;
    }
    pci_read_config_word(pdev, PCI_COMMAND, &d->saved_command);
    rc = pci_enable_device(pdev);
    if (rc) goto free_state;
    rc = pci_request_regions(pdev, "dac960rtems");
    if (rc) goto disable;
    rc = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
    if (rc) goto release;
    d->bar = pci_iomap(pdev, 0, 0x2000);
    if (!d->bar) { rc = -ENOMEM; goto release; }
    d->dma_buf = dma_alloc_coherent(&pdev->dev, DMA_SIZE, &d->dma, GFP_KERNEL);
    if (!d->dma_buf) { rc = -ENOMEM; goto unmap; }
    for (i = 0; i < 54; i++) {
        d->capture[i].blob.size = (i == 1 || i == 2) ? (pointer_check ? 4 : length) : 512;
        if (i == 6 || i == 7) d->capture[i].blob.size = 16;
        if (i == 8 || i == 9) d->capture[i].blob.size = 8;
        if (i >= 12 && i <= 17) d->capture[i].blob.size = SCRATCH_REGION_SIZE;
        if (i >= 18) d->capture[i].blob.size = SCRATCH_WRITE_SIZE;
        if (i >= 20) d->capture[i].blob.size = DRAM_HOOK_SIZE;
        if (i >= 22) d->capture[i].blob.size = 4;
        if (i >= 24) d->capture[i].blob.size = EXEC_REGION_SIZE;
        if (i == 28 || i == 45) d->capture[i].blob.size = EXEC_RAM_SIZE;
        if (i == 35 || i == 48) d->capture[i].blob.size = EXEC_FLASH_SIZE;
        if (flash_map_check && i >= 24 && i <= 29) d->capture[i].blob.size = 64;
        if (i == 31 || i == 32 || i == 33 || i == 38 || i == 39 || i == 40 ||
            i == 42 || i == 43 || i == 44) d->capture[i].blob.size = 4;
        if (i == 34 || i == 41 || i == 51 || i == 52 || i == 53)
            d->capture[i].blob.size = 16;
        if (i == 20 || i == 21) d->capture[i].blob.size = 16;
        d->capture[i].data = kzalloc(d->capture[i].blob.size, GFP_KERNEL);
        if (!d->capture[i].data) { rc = -ENOMEM; goto free_dma; }
        d->capture[i].blob.data = d->capture[i].data;
    }
    if (stage_check) {
        for (i = 0; i < ARRAY_SIZE(d->stage); i++) {
            d->stage[i].data = kvzalloc(IMAGE_WINDOW, GFP_KERNEL);
            if (!d->stage[i].data) { rc = -ENOMEM; goto free_dma; }
            d->stage[i].blob.data = d->stage[i].data;
            d->stage[i].blob.size = IMAGE_WINDOW;
        }
    }
    d->saved_irq = readl(d->bar + IRQMASK);
    pci_set_master(pdev);
    writel(~0u, d->bar + IRQMASK);
    readl(d->bar + IRQMASK);
    record(d, "bdf=%s attempt=%u length=%u offset=%08x saved-irq=%08x\n",
           pci_name(pdev), attempt, length, flash_offset, d->saved_irq);
    rc = run(d);
    record(d, "experiment-result=%d pending=%u; exported files are captures, not a physical-flash backup\n", rc, d->pending);
    record(d, "scratch-dirty=%u\n", d->scratch_dirty);
    record(d, "exec-dirty=%u\n", d->exec_dirty);
    record(d, "stage-dirty=%u\n", d->stage_dirty);
    if (d->pending || d->scratch_dirty || d->exec_dirty || d->stage_dirty) {
        __module_get(THIS_MODULE);
        d->pinned = true;
        pci_dev_get(pdev);
        record(d, "REBOOT REQUIRED before unloading/unbinding or reusing controller; DMA retained\n");
    }
    /* Even a negative experiment stays bound until captures are collected. */
    pci_set_drvdata(pdev, d);
    d->directory = debugfs_create_dir("dac960rtems", NULL);
    d->result_blob.data = d->result;
    d->result_blob.size = d->used;
    debugfs_create_blob("result.txt", 0400, d->directory, &d->result_blob);
    for (i = 0; i < 54; i++) {
        const char *name = names[i];
        if (flash_map_check && i == 24) name = "fefb0200-a5.bin";
        if (flash_map_check && i == 25) name = "fefb0200-5a.bin";
        if (flash_map_check && i == 26) name = "fefc8200-a5.bin";
        if (flash_map_check && i == 27) name = "fefc8200-5a.bin";
        if (flash_map_check && i == 28) name = "fefe0000-a5.bin";
        if (flash_map_check && i == 29) name = "fefe0000-5a.bin";
        debugfs_create_blob(name, 0400, d->directory, &d->capture[i].blob);
    }
    if (stage_check) {
        static const char * const stage_names[] = {
            "stage-before-a5.bin", "stage-before-5a.bin",
            "stage-candidate-a5.bin", "stage-candidate-5a.bin",
            "stage-restored-a5.bin", "stage-restored-5a.bin",
            "payload-after-a5.bin", "payload-after-5a.bin"
        };
        for (i = 0; i < ARRAY_SIZE(d->stage); i++)
            debugfs_create_blob(stage_names[i], 0400, d->directory, &d->stage[i].blob);
    }
    if(!rc && !d->pinned) {
        d->misc.minor=MISC_DYNAMIC_MINOR;d->misc.name="i960-rtems";
        d->misc.fops=&session_fops;d->misc.mode=0600;
        rc=misc_register(&d->misc);
        if(rc) record(d,"misc_register failed=%d\n",rc);
        else d->misc_registered=true;
    }
    return 0;
 free_dma:
    free_captures(d);
    dma_free_coherent(&pdev->dev, DMA_SIZE, d->dma_buf, d->dma);
 unmap:
    pci_iounmap(pdev, d->bar);
 release:
    pci_release_regions(pdev);
 disable:
    pci_disable_device(pdev);
    pci_write_config_word(pdev, PCI_COMMAND, d->saved_command);
 free_state:
    if (d->payload) release_firmware(d->payload);
    kfree(d);
    return rc;
}

static void remove(struct pci_dev *pdev)
{
    struct experiment *d=pci_get_drvdata(pdev);
    if(d->misc_registered) misc_deregister(&d->misc);
    mutex_lock(&d->session_lock);
    if(d->owned && !d->pinned) {session_close(d);session_pin(d);}
    d->removed=true;
    debugfs_remove_recursive(d->directory);
    if(d->pending || d->exec_dirty || d->stage_dirty) {
        session_pin(d);mutex_unlock(&d->session_lock);return;
    }
    writel(d->saved_irq,d->bar+IRQMASK);readl(d->bar+IRQMASK);
    dma_free_coherent(&pdev->dev,DMA_SIZE,d->dma_buf,d->dma);
    pci_iounmap(pdev,d->bar);pci_release_regions(pdev);pci_disable_device(pdev);
    pci_write_config_word(pdev,PCI_COMMAND,d->saved_command);
    mutex_unlock(&d->session_lock);kref_put(&d->refs,session_free);
}
static struct pci_driver dac960rtems_driver = {
    .name = "dac960rtems", .id_table = ids, .probe = probe, .remove = remove,
};
static int __init load_init(void)
{
    if (!buffer_io || !firmware_name || !stage_check || !pointer_check || !runtime_check ||
        scratch_check || rom_exec_check || rom_table_check || dram_hook_check || flash_map_check || attempt)
        return -EINVAL;
    return pci_register_driver(&dac960rtems_driver);
}
static void __exit load_exit(void) { pci_unregister_driver(&dac960rtems_driver); }
module_init(load_init);
module_exit(load_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Controlled DAC960PG Enquiry2/LoadImage capture experiment");

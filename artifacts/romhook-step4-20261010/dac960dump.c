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
#include "staging_pointer.h"
#include "ram_scratch.h"

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
    struct pci_dev *pdev;
    void __iomem *bar;
    void *dma_buf;
    dma_addr_t dma;
    u32 saved_irq;
    u16 saved_command;
    bool pending, pinned, pointer_armed, pointer_verified, runtime_verified, scratch_armed, scratch_dirty, dram_hook_armed, rom_table_armed;
    const u8 *upload_data;
    u32 audit_address, audit_length;
    u8 tag;
    struct dentry *directory;
    struct capture capture[24];
    char result[16384];
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
    if (opcode != 0x1c && opcode != 0x20 && opcode != 0x21) return -EPERM;
    if (opcode == 0x21 && (!d->upload_data ||
        !scratch_allowed(opcode,count,offset,d->runtime_verified,d->scratch_armed))) return -EPERM;
    if (opcode == 0x20 && !sp_allowed(count, offset, d->pointer_armed) &&
        !(runtime_check && sp_runtime_allowed(count, offset, d->pointer_verified) &&
          d->audit_length && count == d->audit_length &&
          offset == d->audit_address - STAGING_BASE) &&
        !sp_dram_hook_allowed(count, offset, d->runtime_verified, d->dram_hook_armed) &&
        !sp_rom_table_allowed(count, offset, d->runtime_verified, d->rom_table_armed) &&
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
    if (opcode == 0x21) memcpy(d->dma_buf, d->upload_data, SCRATCH_WRITE_SIZE);
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
    memcpy(d->capture[slot].data, d->dma_buf, d->capture[slot].blob.size);
    if (guard) return -EOVERFLOW;
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
        if (!rc && scratch_check) rc = run_scratch(d);
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
    for (i = 0; i < 24; i++) kfree(d->capture[i].data);
}

static int probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    static const char *names[] = {"enquiry-before.bin", "read-a5.bin", "read-5a.bin", "enquiry-after.bin", "control-a5.bin", "control-5a.bin", "code-a5.bin", "code-5a.bin", "globals-a5.bin", "globals-5a.bin", "board-a5.bin", "board-5a.bin", "scratch-before-a5.bin", "scratch-before-5a.bin", "scratch-test-a5.bin", "scratch-test-5a.bin", "scratch-restored-a5.bin", "scratch-restored-5a.bin", "upload-test.bin", "upload-restore.bin", "dram-hook-a5.bin", "dram-hook-5a.bin", "rom-table-a5.bin", "rom-table-5a.bin"};
    struct experiment *d;
    unsigned int i;
    int rc;
    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;
    if (scratch_check && !runtime_check) return -EINVAL;
    if (dram_hook_check && (!runtime_check || scratch_check)) return -EINVAL;
    if (rom_table_check && (!runtime_check || scratch_check || dram_hook_check)) return -EINVAL;
    if (runtime_check && !pointer_check) return -EINVAL;
    if (pointer_check && (attempt || length != 512 || flash_offset)) return -EINVAL;
    if (!length || length > MAX_READ || (length & 3) ||
        (flash_offset & 3) || flash_offset > IMAGE_WINDOW - length) return -EINVAL;
    if (!(pci_resource_flags(pdev, 0) & IORESOURCE_MEM) ||
        pci_resource_len(pdev, 0) < 0x2000) return -ENODEV;
    d = kzalloc(sizeof(*d), GFP_KERNEL);
    if (!d) return -ENOMEM;
    d->pdev = pdev;
    pci_read_config_word(pdev, PCI_COMMAND, &d->saved_command);
    rc = pci_enable_device(pdev);
    if (rc) goto free_state;
    rc = pci_request_regions(pdev, "dac960dump");
    if (rc) goto disable;
    rc = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
    if (rc) goto release;
    d->bar = pci_iomap(pdev, 0, 0x2000);
    if (!d->bar) { rc = -ENOMEM; goto release; }
    d->dma_buf = dma_alloc_coherent(&pdev->dev, DMA_SIZE, &d->dma, GFP_KERNEL);
    if (!d->dma_buf) { rc = -ENOMEM; goto unmap; }
    for (i = 0; i < 24; i++) {
        d->capture[i].blob.size = (i == 1 || i == 2) ? (pointer_check ? 4 : length) : 512;
        if (i == 6 || i == 7) d->capture[i].blob.size = 16;
        if (i == 8 || i == 9) d->capture[i].blob.size = 8;
        if (i >= 12 && i <= 17) d->capture[i].blob.size = SCRATCH_REGION_SIZE;
        if (i >= 18) d->capture[i].blob.size = SCRATCH_WRITE_SIZE;
        if (i >= 20) d->capture[i].blob.size = DRAM_HOOK_SIZE;
        if (i >= 22) d->capture[i].blob.size = 4;
        d->capture[i].data = kzalloc(d->capture[i].blob.size, GFP_KERNEL);
        if (!d->capture[i].data) { rc = -ENOMEM; goto free_dma; }
        d->capture[i].blob.data = d->capture[i].data;
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
    if (d->pending || d->scratch_dirty) {
        __module_get(THIS_MODULE);
        d->pinned = true;
        pci_dev_get(pdev);
        record(d, "REBOOT REQUIRED before unloading/unbinding or reusing controller; DMA retained\n");
    }
    /* Even a negative experiment stays bound until captures are collected. */
    pci_set_drvdata(pdev, d);
    d->directory = debugfs_create_dir("dac960dump", NULL);
    d->result_blob.data = d->result;
    d->result_blob.size = d->used;
    debugfs_create_blob("result.txt", 0400, d->directory, &d->result_blob);
    for (i = 0; i < 24; i++) debugfs_create_blob(names[i], 0400, d->directory, &d->capture[i].blob);
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
    kfree(d);
    return rc;
}

static void remove(struct pci_dev *pdev)
{
    struct experiment *d = pci_get_drvdata(pdev);
    debugfs_remove_recursive(d->directory);
    if (d->pending || d->scratch_dirty) {
        /* Userspace unbind can bypass a pinned module. Deliberately keep the
         * allocation/mapping/regions/device reference alive; never free memory
         * the controller might still target. Only reboot reclaims this state. */
        dev_err(&pdev->dev, "uncertain DMA: retained allocation/regions; reboot before reuse\n");
        return;
    }
    writel(d->saved_irq, d->bar + IRQMASK);
    readl(d->bar + IRQMASK);
    dma_free_coherent(&pdev->dev, DMA_SIZE, d->dma_buf, d->dma);
    pci_iounmap(pdev, d->bar);
    pci_release_regions(pdev);
    pci_disable_device(pdev);
    pci_write_config_word(pdev, PCI_COMMAND, d->saved_command);
    free_captures(d);
    kfree(d);
}
static struct pci_driver dac960dump_driver = {
    .name = "dac960dump", .id_table = ids, .probe = probe, .remove = remove,
};
module_pci_driver(dac960dump_driver);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Controlled DAC960PG Enquiry2/LoadImage capture experiment");

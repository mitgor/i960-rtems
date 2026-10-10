// SPDX-License-Identifier: GPL-2.0
/* Controlled PG response experiment. Only Enquiry2 (0x1c) and LoadImage (0x20).
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
    bool pending, pinned;
    u8 tag;
    struct dentry *directory;
    struct capture capture[4];
    char result[4096];
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
    if (d->pending || (opcode != 0x1c && opcode != 0x20)) return -EPERM;
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

static int run(struct experiment *d)
{
    int rc, image_rc = 0, post_rc;
    rc = issue(d, 0x1c, 0, 0, 0xa5, 0);
    if (rc || !attempt) return rc;
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
    for (i = 0; i < 4; i++) kfree(d->capture[i].data);
}

static int probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    static const char *names[] = {"enquiry-before.bin", "read-a5.bin", "read-5a.bin", "enquiry-after.bin"};
    struct experiment *d;
    unsigned int i;
    int rc;
    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;
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
    for (i = 0; i < 4; i++) {
        d->capture[i].blob.size = (i == 1 || i == 2) ? length : 512;
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
    if (d->pending) {
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
    for (i = 0; i < 4; i++) debugfs_create_blob(names[i], 0400, d->directory, &d->capture[i].blob);
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
    if (d->pending) {
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

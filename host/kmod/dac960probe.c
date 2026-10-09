// SPDX-License-Identifier: GPL-2.0
/* dac960probe - minimal PCI driver for the Mylex DAC960 (i960) controller.
 * Issues ONE V1 command through the PG hardware mailbox using the kernel DMA
 * API (IOMMU-correct), bounded polling (cannot wedge). Prints a result summary.
 *
 *   insmod dac960probe.ko cmd=0x1c            # Enquiry2 (read-only, default)
 *   insmod dac960probe.ko cmd=0x21 bufkb=512  # StoreImage probe (non-burn)
 *
 * SAFETY INTERLOCK: refuses cmd=0x22 (ProgramImage = the flash burn). This tool
 * never writes flash. StoreImage(0x21) does not burn flash; worst case it does
 * nothing or an over-size DMA faults harmlessly under the IOMMU.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/slab.h>

#define PG_IDB 0x0020
#define PG_ODB 0x002C
#define PG_IRQM 0x0034
#define PG_CMD 0x1000
#define PG_SID 0x1018
#define PG_STS 0x101A

static int cmd = 0x1c;
static int bufkb = 4;
module_param(cmd, int, 0444);
module_param(bufkb, int, 0444);

static const struct pci_device_id ids[] = { { PCI_DEVICE(0x1069, 0x0010) }, { 0 } };
MODULE_DEVICE_TABLE(pci, ids);

static int probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
	void __iomem *bar; void *buf; dma_addr_t dma;
	u32 w0, w2; int i, rc; u16 status; u8 *b;
	size_t len = (size_t)bufkb * 1024, changed = 0; int first = -1, last = -1, sig55aa = 0, printable = 0;

	if (cmd == 0x22) { dev_err(&pdev->dev, "REFUSED: cmd 0x22 (ProgramImage/flash burn) is interlocked\n"); return -EPERM; }

	rc = pci_enable_device(pdev); if (rc) return rc;
	pci_set_master(pdev);
	rc = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
	if (rc) goto err_dis;
	bar = pci_iomap(pdev, 0, 0x2000); if (!bar) { rc = -ENOMEM; goto err_dis; }
	buf = dma_alloc_coherent(&pdev->dev, len, &dma, GFP_KERNEL);
	if (!buf) { dev_err(&pdev->dev, "dma_alloc_coherent(%zu) failed\n", len); rc = -ENOMEM; goto err_unmap; }
	memset(buf, 0x5a, len);                         /* sentinel */

	dev_info(&pdev->dev, "cmd=0x%02x bufkb=%d iova=%pad\n", cmd, bufkb, &dma);
	iowrite8(0xff, bar + PG_IRQM);
	for (i = 0; i < 100000 && (ioread8(bar + PG_IDB) & 0x01); i++) udelay(10);

	w0 = (cmd & 0xff) | (0x01 << 8);                /* Type3: opcode + id */
	w2 = (u32)dma;                                  /* BusAddress @ bytes 8-11 */
	iowrite32(w0, bar + PG_CMD + 0);
	iowrite32(0,  bar + PG_CMD + 4);
	iowrite32(w2, bar + PG_CMD + 8);
	iowrite8(0,   bar + PG_CMD + 12);
	wmb();
	iowrite8(0x01, bar + PG_IDB);                   /* new command */

	for (i = 0; i < 500000; i++) { if (ioread8(bar + PG_ODB) & 0x01) break; udelay(10); }
	if (!(ioread8(bar + PG_ODB) & 0x01)) { dev_warn(&pdev->dev, "TIMEOUT (no status) for cmd 0x%02x\n", cmd); goto done; }
	status = ioread16(bar + PG_STS);
	iowrite8(0x01, bar + PG_ODB);
	iowrite8(0x02, bar + PG_IDB);

	b = buf;
	for (i = 0; i < len; i++) if (b[i] != 0x5a) { changed++; if (first < 0) first = i; last = i; }
	for (i = 0; i + 1 < len; i++) if (b[i] == 0x55 && b[i+1] == 0xaa) sig55aa++;
	for (i = 0; i < len && i < 4096; i++) if (b[i] >= 0x20 && b[i] < 0x7f) printable++;

	dev_info(&pdev->dev, "status=0x%04x  changed=%zu/%zu bytes  first=%d last=%d  55aa_count=%d printable(first4k)=%d\n",
		 status, changed, len, first, last, sig55aa, printable);
	dev_info(&pdev->dev, "buf[0..31]: %02x %02x %02x %02x %02x %02x %02x %02x  %02x %02x %02x %02x %02x %02x %02x %02x  %02x %02x %02x %02x %02x %02x %02x %02x  %02x %02x %02x %02x %02x %02x %02x %02x\n",
		 b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9],b[10],b[11],b[12],b[13],b[14],b[15],
		 b[16],b[17],b[18],b[19],b[20],b[21],b[22],b[23],b[24],b[25],b[26],b[27],b[28],b[29],b[30],b[31]);
done:
	dma_free_coherent(&pdev->dev, len, buf, dma);
err_unmap:
	pci_iounmap(pdev, bar);
err_dis:
	return rc ? rc : 0;
}
static void remove(struct pci_dev *pdev) { pci_disable_device(pdev); }
static struct pci_driver drv = { .name="dac960probe", .id_table=ids, .probe=probe, .remove=remove };
module_pci_driver(drv);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("DAC960/i960 PG mailbox probe (Enquiry/StoreImage), burn-interlocked");

// SPDX-License-Identifier: GPL-2.0
/* dac960probe - minimal PCI driver for the Mylex DAC960 (i960) controller.
 * Milestone 1: issue the read-only V1 Enquiry2 command through the PG hardware
 * mailbox (BAR0) using the kernel DMA API (IOMMU-correct), with BOUNDED polling
 * so it can never wedge like myrb did. Prints the firmware version to dmesg.
 *
 * Load:  sudo insmod dac960probe.ko [opcode=0x1c]
 * See:   sudo dmesg | tail
 * Unload: sudo rmmod dac960probe
 * Read-only on the card: Enquiry/Enquiry2 only fetch controller info.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/delay.h>
#include <linux/io.h>

/* PG register offsets within BAR0 */
#define PG_IDB   0x0020  /* inbound doorbell  */
#define PG_ODB   0x002C  /* outbound doorbell */
#define PG_IRQM  0x0034  /* interrupt mask    */
#define PG_CMD   0x1000  /* command mailbox (13 bytes) */
#define PG_SID   0x1018  /* status command id */
#define PG_STS   0x101A  /* status word */
#define PG_WIN   0x2000

/* doorbell bits */
#define IDB_NEWCMD     0x01
#define IDB_ACKSTS     0x02
#define ODB_STS_AVAIL  0x01
#define ODB_ACK_IRQ    0x01

static int opcode = 0x1c;              /* Enquiry2 */
module_param(opcode, int, 0444);

static const struct pci_device_id ids[] = {
	{ PCI_DEVICE(0x1069, 0x0010) },
	{ 0 }
};
MODULE_DEVICE_TABLE(pci, ids);

static int probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
	void __iomem *bar;
	void *buf; dma_addr_t dma;
	u32 w0, w2; int i, rc;
	u16 status; u8 *b;

	rc = pci_enable_device(pdev);
	if (rc) return rc;
	pci_set_master(pdev);
	rc = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
	if (rc) { dev_err(&pdev->dev, "no 32-bit DMA\n"); goto err_dis; }

	bar = pci_iomap(pdev, 0, PG_WIN);
	if (!bar) { rc = -ENOMEM; goto err_dis; }

	buf = dma_alloc_coherent(&pdev->dev, 4096, &dma, GFP_KERNEL);
	if (!buf) { rc = -ENOMEM; goto err_unmap; }
	memset(buf, 0, 4096);

	dev_info(&pdev->dev, "BAR0=%p dma_buf iova=%pad irqmask=0x%02x idb=0x%02x\n",
		 bar, &dma, ioread8(bar + PG_IRQM), ioread8(bar + PG_IDB));

	iowrite8(0xff, bar + PG_IRQM);           /* mask interrupts; we poll */

	/* wait until mailbox not full (bounded) */
	for (i = 0; i < 100000 && (ioread8(bar + PG_IDB) & 0x01); i++) udelay(10);

	/* Type3 mailbox: op@0, id@1, BusAddress@8..11 */
	w0 = (opcode & 0xff) | (0x01 << 8);      /* opcode + command id 1 */
	w2 = (u32)dma;                           /* BusAddress (DMA target) */
	iowrite32(w0, bar + PG_CMD + 0);
	iowrite32(0,  bar + PG_CMD + 4);
	iowrite32(w2, bar + PG_CMD + 8);
	iowrite8(0,   bar + PG_CMD + 12);
	wmb();
	iowrite8(IDB_NEWCMD, bar + PG_IDB);      /* ring doorbell */

	/* bounded wait for status-available */
	for (i = 0; i < 200000; i++) {
		if (ioread8(bar + PG_ODB) & ODB_STS_AVAIL) break;
		udelay(10);
	}
	if (!(ioread8(bar + PG_ODB) & ODB_STS_AVAIL)) {
		dev_warn(&pdev->dev, "opcode 0x%02x: TIMEOUT, no status\n", opcode);
		goto done;
	}
	status = ioread16(bar + PG_STS);
	iowrite8(ODB_ACK_IRQ, bar + PG_ODB);     /* ack */
	iowrite8(IDB_ACKSTS,  bar + PG_IDB);

	b = buf;
	dev_info(&pdev->dev, "opcode 0x%02x -> status=0x%04x\n", opcode, status);
	dev_info(&pdev->dev, "  result[0..15]: %02x %02x %02x %02x %02x %02x %02x %02x  %02x %02x %02x %02x %02x %02x %02x %02x\n",
		 b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9],b[10],b[11],b[12],b[13],b[14],b[15]);
	if (opcode == 0x1c)   /* Enquiry2: HW id @0-3, FW id @4-7 */
		dev_info(&pdev->dev, "  HardwareID submodel=%u model=%u | Firmware v%u.%02u-%u type=%u\n",
			 b[0], b[2], b[4], b[5], b[6], b[7]);
done:
	dma_free_coherent(&pdev->dev, 4096, buf, dma);
err_unmap:
	pci_iounmap(pdev, bar);
err_dis:
	/* leave device enabled but bound; cleanup on remove */
	return rc ? rc : 0;
}

static void remove(struct pci_dev *pdev) { pci_disable_device(pdev); }

static struct pci_driver drv = {
	.name = "dac960probe", .id_table = ids, .probe = probe, .remove = remove,
};
module_pci_driver(drv);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Read-only Enquiry probe for DAC960/i960 via PG mailbox");

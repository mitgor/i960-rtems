// SPDX-License-Identifier: GPL-2.0
/* HISTORICAL PROBE: do not use for further hardware experiments.
 * Completion/DMA/opcode handling is unsafe; see ../../docs/firmware/DUMP-ATTEMPT.md and
 * ../dump/README.md. The claimed StoreImage direction below is unverified.
 *
 * dac960probe - bind the (myrb-blacklisted) Mylex DAC960 and issue ONE V1 command
 * through the PG hardware mailbox via the kernel DMA API. Bounded polling (cannot wedge).
 *
 *   insmod dac960probe.ko op=0x1c                 # Enquiry2 (read-only, default)
 *   insmod dac960probe.ko op=0x21 dumpmax=512     # StoreImage: dump firmware -> /tmp/fwdump.bin
 *
 * SAFETY: op=0x22 (ProgramImage) is interlocked. StoreImage(0x21) is a card->host READ
 * (the vendor flasher's own backup path); it does not write the card.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/vmalloc.h>
#include <linux/fs.h>

#define PG_IDB 0x0020
#define PG_ODB 0x002C
#define PG_IRQM 0x0034
#define PG_CMD 0x1000
#define PG_STS 0x101A
#define CHUNK  0xF000u          /* StoreImage max transfer per command */

static int op = 0x1c;
static int dumpmax = 512;       /* KB cap for the dump */
module_param(op, int, 0444);
module_param(dumpmax, int, 0444);

static const struct pci_device_id ids[] = { { PCI_DEVICE(0x1069, 0x0010) }, { 0 } };
MODULE_DEVICE_TABLE(pci, ids);

/* issue one Type3/Type3D mailbox command; returns status word, -1 on timeout */
static int issue(void __iomem *bar, u8 opcode, u16 len, u32 off, u32 busaddr)
{
	int i;
	u32 w0 = opcode | (0x01u << 8) | ((u32)len << 16);
	for (i = 0; i < 100000 && (ioread8(bar + PG_IDB) & 0x01); i++) udelay(10);
	iowrite32(w0, bar + PG_CMD + 0);
	iowrite32(off, bar + PG_CMD + 4);
	iowrite32(busaddr, bar + PG_CMD + 8);
	iowrite8(0, bar + PG_CMD + 12);
	wmb();
	iowrite8(0x01, bar + PG_IDB);
	for (i = 0; i < 500000; i++) { if (ioread8(bar + PG_ODB) & 0x01) break; udelay(10); }
	if (!(ioread8(bar + PG_ODB) & 0x01)) return -1;
	{ u16 s = ioread16(bar + PG_STS); iowrite8(0x01, bar + PG_ODB); iowrite8(0x02, bar + PG_IDB); return s; }
}

static int probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
	void __iomem *bar; void *buf; dma_addr_t dma; int rc, st; u8 *b;

	if (op == 0x22) { dev_err(&pdev->dev, "REFUSED: op 0x22 (flash burn) interlocked\n"); return -EPERM; }
	rc = pci_enable_device(pdev); if (rc) return rc;
	pci_set_master(pdev);
	rc = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32)); if (rc) goto err_dis;
	bar = pci_iomap(pdev, 0, 0x2000); if (!bar) { rc = -ENOMEM; goto err_dis; }
	buf = dma_alloc_coherent(&pdev->dev, CHUNK, &dma, GFP_KERNEL);
	if (!buf) { rc = -ENOMEM; goto err_unmap; }
	iowrite8(0xff, bar + PG_IRQM);
	b = buf;

	if (op == 0x21) {                         /* StoreImage dump */
		u8 *acc; u32 off = 0, cap = (u32)dumpmax * 1024, total = 0;
		struct file *f; loff_t pos = 0; int chunks = 0;
		acc = vmalloc(cap); if (!acc) { rc = -ENOMEM; goto done; }
		while (off < cap) {
			u16 len = (cap - off) < CHUNK ? (cap - off) : CHUNK;
			memset(buf, 0xA5, len);
			st = issue(bar, 0x21, len, off, (u32)dma);
			if (chunks < 3)
				dev_info(&pdev->dev, "StoreImage off=0x%x len=0x%x -> status=0x%x head=%02x%02x%02x%02x\n",
					 off, len, st, b[0], b[1], b[2], b[3]);
			if (st != 0) { dev_info(&pdev->dev, "stop: status=0x%x at off=0x%x\n", st, off); break; }
			memcpy(acc + off, buf, len);
			off += len; total = off; chunks++;
		}
		if (total) {
			f = filp_open("/tmp/fwdump.bin", O_WRONLY | O_CREAT | O_TRUNC, 0644);
			if (!IS_ERR(f)) { kernel_write(f, acc, total, &pos); filp_close(f, NULL);
				dev_info(&pdev->dev, "WROTE /tmp/fwdump.bin %u bytes (%d chunks); head=%02x%02x%02x%02x%02x%02x%02x%02x\n",
					 total, chunks, acc[0],acc[1],acc[2],acc[3],acc[4],acc[5],acc[6],acc[7]); }
			else dev_err(&pdev->dev, "filp_open failed %ld\n", PTR_ERR(f));
		}
		vfree(acc);
	} else {                                   /* single command, hexdump result */
		u16 f23 = (op == 0x2b) ? 0x0002 : 0; /* 0x2B: byte2=subcmd 0x02 (Read Flash Desc Table) */
		int i;
		memset(buf, 0xA5, 512);
		st = issue(bar, op, f23, 0, (u32)dma);
		dev_info(&pdev->dev, "op=0x%02x f23=0x%x status=0x%x\n", op, f23, st);
		for (i = 0; i < 256; i += 16)
			dev_info(&pdev->dev, "  +%03x: %02x%02x%02x%02x %02x%02x%02x%02x %02x%02x%02x%02x %02x%02x%02x%02x\n", i,
				b[i],b[i+1],b[i+2],b[i+3],b[i+4],b[i+5],b[i+6],b[i+7],
				b[i+8],b[i+9],b[i+10],b[i+11],b[i+12],b[i+13],b[i+14],b[i+15]);
	}
done:
	dma_free_coherent(&pdev->dev, CHUNK, buf, dma);
err_unmap:
	pci_iounmap(pdev, bar);
err_dis:
	return rc ? rc : 0;
}
static void remove(struct pci_dev *pdev) { pci_disable_device(pdev); }
static struct pci_driver drv = { .name="dac960probe", .id_table=ids, .probe=probe, .remove=remove };
module_pci_driver(drv);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("DAC960/i960 PG mailbox: Enquiry + StoreImage firmware dump");

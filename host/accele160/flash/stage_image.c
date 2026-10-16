// SPDX-License-Identifier: GPL-2.0
/* Stock 6.00-05 STOREIMAGE staging only. No flash command in this module.
 * Requires exact 1069:0050/0054 BDF bound to the reviewed myrsread driver.
 * A pending command pins this module and its coherent DMA allocation.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/debugfs.h>
#include <linux/completion.h>
#include <linux/workqueue.h>
#include <linux/uaccess.h>
#include <scsi/scsi_host.h>
#include "myrs.h"

#define IMAGE_SIZE 1048576u
#define GUARD 65536u
#define TAIL_GUARD 1048576u
static char *bdf = "";
module_param(bdf, charp, 0444);
static struct pci_dev *pdev;
static struct myrs_hba *cs;
static struct module *parent;
static struct dentry *dir;
static void *allocation, *data;
static dma_addr_t allocation_dma, dma;
static struct work_struct work;
static DEFINE_MUTEX(lock);
static size_t written;
static bool started, done, released;
static int status = -1, residual = -1;
static unsigned int guard_changes;

static void worker(struct work_struct *unused)
{
 struct myrs_cmdblk *cmd = &cs->dcmd_blk;
 union myrs_cmd_mbox *next;
 DECLARE_COMPLETION_ONSTACK(completed);
 unsigned long flags;
 unsigned int i;
 mutex_lock(&cs->dcmd_mutex);
 memset(&cmd->mbox, 0, sizeof(cmd->mbox));
 cmd->status = 0; cmd->residual = 0; cmd->sense_len = 0;
 cmd->mbox.common.id = MYRS_DCMD_TAG;
 cmd->mbox.common.opcode = MYRS_CMD_OP_IOCTL;
 cmd->mbox.common.control.no_autosense = true;
 cmd->mbox.common.dma_size = IMAGE_SIZE;
 cmd->mbox.common.ioctl_opcode = 0x2c;
 cmd->mbox.common.rsvd2[0] = 9; /* full flash image selector */
 /* Word at mailbox byte 16 is zero: offset zero in 1024-byte units. */
 cmd->mbox.common.dma_addr.sge[0].sge_addr = dma;
 cmd->mbox.common.dma_addr.sge[0].sge_count = IMAGE_SIZE;
 cmd->complete = &completed;
 spin_lock_irqsave(&cs->queue_lock, flags);
 next = cs->next_cmd_mbox;
 cs->write_cmd_mbox(next, &cmd->mbox);
 if (cs->prev_cmd_mbox1->words[0] == 0 || cs->prev_cmd_mbox2->words[0] == 0)
  cs->get_cmd_mbox(cs->io_base);
 cs->prev_cmd_mbox2 = cs->prev_cmd_mbox1; cs->prev_cmd_mbox1 = next;
 if (++next > cs->last_cmd_mbox) next = cs->first_cmd_mbox;
 cs->next_cmd_mbox = next;
 spin_unlock_irqrestore(&cs->queue_lock, flags);
 wait_for_completion(&completed);
 spin_lock_irqsave(&cs->queue_lock, flags);
 status = cmd->status; residual = cmd->residual;
 spin_unlock_irqrestore(&cs->queue_lock, flags);
 mutex_unlock(&cs->dcmd_mutex);
 for (i = 0; i < GUARD; ++i)
  guard_changes += ((u8 *)allocation)[i] != 0xa5;
 for (i = GUARD + IMAGE_SIZE; i < GUARD + IMAGE_SIZE + TAIL_GUARD; ++i)
  guard_changes += ((u8 *)allocation)[i] != 0xa5;
 mutex_lock(&lock); done = true; mutex_unlock(&lock);
}

static ssize_t image_write(struct file *f, const char __user *in,
                           size_t n, loff_t *pos)
{
 ssize_t rc = n;
 mutex_lock(&lock);
 if (started || *pos != written || n > IMAGE_SIZE - written)
  rc = -EINVAL;
 else if (copy_from_user((u8 *)data + written, in, n))
  rc = -EFAULT;
 else {
  written += n;
  *pos += n;
 }
 mutex_unlock(&lock);
 return rc;
}
static ssize_t image_read(struct file *f, char __user *out,
                          size_t n, loff_t *pos)
{
 ssize_t rc;
 mutex_lock(&lock);
 rc = started ? -EBUSY : simple_read_from_buffer(out, n, pos, data, written);
 mutex_unlock(&lock);
 return rc;
}
static ssize_t status_read(struct file *f, char __user *out,
                           size_t n, loff_t *pos)
{
 char buf[180]; int len;
 mutex_lock(&lock);
 len = scnprintf(buf, sizeof(buf),
  "written=%zu started=%d done=%d status=%d residual=%d guard_changes=%u released=%d\n",
  written, started, done, status, residual, guard_changes, released);
 mutex_unlock(&lock);
 return simple_read_from_buffer(out, n, pos, buf, len);
}
static ssize_t start_write(struct file *f, const char __user *in,
                           size_t n, loff_t *pos)
{
 char buf[8];
 if (n != 6 || copy_from_user(buf, in, n) || memcmp(buf, "stage\n", 6))
  return -EINVAL;
 mutex_lock(&lock);
 if (started || written != IMAGE_SIZE) { mutex_unlock(&lock); return -EINVAL; }
 started = true;
 __module_get(THIS_MODULE);
 INIT_WORK(&work, worker);
 schedule_work(&work);
 mutex_unlock(&lock);
 return n;
}
static ssize_t release_write(struct file *f, const char __user *in,
                             size_t n, loff_t *pos)
{
 mutex_lock(&lock);
 if (!done || status || residual || guard_changes || released) {
  mutex_unlock(&lock); return -EBUSY;
 }
 /* done is set only after the worker's last access to DMA storage. */
 flush_work(&work);
 released = true;
 module_put(THIS_MODULE);
 mutex_unlock(&lock);
 return n;
}
static const struct file_operations image_ops = {
 .owner = THIS_MODULE, .read = image_read, .write = image_write,
 .llseek = default_llseek,
};
static const struct file_operations status_ops = {
 .owner = THIS_MODULE, .read = status_read, .llseek = default_llseek,
};
static const struct file_operations start_ops = {
 .owner = THIS_MODULE, .write = start_write,
};
static const struct file_operations release_ops = {
 .owner = THIS_MODULE, .write = release_write,
};
static int __init init_stage(void)
{
 unsigned int domain, bus, slot, fn; char tail;
 if (sscanf(bdf, "%x:%x:%x.%x%c", &domain, &bus, &slot, &fn, &tail) != 4 ||
     domain > 65535 || bus > 255 || slot > 31 || fn > 7) return -EINVAL;
 pdev = pci_get_domain_bus_and_slot(domain, bus, PCI_DEVFN(slot, fn));
 if (!pdev) return -ENODEV;
 if (pdev->vendor != 0x1069 || pdev->device != 0x0050 ||
     pdev->subsystem_vendor != 0x1069 || pdev->subsystem_device != 0x0054)
  goto wrong;
 device_lock(&pdev->dev);
 if (!pdev->dev.driver || strcmp(pdev->dev.driver->name, "myrsread")) {
  device_unlock(&pdev->dev); goto wrong;
 }
 parent = pdev->dev.driver->owner;
 if (!try_module_get(parent)) { device_unlock(&pdev->dev); goto wrong; }
 cs = pci_get_drvdata(pdev);
 device_unlock(&pdev->dev);
 if (!cs || cs->pdev != pdev || !cs->ctlr_info || !cs->next_cmd_mbox) {
  module_put(parent); goto wrong;
 }
 allocation = dma_alloc_coherent(&pdev->dev, IMAGE_SIZE + GUARD + TAIL_GUARD,
                                 &allocation_dma, GFP_KERNEL);
 if (!allocation) { module_put(parent); pci_dev_put(pdev); return -ENOMEM; }
 memset(allocation, 0xa5, IMAGE_SIZE + GUARD + TAIL_GUARD);
 data = (u8 *)allocation + GUARD; dma = allocation_dma + GUARD;
 dir = debugfs_create_dir("accele-stageimage", NULL);
 if (IS_ERR(dir)) {
  dma_free_coherent(&pdev->dev, IMAGE_SIZE + GUARD + TAIL_GUARD,
                    allocation, allocation_dma);
  module_put(parent); pci_dev_put(pdev); return PTR_ERR(dir);
 }
 debugfs_create_file("image.bin", 0600, dir, NULL, &image_ops);
 debugfs_create_file("status", 0400, dir, NULL, &status_ops);
 debugfs_create_file("start", 0200, dir, NULL, &start_ops);
 debugfs_create_file("release", 0200, dir, NULL, &release_ops);
 return 0;
wrong:
 pci_dev_put(pdev); return -ENODEV;
}
static void __exit stop_stage(void)
{
 if (started) flush_work(&work);
 debugfs_remove_recursive(dir);
 dma_free_coherent(&pdev->dev, IMAGE_SIZE + GUARD + TAIL_GUARD,
                   allocation, allocation_dma);
 module_put(parent); pci_dev_put(pdev);
}
module_init(init_stage); module_exit(stop_stage); MODULE_LICENSE("GPL");

// SPDX-License-Identifier: GPL-2.0
/* One-shot auto-sense probe using stock unsupported IOCTL 0x8f.
 * No command is submitted merely by loading this module. A pending command
 * pins the module and the reviewed myrsread parent; never force-unload it.
 *
 * Auto-sense is requested. Stock 6.00-05 completion (0xc004e940) turns every
 * non-zero internal status into host status 2; the internal code survives
 * only in sense bytes 12/13 (0x80|code>>8, code&0xff). The unsupported
 * handler should report internal 0x104 as 81/04, without flash writes.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/dma-mapping.h>
#include <linux/debugfs.h>
#include <linux/completion.h>
#include <linux/workqueue.h>
#include <linux/uaccess.h>
#include <linux/jiffies.h>
#include <scsi/scsi_host.h>
#include "myrs.h"

static char *bdf = "";
module_param(bdf, charp, 0444);
static struct pci_dev *pdev;
static struct myrs_hba *cs;
static struct module *parent;
static struct dentry *dir;
static struct work_struct work;
static DEFINE_MUTEX(lock);
static bool started, done, released;
static int status = -1, residual = -1;
static unsigned long start_jiffies, end_jiffies;
static u8 *sense;
static dma_addr_t sense_dma;
static u8 sense_copy[MYRS_SENSE_SIZE];
static int sense_len = -1;

static void worker(struct work_struct *unused)
{
 struct myrs_cmdblk *cmd = &cs->dcmd_blk;
 union myrs_cmd_mbox *next;
 DECLARE_COMPLETION_ONSTACK(completed);
 unsigned long flags;
 mutex_lock(&cs->dcmd_mutex);
 memset(&cmd->mbox, 0, sizeof(cmd->mbox));
 cmd->status = 0; cmd->residual = 0; cmd->sense_len = 0;
 cmd->mbox.common.id = MYRS_DCMD_TAG;
 cmd->mbox.common.opcode = MYRS_CMD_OP_IOCTL;
 memset(sense, 0, MYRS_SENSE_SIZE);
 cmd->mbox.common.sense_addr = sense_dma;
 cmd->mbox.common.sense_len = MYRS_SENSE_SIZE;
 cmd->mbox.common.dma_size = 0;
 cmd->mbox.common.ioctl_opcode = 0x8f;
 /* No selector or staged-image request. */
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
 sense_len = cmd->sense_len;
 spin_unlock_irqrestore(&cs->queue_lock, flags);
 mutex_unlock(&cs->dcmd_mutex);
 mutex_lock(&lock);
 memcpy(sense_copy, sense, sizeof(sense_copy));
 end_jiffies = jiffies;
 done = true;
 mutex_unlock(&lock);
}

static ssize_t status_read(struct file *f, char __user *out,
                           size_t n, loff_t *pos)
{
 char buf[224]; int len;
 mutex_lock(&lock);
 len = scnprintf(buf, sizeof(buf),
  "started=%d done=%d status=%d residual=%d elapsed_ms=%u released=%d sense_len=%d sense=%*phN\n",
  started, done, status, residual,
  started ? jiffies_to_msecs((done ? end_jiffies : jiffies) - start_jiffies) : 0,
  released, sense_len, (int)sizeof(sense_copy), sense_copy);
 mutex_unlock(&lock);
 return simple_read_from_buffer(out, n, pos, buf, len);
}
static ssize_t start_write(struct file *f, const char __user *in,
                           size_t n, loff_t *pos)
{
 static const char token[] = "SENSEPROBE unsupported\n";
 char buf[sizeof(token) - 1];
 if (n != sizeof(buf) || copy_from_user(buf, in, n) || memcmp(buf, token, n))
  return -EINVAL;
 mutex_lock(&lock);
 if (started) { mutex_unlock(&lock); return -EBUSY; }
 started = true;
 start_jiffies = jiffies;
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
 if (!done || released) {
  mutex_unlock(&lock); return -EBUSY;
 }
 flush_work(&work);
 released = true;
 module_put(THIS_MODULE);
 mutex_unlock(&lock);
 return n;
}
static const struct file_operations status_ops = {
 .owner = THIS_MODULE, .read = status_read, .llseek = default_llseek,
};
static const struct file_operations start_ops = {
 .owner = THIS_MODULE, .write = start_write,
};
static const struct file_operations release_ops = {
 .owner = THIS_MODULE, .write = release_write,
};
static int __init init_flash(void)
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
 sense = dma_alloc_coherent(&pdev->dev, MYRS_SENSE_SIZE, &sense_dma, GFP_KERNEL);
 if (!sense) { module_put(parent); pci_dev_put(pdev); return -ENOMEM; }
 dir = debugfs_create_dir("accele-senseprobe", NULL);
 if (IS_ERR(dir)) {
  dma_free_coherent(&pdev->dev, MYRS_SENSE_SIZE, sense, sense_dma);
  module_put(parent); pci_dev_put(pdev); return PTR_ERR(dir);
 }
 debugfs_create_file("status", 0400, dir, NULL, &status_ops);
 debugfs_create_file("start", 0200, dir, NULL, &start_ops);
 debugfs_create_file("release", 0200, dir, NULL, &release_ops);
 return 0;
wrong:
 pci_dev_put(pdev); return -ENODEV;
}
static void __exit stop_flash(void)
{
 if (started) flush_work(&work);
 debugfs_remove_recursive(dir);
 dma_free_coherent(&pdev->dev, MYRS_SENSE_SIZE, sense, sense_dma);
 module_put(parent); pci_dev_put(pdev);
}
module_init(init_flash); module_exit(stop_flash); MODULE_LICENSE("GPL");

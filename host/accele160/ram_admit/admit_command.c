// SPDX-License-Identifier: GPL-2.0
/* Exact zero-DMA operation-13 command for manifest-checked returning RAM image.
 * A pending command pins this companion and the myrsread parent driver.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/debugfs.h>
#include <linux/completion.h>
#include <linux/workqueue.h>
#include <linux/uaccess.h>
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
static u8 request[64];

static void worker(struct work_struct *unused)
{
 struct myrs_cmdblk *cmd = &cs->dcmd_blk;
 union myrs_cmd_mbox *next;
 DECLARE_COMPLETION_ONSTACK(completed);
 unsigned long flags;
 u8 *raw;
 mutex_lock(&cs->dcmd_mutex);
 memset(&cmd->mbox, 0, sizeof(cmd->mbox));
 cmd->status = 0; cmd->residual = 0; cmd->sense_len = 0;
 cmd->mbox.common.id = MYRS_DCMD_TAG;
 cmd->mbox.common.opcode = MYRS_CMD_OP_IOCTL;
 cmd->mbox.common.control.no_autosense = true;
 raw = (u8 *)&cmd->mbox;
 raw[21] = 0x8f;
 raw[22] = 1; raw[23] = 13;
 memcpy(raw + 24, "I960", 4);
 raw[28] = 0xd1; raw[29] = 0x10; raw[30] = 0x16; raw[31] = 0x16;
 memcpy(request, raw, sizeof(request));
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
 mutex_lock(&lock); done = true; mutex_unlock(&lock);
}

static ssize_t status_read(struct file *f, char __user *out,
                           size_t n, loff_t *pos)
{
 char buf[280]; int len, i;
 mutex_lock(&lock);
 len = scnprintf(buf, sizeof(buf),
  "started=%d done=%d status=%d residual=%d released=%d\n",
  started, done, status, residual, released);
 if (done) {
  len += scnprintf(buf + len, sizeof(buf) - len, "mailbox=");
  for (i = 0; i < sizeof(request); ++i)
   len += scnprintf(buf + len, sizeof(buf) - len, "%02x", request[i]);
  len += scnprintf(buf + len, sizeof(buf) - len, "\n");
 }
 mutex_unlock(&lock);
 return simple_read_from_buffer(out, n, pos, buf, len);
}
static ssize_t start_write(struct file *f, const char __user *in,
                           size_t n, loff_t *pos)
{
 char buf[6];
 if (n != 6 || copy_from_user(buf, in, n) || memcmp(buf, "probe\n", n))
  return -EINVAL;
 mutex_lock(&lock);
 if (started) { mutex_unlock(&lock); return -EBUSY; }
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
 if (!done || released) { mutex_unlock(&lock); return -EBUSY; }
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
static int __init init_ping(void)
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
 dir = debugfs_create_dir("accele-ram-admit", NULL);
 if (IS_ERR(dir)) { module_put(parent); pci_dev_put(pdev); return PTR_ERR(dir); }
 debugfs_create_file("status", 0400, dir, NULL, &status_ops);
 debugfs_create_file("start", 0200, dir, NULL, &start_ops);
 debugfs_create_file("release", 0200, dir, NULL, &release_ops);
 return 0;
wrong:
 pci_dev_put(pdev); return -ENODEV;
}
static void __exit stop_ping(void)
{
 if (started) flush_work(&work);
 debugfs_remove_recursive(dir);
 module_put(parent); pci_dev_put(pdev);
}
module_init(init_ping); module_exit(stop_ping); MODULE_LICENSE("GPL");

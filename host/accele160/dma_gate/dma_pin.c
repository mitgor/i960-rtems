// SPDX-License-Identifier: GPL-2.0
/* One exact AcceleRAID host DMA target. No firmware command or DMA is issued. */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/dma-mapping.h>
#include <linux/debugfs.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>

#define TARGET_BDF "0000:37:09.1"
#define PAGE_BYTES 4096u
#define TRANSFER_BYTES 256u
#define ALLOC_BYTES (3u * PAGE_BYTES)

static struct pci_dev *pdev;
static struct module *driver_owner;
static struct dentry *dir;
static void *area;
static dma_addr_t bus_base;
static bool armed, verified, released;
static DEFINE_MUTEX(gate_lock);

static unsigned int guard_changes(void)
{
 const u8 *b = area;
 unsigned int i, bad = 0;
 for (i = 0; i < PAGE_BYTES; i++) bad += b[i] != 0xa5;
 for (i = 2 * PAGE_BYTES; i < ALLOC_BYTES; i++) bad += b[i] != 0xa5;
 return bad;
}

static bool payload_matches(void)
{
 const u8 *b = (const u8 *)area + PAGE_BYTES;
 unsigned int i;
 for (i = 0; i < TRANSFER_BYTES; i++)
  if (b[i] != (u8)(i ^ 0xa6)) return false;
 for (; i < PAGE_BYTES; i++)
  if (b[i] != 0x5a) return false;
 return true;
}

static ssize_t status_read(struct file *f, char __user *out, size_t n, loff_t *pos)
{
 char s[200]; int len;
 mutex_lock(&gate_lock);
 len = scnprintf(s, sizeof(s),
  "bdf=%s bus_addr=0x%08llx length=%u armed=%u verified=%u released=%u guard_changes=%u payload_match=%u\n",
  TARGET_BDF, (unsigned long long)(bus_base + PAGE_BYTES), TRANSFER_BYTES,
  armed, verified, released, guard_changes(), payload_matches());
 mutex_unlock(&gate_lock);
 return simple_read_from_buffer(out, n, pos, s, len);
}

static ssize_t data_read(struct file *f, char __user *out, size_t n, loff_t *pos)
{
 return simple_read_from_buffer(out, n, pos,
                                (const u8 *)area + PAGE_BYTES, PAGE_BYTES);
}

static ssize_t arm_write(struct file *f, const char __user *in, size_t n, loff_t *pos)
{
 char s[8];
 if (n != 4 || copy_from_user(s, in, n) || memcmp(s, "arm\n", 4)) return -EINVAL;
 mutex_lock(&gate_lock);
 if (armed || verified || released || guard_changes() || payload_matches()) {
  mutex_unlock(&gate_lock); return -EBUSY;
 }
 armed = true;
 mutex_unlock(&gate_lock);
 return n;
}

static ssize_t verify_write(struct file *f, const char __user *in, size_t n, loff_t *pos)
{
 char s[8];
 if (n != 7 || copy_from_user(s, in, n) || memcmp(s, "verify\n", 7)) return -EINVAL;
 mutex_lock(&gate_lock);
 if (!armed || released || guard_changes() || !payload_matches()) {
  mutex_unlock(&gate_lock); return -EBUSY;
 }
 verified = true;
 mutex_unlock(&gate_lock);
 return n;
}

static ssize_t release_write(struct file *f, const char __user *in, size_t n, loff_t *pos)
{
 char s[8];
 if (n != 8 || copy_from_user(s, in, n) || memcmp(s, "release\n", 8)) return -EINVAL;
 mutex_lock(&gate_lock);
 if (released || guard_changes() || (armed && !verified)) {
  mutex_unlock(&gate_lock); return -EBUSY;
 }
 released = true;
 module_put(THIS_MODULE);
 mutex_unlock(&gate_lock);
 return n;
}

static const struct file_operations status_ops = {
 .owner = THIS_MODULE, .read = status_read, .llseek = default_llseek,
};
static const struct file_operations data_ops = {
 .owner = THIS_MODULE, .read = data_read, .llseek = default_llseek,
};
static const struct file_operations arm_ops = {.owner = THIS_MODULE, .write = arm_write};
static const struct file_operations verify_ops = {.owner = THIS_MODULE, .write = verify_write};
static const struct file_operations release_ops = {.owner = THIS_MODULE, .write = release_write};

static int __init dma_pin_init(void)
{
 int ret = -ENODEV;
 pdev = pci_get_domain_bus_and_slot(0, 0x37, PCI_DEVFN(0x09, 1));
 if (!pdev) return ret;
 if (strcmp(pci_name(pdev), TARGET_BDF) || pdev->vendor != 0x1069 ||
     pdev->device != 0x0050 || pdev->subsystem_vendor != 0x1069 ||
     pdev->subsystem_device != 0x0054) goto fail_dev;
 device_lock(&pdev->dev);
 if (!pdev->dev.driver || strcmp(pdev->dev.driver->name, "myrsread")) {
  device_unlock(&pdev->dev); goto fail_dev;
 }
 driver_owner = pdev->dev.driver->owner;
 if (!try_module_get(driver_owner)) {
  device_unlock(&pdev->dev); goto fail_dev;
 }
 device_unlock(&pdev->dev);
 area = dma_alloc_coherent(&pdev->dev, ALLOC_BYTES, &bus_base, GFP_KERNEL);
 if (!area) { ret = -ENOMEM; goto fail_driver; }
 if (upper_32_bits(bus_base + 2 * PAGE_BYTES - 1)) {
  ret = -ERANGE; goto fail_dma;
 }
 memset(area, 0xa5, ALLOC_BYTES);
 memset((u8 *)area + PAGE_BYTES, 0x5a, PAGE_BYTES);
 dir = debugfs_create_dir("accele-dma-pin", NULL);
 if (IS_ERR_OR_NULL(dir)) {
  ret = dir ? PTR_ERR(dir) : -ENODEV; goto fail_dma;
 }
 debugfs_create_file("status", 0400, dir, NULL, &status_ops);
 debugfs_create_file("data.bin", 0400, dir, NULL, &data_ops);
 debugfs_create_file("arm", 0200, dir, NULL, &arm_ops);
 debugfs_create_file("verify", 0200, dir, NULL, &verify_ops);
 debugfs_create_file("release", 0200, dir, NULL, &release_ops);
 __module_get(THIS_MODULE); /* Retain allocation until explicit release. */
 return 0;
fail_dma:
 dma_free_coherent(&pdev->dev, ALLOC_BYTES, area, bus_base);
fail_driver:
 module_put(driver_owner);
fail_dev:
 pci_dev_put(pdev);
 return ret;
}

static void __exit dma_pin_exit(void)
{
 debugfs_remove_recursive(dir);
 dma_free_coherent(&pdev->dev, ALLOC_BYTES, area, bus_base);
 module_put(driver_owner);
 pci_dev_put(pdev);
}
module_init(dma_pin_init);
module_exit(dma_pin_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Pinned guarded AcceleRAID 160 DMA target, exact BDF");

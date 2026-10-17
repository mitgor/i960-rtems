// SPDX-License-Identifier: GPL-2.0
/* Reboot-only coherent frame targets. This module never starts card DMA. */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/dma-mapping.h>
#include <linux/debugfs.h>
#include <linux/uaccess.h>
#define TARGET_BDF "0000:37:09.1"
#define GUARD 4096u
#define PAYLOAD 65536u
#define MARKER 32u
#define TOTAL (19u*GUARD)
struct frame_slot { void *area; dma_addr_t bus; };
static struct frame_slot slots[2];
static struct pci_dev *pdev;
static struct module *driver_owner;
static struct dentry *dir;
static unsigned guard_changes(void) {
 unsigned s,i,bad=0;
 for(s=0;s<2;s++) {
  const u8 *p=slots[s].area;
  for(i=0;i<GUARD;i++)bad+=p[i]!=0xa5;
  for(i=GUARD+PAYLOAD+MARKER;i<TOTAL;i++)bad+=p[i]!=0xa5;
 }
 return bad;
}
static ssize_t status_read(struct file*f,char __user*out,size_t n,loff_t*pos) {
 char s[256];int len;
 dma_rmb();
 len=scnprintf(s,sizeof(s),"bdf=%s bytes=%u total=%u bus0=0x%08llx bus1=0x%08llx guard_changes=%u retained=1\n",
 TARGET_BDF,PAYLOAD,TOTAL,(unsigned long long)(slots[0].bus+GUARD),
 (unsigned long long)(slots[1].bus+GUARD),guard_changes());
 return simple_read_from_buffer(out,n,pos,s,len);
}
static ssize_t data_read(struct file*f,char __user*out,size_t n,loff_t*pos) {
 struct frame_slot *s=f->private_data;
 dma_rmb();return simple_read_from_buffer(out,n,pos,s->area,TOTAL);
}
static ssize_t marker_read(struct file*f,char __user*out,size_t n,loff_t*pos) {
 struct frame_slot *s=f->private_data;
 dma_rmb();return simple_read_from_buffer(out,n,pos,(u8*)s->area+GUARD+PAYLOAD,MARKER);
}
static const struct file_operations status_ops={.owner=THIS_MODULE,.read=status_read,.llseek=default_llseek};
static const struct file_operations data_ops={.owner=THIS_MODULE,.open=simple_open,.read=data_read,.llseek=default_llseek};
static const struct file_operations marker_ops={.owner=THIS_MODULE,.open=simple_open,.read=marker_read,.llseek=default_llseek};
static int __init frames_init(void) {
 int ret=-ENODEV;unsigned i;u16 command;
 pdev=pci_get_domain_bus_and_slot(0,0x37,PCI_DEVFN(9,1));if(!pdev)return ret;
 if(strcmp(pci_name(pdev),TARGET_BDF)||pdev->vendor!=0x1069||pdev->device!=0x0050||pdev->subsystem_vendor!=0x1069||pdev->subsystem_device!=0x0054)goto fail_dev;
 device_lock(&pdev->dev);
 if(!pdev->dev.driver||strcmp(pdev->dev.driver->name,"myrsread")){device_unlock(&pdev->dev);goto fail_dev;}
 driver_owner=pdev->dev.driver->owner;
 if(!try_module_get(driver_owner)){device_unlock(&pdev->dev);goto fail_dev;}
 device_unlock(&pdev->dev);
 pci_read_config_word(pdev,PCI_COMMAND,&command);if(!(command&PCI_COMMAND_MASTER))goto fail_driver;
 for(i=0;i<2;i++) {
  slots[i].area=dma_alloc_coherent(&pdev->dev,TOTAL,&slots[i].bus,GFP_KERNEL);
  if(!slots[i].area){ret=-ENOMEM;goto fail_dma;}
  if(upper_32_bits(slots[i].bus+TOTAL-1)){ret=-ERANGE;goto fail_dma;}
  memset(slots[i].area,0xa5,TOTAL);
  memset((u8*)slots[i].area+GUARD,0x5a,PAYLOAD);
  memset((u8*)slots[i].area+GUARD+PAYLOAD,0,MARKER);
 }
 dir=debugfs_create_dir("accele-frame-dma",NULL);
 if(IS_ERR_OR_NULL(dir)){ret=dir?PTR_ERR(dir):-ENODEV;goto fail_dma;}
 debugfs_create_file("status",0400,dir,NULL,&status_ops);
 debugfs_create_file("frame0.bin",0400,dir,&slots[0],&data_ops);
 debugfs_create_file("frame1.bin",0400,dir,&slots[1],&data_ops);
 debugfs_create_file("marker0.bin",0400,dir,&slots[0],&marker_ops);
 debugfs_create_file("marker1.bin",0400,dir,&slots[1],&marker_ops);
 __module_get(THIS_MODULE); /* Never unpin on process death, STOP or uncertainty. */
 return 0;
fail_dma:
 for(i=0;i<2;i++)if(slots[i].area)dma_free_coherent(&pdev->dev,TOTAL,slots[i].area,slots[i].bus);
fail_driver:module_put(driver_owner);
fail_dev:pci_dev_put(pdev);return ret;
}
static void __exit frames_exit(void) {
 unsigned i;debugfs_remove_recursive(dir);
 for(i=0;i<2;i++)dma_free_coherent(&pdev->dev,TOTAL,slots[i].area,slots[i].bus);
 module_put(driver_owner);pci_dev_put(pdev);
}
module_init(frames_init);module_exit(frames_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Exact AcceleRAID guarded double frame target; reboot-only pin lifetime");

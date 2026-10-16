// SPDX-License-Identifier: GPL-2.0
/* Exact myrs v6.8 private ABI companion. Requires the reviewed myrsread driver.
 * READIMAGE only; no bind/unbind/reset/programming. Never unload pending DMA.
 */
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/debugfs.h>
#include <linux/completion.h>
#include <linux/workqueue.h>
#include <scsi/scsi_host.h>
#include "myrs.h"
#ifndef CAPTURE_DIR
#define CAPTURE_DIR "accele-readimage"
#endif
static char *bdf="";
static unsigned int selector=0, length=0;
module_param(bdf,charp,0444);
module_param(selector,uint,0444);
module_param(length,uint,0444);
static struct pci_dev *pdev;
static struct myrs_hba *cs;
static struct module *parent;
static struct dentry *dir;
/* Extra mapped guard space is diagnostic, not an IOMMU isolation guarantee. */
#define GUARD 65536u
#define TAIL_GUARD 1048576u
static void *allocation,*data;
static dma_addr_t allocation_dma;
static unsigned int guard_changes;
static dma_addr_t dma;
static struct work_struct work;
static DEFINE_MUTEX(lock);
static bool done,released;
static int status=-1,residual=-1;
static void worker(struct work_struct *w)
{
 struct myrs_cmdblk *cmd=&cs->dcmd_blk;
 union myrs_cmd_mbox *next;
 DECLARE_COMPLETION_ONSTACK(completed);
 unsigned long flags;
 mutex_lock(&cs->dcmd_mutex);
 memset(&cmd->mbox,0,sizeof(cmd->mbox));
 cmd->status=0;cmd->residual=0;cmd->sense_len=0;
 cmd->mbox.common.id=MYRS_DCMD_TAG;
 cmd->mbox.common.opcode=MYRS_CMD_OP_IOCTL;
 cmd->mbox.common.control.dma_ctrl_to_host=true;
 cmd->mbox.common.control.no_autosense=true;
 cmd->mbox.common.dma_size=length;
 cmd->mbox.common.ioctl_opcode=0x2d;
 cmd->mbox.common.rsvd2[0]=selector;
 cmd->mbox.common.dma_addr.sge[0].sge_addr=dma;
 cmd->mbox.common.dma_addr.sge[0].sge_count=length;
 cmd->complete=&completed;
 /* Same queue publication as Linux v6.8 myrs_qcmd, under its queue lock. */
 spin_lock_irqsave(&cs->queue_lock,flags);
 next=cs->next_cmd_mbox;
 cs->write_cmd_mbox(next,&cmd->mbox);
 if(cs->prev_cmd_mbox1->words[0]==0 || cs->prev_cmd_mbox2->words[0]==0)
  cs->get_cmd_mbox(cs->io_base);
 cs->prev_cmd_mbox2=cs->prev_cmd_mbox1;cs->prev_cmd_mbox1=next;
 if(++next>cs->last_cmd_mbox) next=cs->first_cmd_mbox;
 cs->next_cmd_mbox=next;
 spin_unlock_irqrestore(&cs->queue_lock,flags);
 wait_for_completion(&completed);
 /* Synchronize with ISR's final cmd->complete=NULL store. */
 spin_lock_irqsave(&cs->queue_lock,flags);
 status=cmd->status;residual=cmd->residual;
 spin_unlock_irqrestore(&cs->queue_lock,flags);
 mutex_unlock(&cs->dcmd_mutex);
 {
  unsigned int i;
  for(i=0;i<GUARD;i++)
   guard_changes+=((u8 *)allocation)[i]!=0xa5;
  for(i=GUARD+length;i<length+GUARD+TAIL_GUARD;i++)
   guard_changes+=((u8 *)allocation)[i]!=0xa5;
 }
 mutex_lock(&lock);done=true;mutex_unlock(&lock);
}
static ssize_t read_status(struct file *f,char __user *out,size_t n,loff_t *pos)
{
 char buf[160];int len;
 mutex_lock(&lock);
 len=scnprintf(buf,sizeof(buf),"done=%d status=%d residual=%d selector=%u length=%u released=%d guard_changes=%u\n",done,status,residual,selector,length,released,guard_changes);
 mutex_unlock(&lock);return simple_read_from_buffer(out,n,pos,buf,len);
}
static ssize_t read_data(struct file *f,char __user *out,size_t n,loff_t *pos)
{
 ssize_t rc;
 mutex_lock(&lock);
 rc=done?simple_read_from_buffer(out,n,pos,data,length):-EAGAIN;
 mutex_unlock(&lock);return rc;
}
static ssize_t release_job(struct file *f,const char __user *in,size_t n,loff_t *pos)
{
 mutex_lock(&lock);
 if(!done || status || residual || guard_changes){mutex_unlock(&lock);return -EBUSY;}
 flush_work(&work);
 if(!released){released=true;module_put(THIS_MODULE);}
 mutex_unlock(&lock);return n;
}
static const struct file_operations status_ops={.owner=THIS_MODULE,.read=read_status,.llseek=default_llseek};
static const struct file_operations data_ops={.owner=THIS_MODULE,.read=read_data,.llseek=default_llseek};
static const struct file_operations release_ops={.owner=THIS_MODULE,.write=release_job};
static int __init start(void)
{
 unsigned int domain,bus,slot,fn;char tail;
 if(sscanf(bdf,"%x:%x:%x.%x%c",&domain,&bus,&slot,&fn,&tail)!=4 || domain>65535 || bus>255 || slot>31 || fn>7) return -EINVAL;
 if(!length || (length & 3) || length>1048576 || !((selector>=1 && selector<=3)||selector==5||selector==9||selector==14)) return -EINVAL;
 pdev=pci_get_domain_bus_and_slot(domain,bus,PCI_DEVFN(slot,fn));
 if(!pdev)return -ENODEV;
 if(pdev->vendor!=0x1069 || pdev->device!=0x0050 || pdev->subsystem_vendor!=0x1069 || pdev->subsystem_device!=0x0054)goto wrong;
 device_lock(&pdev->dev);
 if(!pdev->dev.driver || strcmp(pdev->dev.driver->name,"myrsread")){device_unlock(&pdev->dev);goto wrong;}
 parent=pdev->dev.driver->owner;
 if(!try_module_get(parent)){device_unlock(&pdev->dev);goto wrong;}
 cs=pci_get_drvdata(pdev);
 device_unlock(&pdev->dev);
 if(!cs || cs->pdev!=pdev || !cs->ctlr_info || !cs->next_cmd_mbox){module_put(parent);goto wrong;}
 allocation=dma_alloc_coherent(&pdev->dev,length+GUARD+TAIL_GUARD,&allocation_dma,GFP_KERNEL);
 if(!allocation){module_put(parent);pci_dev_put(pdev);return -ENOMEM;}
 memset(allocation,0xa5,length+GUARD+TAIL_GUARD);
 data=(u8 *)allocation+GUARD;dma=allocation_dma+GUARD;
 dir=debugfs_create_dir(CAPTURE_DIR,NULL);
 if(IS_ERR(dir)){dma_free_coherent(&pdev->dev,length+GUARD+TAIL_GUARD,allocation,allocation_dma);module_put(parent);pci_dev_put(pdev);return PTR_ERR(dir);}
 debugfs_create_file("status",0400,dir,NULL,&status_ops);
 debugfs_create_file("data.bin",0400,dir,NULL,&data_ops);
 debugfs_create_file("release",0200,dir,NULL,&release_ops);
 __module_get(THIS_MODULE);
 INIT_WORK(&work,worker);schedule_work(&work);return 0;
 wrong:pci_dev_put(pdev);return -ENODEV;
}
static void __exit stop(void)
{
 flush_work(&work);debugfs_remove_recursive(dir);
 dma_free_coherent(&pdev->dev,length+GUARD+TAIL_GUARD,allocation,allocation_dma);
 module_put(parent);pci_dev_put(pdev);
}
module_init(start);module_exit(stop);MODULE_LICENSE("GPL");

/* Only included in a module pinned to a --fault-test 3 image. One doorbell NMI.
 * No arbitrary MMIO or trigger before resident takeover / target arming. */
static long nmi_test_ioctl(struct file*file,unsigned int cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned int w[8];int rc=0;
 if(cmd!=0xc0204d06u)return resident_ioctl(file,cmd,arg);
 if(copy_from_user(w,(void __user*)arg,sizeof(w)))return -EFAULT;
 if(w[0]!=1||!w[1]||w[1]>65535||w[2]||w[3]||w[4]||w[5]||w[6]||w[7])return -EINVAL;
 mutex_lock(&d->session_lock);
 if(w[1]!=d->monitor_epoch){rc=-ESTALE;goto out;}
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||d->mu_failed||d->mu_halted||d->mu_nmi_injected||d->steps!=1||d->sequence!=1||!d->irq_may_run||d->response_ready){rc=-EBUSY;goto out;}
 if(readl(d->bar+0x28)!=0x1f3||readl(d->bar+0x34)!=0xff||readl(d->bar+0x20)||(readl(d->bar+ODB)&1)){rc=-EPROTO;goto out;}
 d->mu_nmi_injected=true;
 record(d,"NMI TEST one-shot doorbell bit31 epoch=%u; target mask=1f3\n",w[1]);
 writel(0x80000000u,d->bar+0x20);readl(d->bar+0x20);
 w[3]=1;session_log_end(d);if(copy_to_user((void __user*)arg,w,sizeof(w)))rc=-EFAULT;
 out:mutex_unlock(&d->session_lock);return rc;
}

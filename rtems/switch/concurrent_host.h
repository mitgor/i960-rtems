/* Lock order: session_lock -> control_lock. ioctl takes only control_lock.
 * Window is published after submission and closed/joined before any completion
 * logging, cleanup, release or remove. File references protect d/module. */
static int control_wait(struct experiment*d,u32 expected){unsigned int i;
 for(i=0;i<800;i++){
  if(readl(d->bar+ODB)&1)return -EPROTO;
  if(readl(d->bar+0x28)!=0x1fb||readl(d->bar+0x34)!=0xff)return -EIO;
  if(readl(d->bar+0x1c)==expected)return 0;
  usleep_range(1000,1500);
 }
 return -ETIMEDOUT;
}
static long concurrent_ioctl(struct file*file,unsigned int cmd,unsigned long arg){
 struct experiment*d=file->private_data;u32 w[8];int rc=0;
 if(cmd!=0xc0204d03u)return -ENOTTY;
 if(copy_from_user(w,(void __user*)arg,sizeof(w)))return -EFAULT;
 if(w[0]>1||w[2]||w[3]||w[4]||w[5]||w[6]||w[7])return -EINVAL;
 mutex_lock(&d->control_lock);
 if(!d->control_window){rc=-EAGAIN;goto out;}
 if(w[1]!=d->control_epoch){rc=-ESTALE;goto out;}
 if(d->control_taken){rc=-EALREADY;goto out;}
 w[2]=d->control_sequence;w[3]=readl(d->bar+ODB);w[4]=readl(d->bar+0x1c);
 if(!w[0])goto copy;
 d->control_taken=true;
 rc=control_wait(d,0x71000000u|d->control_epoch);if(rc)goto failed;
 msleep(d->stop_delay_ms);
 if(readl(d->bar+ODB)&1){rc=-EPROTO;goto failed;}
 record(d,"CONCURRENT STOP ioctl sequence=%u; hardware completion absent\n",d->control_sequence);
 writel(0x72000000u|d->control_epoch,d->bar+0x14);readl(d->bar+0x14);
 rc=control_wait(d,0x73000000u|d->control_epoch);if(rc)goto failed;
 w[5]=readl(d->bar+ODB);w[6]=readl(d->bar+0x1c);
 if(w[5]&1){rc=-EPROTO;goto failed;}
 record(d,"CONCURRENT DRAINED ioctl sequence=%u; hardware completion absent; RELEASE\n",d->control_sequence);
 writel(0x74000000u|d->control_epoch,d->bar+0x14);readl(d->bar+0x14);
 d->control_done=true;w[7]=1;goto copy;
failed:
 d->control_error=rc;
 record(d,"CONCURRENT control error=%d; retain pending resources\n",rc);
copy:
 /* An EFAULT after RELEASE does not undo completed hardware work. No replay. */
 if(!rc&&copy_to_user((void __user*)arg,w,sizeof(w)))rc=-EFAULT;
out:
 mutex_unlock(&d->control_lock);return rc;
}

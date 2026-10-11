/* session_lock owns the parked callback. control_lock serializes only sideband
 * ioctls. No firmware transaction is submitted while the lease window is open. */
static int lease_wait(struct experiment*d,u32 expected){unsigned int i;
 for(i=0;i<800;i++){
  if(readl(d->bar+ODB)&1)return -EPROTO;
  if(readl(d->bar+0x28)!=0x1fb||readl(d->bar+0x34)!=0xff)return -EIO;
  if(readl(d->bar+0x1c)==expected)return 0;
  usleep_range(1000,1500);
 }return -ETIMEDOUT;
}
static long concurrent_ioctl(struct file*file,unsigned int cmd,unsigned long arg){
 struct experiment*d=file->private_data;u32 w[8],token;int rc=0;
 if(cmd!=0xc0204d03u)return -ENOTTY;
 if(copy_from_user(w,(void __user*)arg,sizeof(w)))return -EFAULT;
 if(w[0]>3||w[2]||w[3]||w[4]||w[5]||w[6]||w[7])return -EINVAL;
 mutex_lock(&d->control_lock);
 if(!d->control_window){rc=-EAGAIN;goto out;}
 if(w[1]!=d->control_epoch){rc=-ESTALE;goto out;}
 if(d->control_taken){rc=-EALREADY;goto out;}
 w[2]=d->control_sequence;w[3]=readl(d->bar+ODB);w[4]=readl(d->bar+0x1c);
 if(w[3]&1){rc=-EPROTO;goto failed;}
 if(!w[0])goto copy;
 if(w[0]==2){
  if(d->lease_granted){rc=-EALREADY;goto out;}
  rc=lease_wait(d,0x71000000u|d->control_epoch);if(rc)goto failed;
  writel(0x61000000u|d->control_epoch,d->bar+0x14);readl(d->bar+0x14);
  rc=lease_wait(d,0x62000000u|d->control_epoch);if(rc)goto failed;
  d->lease_granted=true;
  record(d,"LEASE GRANTED sequence=%u; firmware callback pending; no stock commands until RELEASE\n",d->control_sequence);
 }else if(w[0]==3){
  if(!d->lease_granted){rc=-EPERM;goto out;}
  if(d->lease_seq>=65535){rc=-EOVERFLOW;goto out;}
  token=++d->lease_seq;
  writel(0x63000000u|token,d->bar+0x14);readl(d->bar+0x14);
  rc=lease_wait(d,0x64000000u|token);if(rc)goto failed;
 }else{
  token=readl(d->bar+0x1c);
  if(token!=(0x75000000u|d->control_epoch)){
   if(!d->lease_granted){rc=-EPERM;goto out;}
   writel(0x72000000u|d->control_epoch,d->bar+0x14);readl(d->bar+0x14);
   rc=lease_wait(d,0x75000000u|d->control_epoch);if(rc)goto failed;
  }
  d->control_taken=true;w[5]=readl(d->bar+ODB);w[6]=readl(d->bar+0x1c);
  if(w[5]&1){rc=-EPROTO;goto failed;}
  record(d,"LEASE QUIESCED sequence=%u renewals=%u; completion absent; RELEASE\n",d->control_sequence,d->lease_seq);
  writel(0x74000000u|d->control_epoch,d->bar+0x14);readl(d->bar+0x14);d->control_done=true;
 }
 if(w[0]!=1){w[5]=readl(d->bar+ODB);w[6]=readl(d->bar+0x1c);}w[7]=w[0]==1?1:d->lease_seq;goto copy;
failed:d->control_error=rc;record(d,"LEASE control error=%d; retain pending resources\n",rc);
copy:if(!rc&&copy_to_user((void __user*)arg,w,sizeof(w)))rc=-EFAULT;
out:mutex_unlock(&d->control_lock);return rc;
}

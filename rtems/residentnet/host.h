/* Packet ABI: eight u32 header words + 1536 bytes. Only the session owner can
 * use this; timeout poisons the entire session, and never resumes firmware. */
static int packet_exchange(struct experiment*d,unsigned int token,unsigned int data,unsigned int*value,unsigned long deadline){unsigned int i,seen;
 if(time_after_eq(jiffies,deadline))return -ETIMEDOUT;
 writel(data,d->bar+0x10);readl(d->bar+0x10);writel(token,d->bar+0x14);readl(d->bar+0x14);
 for(i=0;i<20000;i++){
  if(time_after_eq(jiffies,deadline))return -ETIMEDOUT;
  if((readl(d->bar+ODB)&1)||readl(d->bar+0x28)!=0x1fb||readl(d->bar+0x34)!=0xff)return -EPROTO;
  seen=readl(d->bar+0x1c);
  if(seen==(token|0x08000000u)&&readl(d->bar+0x14)==0){*value=readl(d->bar+0x18);return 0;}
  usleep_range(50,100);
 }
 return -ETIMEDOUT;
}
static long resident_ioctl(struct file*file,unsigned int cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned int *w,i,n,v=0,epoch,op;int rc=0;unsigned long deadline;
 if(cmd!=0xc6204d05u)return monitor_ioctl(file,cmd,arg);
 w=memdup_user((void __user*)arg,1568);if(IS_ERR(w))return PTR_ERR(w);
 op=w[0];epoch=w[1];n=w[2];
 if((op!=1&&op!=2)||!epoch||epoch>65535||w[3]||w[4]||w[5]||w[6]||w[7]||(op==1&&(n<20||n>1500))||(op==2&&n)){rc=-EINVAL;goto free;}
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto unlock;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto unlock;}
 deadline=jiffies+msecs_to_jiffies(5000);
 if(op==1){
  rc=packet_exchange(d,0xa0000000u|epoch,n,&v,deadline);if(rc)goto uncertain;if(v){rc=-EAGAIN;goto unlock;}
  for(i=0;i<(n+3)/4;i++){rc=packet_exchange(d,0xb0000000u|(i<<16)|epoch,w[8+i],&v,deadline);if(rc)goto uncertain;if(v){rc=-EPROTO;goto uncertain;}}
  rc=packet_exchange(d,0xc0000000u|epoch,0,&v,deadline);if(rc)goto uncertain;if(v){rc=-ESHUTDOWN;goto unlock;}
 }else{
  rc=packet_exchange(d,0xd0000000u|epoch,0,&n,deadline);if(rc)goto uncertain;
  if(n==0xfffffffeu){rc=-ESHUTDOWN;goto unlock;}if(n>1536){rc=-EPROTO;goto uncertain;}
  memset(w+8,0,1536);
  for(i=0;i<(n+3)/4;i++){rc=packet_exchange(d,0xe0000000u|(i<<16)|epoch,0,&w[8+i],deadline);if(rc)goto uncertain;}
  if(n){rc=packet_exchange(d,0xf0000000u|epoch,0,&v,deadline);if(rc)goto uncertain;if(v!=n){rc=-EPROTO;goto uncertain;}}
 }
 w[2]=n;w[3]=d->sequence;w[4]=readl(d->bar+ODB);w[5]=d->pending;w[6]=d->runner_uncertain;
 if(w[4]&1||w[5]||w[6]){rc=-EPROTO;goto uncertain;}
 if(n)record(d,"RESIDENT PIO op=%u bytes=%u sequence=1 pending=0 uncertain=0\n",op,n);
 session_log_end(d);if(copy_to_user((void __user*)arg,w,1568))rc=-EFAULT;goto unlock;
uncertain:d->mu_failed=true;d->ready=false;record(d,"RESIDENT PIO uncertain rc=%d; retain until reboot\n",rc);session_log_end(d);
unlock:mutex_unlock(&d->session_lock);
free:kfree(w);return rc;
}

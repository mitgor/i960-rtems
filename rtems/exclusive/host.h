/* Serialized while no firmware command/callback is pending. The only device
 * writes here are the documented message-1 word. Never DMA/SCSI/config writes. */
static int monitor_wait(struct experiment*d,unsigned int expected,unsigned int alternative,unsigned int*seen){unsigned int i;
#ifdef I960_LARGE_CONTROL
 unsigned long deadline=jiffies+msecs_to_jiffies((expected&0xff000000u)==0x8b000000u?180000:20000);
 for(i=0;time_before(jiffies,deadline);i++){
#else
 for(i=0;i<15000;i++){
#endif
  if(readl(d->bar+ODB)&1)return -EPROTO;
  if(readl(d->bar+0x28)!=0x1fb||readl(d->bar+0x34)!=0xff)return -EIO;
  *seen=readl(d->bar+0x1c);if((*seen==expected||*seen==alternative)&&(!d->mu_resident||readl(d->bar+0x14)==0))return 0;
#ifdef I960_LARGE_CONTROL
  if((expected&0xff000000u)>=0x92000000u)usleep_range(50,100);else usleep_range(1000,1500);
#else
  usleep_range(1000,1500);
#endif
 }return -ETIMEDOUT;
}
static long monitor_ioctl(struct file*file,unsigned int cmd,unsigned long arg){struct experiment*d=file->private_data;unsigned int w[8],epoch,seen=0;int rc=0;
 if(cmd!=0xc0204d04u)return -ENOTTY;
 if(copy_from_user(w,(void __user*)arg,sizeof(w)))return -EFAULT;
 if(w[0]>7||!w[1]||w[1]>65535||w[2]>(w[0]==5?63:20)||w[3]||w[4]||w[5]||w[6]||w[7])return -EINVAL;
 epoch=w[1];mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||(!d->ready&&!d->mu_resident)||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->steps!=1||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto out;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto out;}
 if((d->mu_resident&&w[0]<5)||(!d->mu_resident&&w[0]>=5)){rc=-EBUSY;goto out;}
 d->mu_used=true;w[3]=d->sequence;w[4]=readl(d->bar+ODB);w[6]=d->pending;w[7]=d->runner_uncertain;
 if(w[4]&1){rc=-EPROTO;goto failed;}
 record(d,"MONITOR enter action=%u sequence=%u pending=%u uncertain=%u completion=%u\n",w[0],w[3],w[6],w[7],w[4]&1);
 if(w[0]>=4){
  unsigned int token,reply;
  if(w[0]==4){d->mu_resident=true;d->ready=false;token=0x8a000000u;reply=0x8b000000u;}
  else if(w[0]==5){token=0x91000000u|(w[2]<<16);reply=0x92000000u|(w[2]<<16);}
  else if(w[0]==6){token=0x93000000u;reply=0x94000000u;}
  else{token=0x90000000u;reply=0x95000000u;}
  writel(token|epoch,d->bar+0x14);readl(d->bar+0x14);
  rc=monitor_wait(d,reply|epoch,reply|epoch,&seen);w[5]=seen;if(rc)goto failed;
  if(w[0]==5)w[2]=readl(d->bar+0x18);
  record(d,"EXCLUSIVE resident action=%u sequence=%u pending=0 uncertain=0 token=%08x value=%08x\n",w[0],d->sequence,seen,w[2]);goto copy;
 }
 writel((w[0]==1?0x84000000u:w[0]==3?0x88000000u:0x81000000u)|epoch,d->bar+0x14);readl(d->bar+0x14);
 if(w[0]==1)rc=monitor_wait(d,0x85000000u|epoch,0x85000000u|epoch,&seen);
 else if(w[0]==3){rc=monitor_wait(d,0x89000000u|epoch,0x89000000u|epoch,&seen);if(!rc)d->mu_halted=true;}
 else{
  rc=monitor_wait(d,0x82000000u|epoch,0x82000000u|epoch,&seen);if(rc)goto failed;
  record(d,"MONITOR parked original IRQ frame; no firmware callback pending\n");
  if(!w[0]){msleep(w[2]);writel(0x83000000u|epoch,d->bar+0x14);readl(d->bar+0x14);}
  rc=monitor_wait(d,(w[0]==2?0x86000000u:0x87000000u)|epoch,0x86000000u|epoch,&seen);
 }
 w[5]=seen;if(rc)goto failed;
 if(d->sequence!=w[3]||d->pending||d->runner_uncertain||(readl(d->bar+ODB)&1)){rc=-EPROTO;goto failed;}
 record(d,"MONITOR returned token=%08x sequence=%u pending=0 uncertain=0\n",seen,d->sequence);goto copy;
failed:d->mu_failed=true;d->ready=false;record(d,"MONITOR uncertainty rc=%d; retain resources\n",rc);
copy:session_log_end(d);if(copy_to_user((void __user*)arg,w,sizeof(w)))rc=-EFAULT;
out:mutex_unlock(&d->session_lock);return rc;
}

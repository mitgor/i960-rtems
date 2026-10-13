/* UPL1 PIO mailbox: fixed 32-byte ioctl header + 1024 bytes. Session mutex and
 * epoch checks are shared with networking/control. No firmware doorbell/DMA. */
static long upload_ioctl(struct file*file,unsigned int cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned int *w,i,n,v,epoch,op;int rc=0;unsigned long deadline;
 if(cmd!=0xc4204d06u)return resident_ioctl(file,cmd,arg);
 w=memdup_user((void __user*)arg,1056);if(IS_ERR(w))return PTR_ERR(w);
 op=w[0];epoch=w[1];n=w[2];
 if((op!=1&&op!=2
#ifdef I960_DOOM_ENGINE
 &&op!=9&&op!=10
#endif
#ifdef I960_DOOM_RUNTIME
 &&op!=3&&op!=4
#ifdef I960_DOOM_OWNED
 &&op!=5&&op!=6
#ifdef I960_DOOM_CHECKPOINTS
 &&op!=7
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
 &&op!=8
#endif
#endif
#endif
#endif
 )||!epoch||epoch>65535||w[3]||w[4]||w[5]||w[6]||w[7]||(op==1&&(n<32||n>1024||(n&3)))||((op==2||op==3||op==5)&&n)||(op==4&&(n<32||n>544||(n&3)))||(op==6&&n!=32)||(op==7&&n!=4)||(op==8&&n!=8)||((op==9||op==10)&&n!=8)){rc=-EINVAL;goto free;}
#ifdef I960_DOOM_OWNED
 if(op==6){if(w[8]!=0x3252444fu||!w[9]){rc=-EINVAL;goto free;}for(i=10;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}}
#endif
#ifdef I960_DOOM_CHECKPOINTS
 if(op==7){if(!w[8]||w[8]>512){rc=-EINVAL;goto free;}for(i=9;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}}
#endif
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
 if(op==8){if(!w[8]||w[8]>512||!w[9]){rc=-EINVAL;goto free;}for(i=10;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}}
#endif
#ifdef I960_DOOM_ENGINE
 if(op==10){if(w[8]>2||(w[8]==0&&w[9])||(w[8]==2&&w[9]>511)){rc=-EINVAL;goto free;}for(i=10;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}}
 if(op==9){if(!w[8]||(w[9]&1023)||w[9]>131072-1024){rc=-EINVAL;goto free;}for(i=10;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}}
#endif
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto unlock;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto unlock;}
 deadline=jiffies+msecs_to_jiffies(10000);
#ifdef I960_DOOM_ENGINE
 if(op==10){
  rc=packet_exchange(d,0x6b000000u|(w[8]<<16)|epoch,w[9],&v,deadline);if(rc)goto uncertain;
  memset(w+8,0,1024);n=4;w[8]=v;
 }
 else
 if(op==9){
  rc=packet_exchange(d,0x6c000000u|epoch,w[8],&v,deadline);if(rc)goto uncertain;if(v){rc=-ESTALE;goto unlock;}
  rc=packet_exchange(d,0x6d000000u|epoch,w[9],&v,deadline);if(rc)goto uncertain;if(v){rc=-ESTALE;goto unlock;}
  memset(w+8,0,1024);n=1024;
  for(i=0;i<256;i++){rc=packet_exchange(d,0x6e000000u|(i<<16)|epoch,0,&w[8+i],deadline);if(rc)goto uncertain;}
 }
 else
#endif
#ifdef I960_DOOM_CHECKPOINT_BARRIERS
 if(op==8){
  rc=packet_exchange(d,0x7f000000u|epoch,w[8],&v,deadline);if(rc)goto uncertain;if(v){rc=-ESTALE;goto unlock;}
  rc=packet_exchange(d,0x7f010000u|epoch,w[9],&v,deadline);if(rc)goto uncertain;if(v){rc=-ESTALE;goto unlock;}
 }
 else
#endif
#ifdef I960_DOOM_OWNED
 if(op==6){rc=packet_exchange(d,0x7a000000u|epoch,w[9],&v,deadline);if(rc)goto uncertain;if(v){rc=-ESTALE;goto unlock;}}
 else
#endif
 if(op==1||op==4){
  rc=packet_exchange(d,(op==1?0x70000000u:0x77000000u)|epoch,n,&v,deadline);if(rc)goto uncertain;if(v){rc=-EAGAIN;goto unlock;}
  for(i=0;i<n/4;i++){rc=packet_exchange(d,(op==1?0x71000000u:0x78000000u)|(i<<16)|epoch,w[8+i],&v,deadline);if(rc)goto uncertain;if(v){rc=-EPROTO;goto uncertain;}}
  rc=packet_exchange(d,(op==1?0x72000000u:0x79000000u)|epoch,0,&v,deadline);if(rc)goto uncertain;if(v){rc=-ESHUTDOWN;goto unlock;}
 }else{
  rc=packet_exchange(d,(op==2?0x74000000u:op==5?0x7b000000u:op==7?0x7d000000u:0x75000000u)|epoch,op==7?w[8]:0,&v,deadline);if(rc)goto uncertain;if(v){rc=-EPROTO;goto uncertain;}
  memset(w+8,0,1024);n=op==2?64:32;
  for(i=0;i<n/4;i++){rc=packet_exchange(d,(op==2?0x73000000u:op==5?0x7c000000u:op==7?0x7e000000u:0x76000000u)|(i<<16)|epoch,0,&w[8+i],deadline);if(rc)goto uncertain;}
 }
 w[2]=n;w[3]=d->sequence;w[4]=readl(d->bar+ODB);w[5]=d->pending;w[6]=d->runner_uncertain;
 if(w[4]&1||w[5]||w[6]){rc=-EPROTO;goto uncertain;}
 session_log_end(d);if(copy_to_user((void __user*)arg,w,1056))rc=-EFAULT;goto unlock;
uncertain:d->mu_failed=true;d->ready=false;record(d,"RESIDENT UPLOAD uncertain rc=%d; retain until reboot\n",rc);session_log_end(d);
unlock:mutex_unlock(&d->session_lock);
free:kfree(w);return rc;
}

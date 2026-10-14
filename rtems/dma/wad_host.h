/* Fixed 4 KiB host-to-card block. No user-provided bus/card address. */
static long wad_dma_ioctl(struct file*file,unsigned cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned *w,op,epoch,g,i,v=0,q[8];int rc=0;unsigned long deadline;
 if(cmd!=0xd0204d09u)return frame_dma_ioctl(file,cmd,arg);
 w=memdup_user((void __user*)arg,4128);if(IS_ERR(w))return PTR_ERR(w);
 op=w[0];epoch=w[1];g=w[2];
 if((op!=1&&op!=2)||!epoch||epoch>65535||!g||w[6]||w[7]||!w[4]||w[4]>4096||w[3]>=w[5]){rc=-EINVAL;goto free;}
 if(op==2){for(i=8;i<1032;i++)if(w[i]){rc=-EINVAL;goto free;}}
 else {unsigned n=min(w[4],w[5]-w[3]);for(i=n;i<4096;i++)if(((u8*)(w+8))[i]){rc=-EINVAL;goto free;}}
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto unlock;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto unlock;}
 deadline=jiffies+msecs_to_jiffies(10000);
 if(op==1){
  if(d->wad_dma_pending){rc=-EBUSY;goto unlock;}
  if(g<=d->wad_dma_gen){rc=-ESTALE;goto unlock;}
  rc=packet_exchange(d,0x75000000u|epoch,0,&v,deadline);if(rc||v)goto uncertain;
  for(i=0;i<8;i++){rc=packet_exchange(d,0x76000000u|(i<<16)|epoch,0,q+i,deadline);if(rc)goto uncertain;}
  if(q[0]!=0x31424157||q[1]!=g||q[2]!=1||q[3]!=1||q[4]!=w[3]||q[5]!=w[4]||q[6]!=w[5]){rc=-ESTALE;goto unlock;}
  if(!d->wad_dma_buf){
   d->wad_dma_buf=dma_alloc_coherent(&d->pdev->dev,12288,&d->wad_dma_bus,GFP_KERNEL);if(!d->wad_dma_buf){rc=-ENOMEM;goto unlock;}
   if(d->wad_dma_bus>0xffffffffULL-12288||(d->wad_dma_bus&3)){dma_free_coherent(&d->pdev->dev,12288,d->wad_dma_buf,d->wad_dma_bus);d->wad_dma_buf=NULL;rc=-ERANGE;goto unlock;}
  }
  memset(d->wad_dma_buf,0xa5,12288);memcpy((u8*)d->wad_dma_buf+4096,w+8,4096);dma_wmb();
  for(i=0;i<3;i++)d->wad_dma_geometry[i]=w[3+i];
  rc=packet_exchange(d,0x77010000u|epoch,(unsigned)d->wad_dma_bus+4096,&v,deadline);if(rc||v)goto uncertain;
  d->wad_dma_gen=g;d->wad_dma_pending=true;
  rc=packet_exchange(d,0x77020000u|epoch,g,&v,deadline);if(rc||v)goto uncertain;
  memset(w+8,0,4096);goto copy;
 }
 if(!d->wad_dma_pending||g!=d->wad_dma_gen){rc=-ESTALE;goto unlock;}
 for(i=0;i<3;i++)if(w[3+i]!=d->wad_dma_geometry[i]){rc=-ESTALE;goto unlock;}
 rc=packet_exchange(d,0x77030000u|epoch,0,&v,deadline);if(rc)goto uncertain;
 if(v==1){rc=-EAGAIN;goto unlock;}if(v!=2){rc=-EPROTO;goto uncertain;}
 for(i=0;i<12;i++){rc=packet_exchange(d,0x77040000u|epoch,i,w+8+i,deadline);if(rc)goto uncertain;}
 if(w[8]!=g||w[9]!=(unsigned)d->wad_dma_bus+4096||w[10]<0xc0241000||w[10]>0xc0e2e000||(w[10]&3)||w[11]!=4096||w[12]||w[13]!=w[18]||w[14]||w[15]||w[16]!=6||w[17]>=200000||w[18]<0xc0f4c010||w[18]>0xc0f8bfe0||(w[18]&31)||w[19]){rc=-EPROTO;goto uncertain;}
 dma_rmb();for(i=0;i<4096;i++)if(((u8*)d->wad_dma_buf)[i]!=0xa5||((u8*)d->wad_dma_buf)[8192+i]!=0xa5){rc=-EILSEQ;goto uncertain;}
 rc=packet_exchange(d,0x77050000u|epoch,g,&v,deadline);if(rc||v)goto uncertain;
 d->wad_dma_pending=false;
copy:session_log_end(d);if(copy_to_user((void __user*)arg,w,4128))rc=-EFAULT;goto unlock;
uncertain:if(!rc)rc=-EIO;d->mu_failed=true;d->ready=false;record(d,"WAD DMA uncertain rc=%d; retain mappings until reboot\n",rc);session_log_end(d);
unlock:mutex_unlock(&d->session_lock);
free:kfree(w);return rc;
}

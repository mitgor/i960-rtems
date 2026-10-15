/* Two persistent coherent destinations. No userspace DMA address is accepted.
 * Completion/read are host-RAM-only. RELEASE is one bounded control write.
 * Mapping lifetime is the retained resident session, including all failures. */
#define PP_BYTES 73728u
#define PP_MARK 73696u
static long pingpong_ioctl(struct file*file,unsigned cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned*w,op,epoch,g,off,i,slot,v=0,*m;int rc=0;unsigned long deadline;
 if(cmd!=0xc4204d0au)return wad_dma_ioctl(file,cmd,arg);
 w=memdup_user((void __user*)arg,1056);if(IS_ERR(w))return PTR_ERR(w);
 op=w[0];epoch=w[1];g=w[2];off=w[3];slot=(g-1)&1;
 if(op<1||op>8||!epoch||epoch>65535||w[4]||w[5]||w[6]||w[7]||(op==1&&(g||off))||((op>=2&&op<=4||op==8)&&!g)||(op!=3&&op!=8&&off)||(op==8&&off!=PP_BYTES)||(op==3&&((off&1023)||off>72704))){rc=-EINVAL;goto free;}
 for(i=8;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto unlock;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto unlock;}
 deadline=jiffies+msecs_to_jiffies(10000);
 if(op==1){
  if(d->pp_enabled||d->pp_buf[0]||d->pp_buf[1]){rc=-EBUSY;goto unlock;}
  for(i=0;i<2;i++){
   d->pp_buf[i]=dma_alloc_coherent(&d->pdev->dev,PP_BYTES,&d->pp_bus[i],GFP_KERNEL);
   if(!d->pp_buf[i]){rc=-ENOMEM;goto uncertain;}
   if(d->pp_bus[i]>0xffffffffULL-PP_BYTES){rc=-ERANGE;goto uncertain;}
   memset(d->pp_buf[i],0xa5,PP_BYTES);d->pp_next[i]=i+1;
  }
  dma_wmb();
  for(i=0;i<2;i++){rc=packet_exchange(d,0x6b000000u|((8+i)<<16)|epoch,(unsigned)d->pp_bus[i]+4096,&v,deadline);if(rc||v)goto uncertain;w[8+i]=(unsigned)d->pp_bus[i];}
  d->pp_enabled=true;goto copy;
 }
 if(!d->pp_enabled){rc=-EINVAL;goto unlock;}
 if(op==6){
  if(d->pp_running||!g||(g&1)!=1){rc=-EINVAL;goto unlock;}
  d->pp_next[0]=g;d->pp_next[1]=g+1;
  rc=packet_exchange(d,0x6b0a0000u|epoch,1,&v,deadline);if(rc||v)goto uncertain;d->pp_running=true;goto copy;
 }
 if(op==7){rc=packet_exchange(d,0x6b0c0000u|epoch,5,w+8,deadline);if(rc)goto uncertain;goto copy;}
 if(op==5){for(i=0;i<6;i++){rc=packet_exchange(d,0x6b0c0000u|epoch,i==5?6:i,w+8+i,deadline);if(rc)goto uncertain;}goto copy;}
 if(!d->pp_running){rc=-EINVAL;goto unlock;}
 if(g!=d->pp_next[slot]){rc=-ESTALE;goto unlock;}
 m=(unsigned*)((u8*)d->pp_buf[slot]+PP_MARK);
 if(READ_ONCE(m[7])!=g){rc=-EAGAIN;goto unlock;}
 dma_rmb();
 if(m[0]!=0x31505044u||m[1]!=g||m[2]!=slot||m[3]!=65536||(m[4]&3)||m[4]<0xc0240000u||m[4]>0xc0e30000u||m[6]!=~g||READ_ONCE(m[7])!=g){rc=-EPROTO;goto uncertain;}
 if(op==2||op==8){
  for(i=0;i<4096;i++)if(((u8*)d->pp_buf[slot])[i]!=0xa5){rc=-EILSEQ;goto uncertain;}
  for(i=69632;i<PP_MARK;i++)if(((u8*)d->pp_buf[slot])[i]!=0xa5){rc=-EILSEQ;goto uncertain;}
  if(op==8){
   /* The slot stays owned under session_lock throughout the full copy.
    * No release credit on a short/faulting userspace copy. */
   if(copy_to_user((u8 __user*)arg+32,d->pp_buf[slot],PP_BYTES)){rc=-EFAULT;goto unlock;}
   d->pp_reads[slot][0]=~0u;d->pp_reads[slot][1]=~0u;d->pp_reads[slot][2]=255;
   goto unlock;
  }
  memcpy(w+8,m,32);goto copy;
 }
 if(op==3){memcpy(w+8,(u8*)d->pp_buf[slot]+off,1024);goto copy;}
 if(d->pp_reads[slot][0]!=~0u||d->pp_reads[slot][1]!=~0u||d->pp_reads[slot][2]!=255){rc=-EBUSY;goto unlock;}
 rc=packet_exchange(d,0x6b0b0000u|epoch,g,&v,deadline);if(rc||v)goto uncertain;
 memset(d->pp_reads[slot],0,sizeof(d->pp_reads[slot]));d->pp_next[slot]+=2;
copy:session_log_end(d);if(copy_to_user((void __user*)arg,w,1056))rc=-EFAULT;else if(op==3){i=off/1024;d->pp_reads[slot][i/32]|=1u<<(i%32);}goto unlock;
uncertain:if(!rc)rc=-EIO;d->mu_failed=true;d->ready=false;record(d,"PINGPONG uncertain rc=%d; retain both mappings\n",rc);FRAME_DMA_DIAG(d,epoch);session_log_end(d);
unlock:mutex_unlock(&d->session_lock);
free:kfree(w);return rc;
}

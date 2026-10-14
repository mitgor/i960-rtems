/* Kernel owns a dedicated coherent mapping for the actual Mylex PCI device.
 * The resident session already pins its module/device on final close. This
 * mapping is retained until reboot, including on copyout failure or timeout. */
#define DMA_PROOF_BYTES 73728u
static long dma_proof_ioctl(struct file*file,unsigned int cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned*w,op,epoch,n,offset,seq,seed,i,v=0;int rc=0;unsigned long deadline;
 if(cmd!=0xc4204d07u)return resident_ioctl(file,cmd,arg);
 w=memdup_user((void __user*)arg,1056);if(IS_ERR(w))return PTR_ERR(w);
 op=w[0];epoch=w[1];n=w[2];offset=w[3];seq=w[4];seed=w[5];
 if(!epoch||epoch>65535||!seq||w[6]||w[7]||(op!=1&&op!=2)||(op==1&&(!n||n>65536||offset>4095))||(op==2&&(n!=1024||offset>DMA_PROOF_BYTES-1024||(offset&1023)||seed))){rc=-EINVAL;goto free;}
 for(i=8;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto unlock;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto unlock;}
 if(op==2){
  if(!d->proof_valid||seq!=d->proof_seq){rc=-ESTALE;goto unlock;}
  dma_rmb();memcpy(w+8,(u8*)d->proof_buf+offset,1024);goto copy;
 }
 if(seq!=d->proof_seq+1){rc=-ESTALE;goto unlock;}
 if(!d->proof_buf){
  d->proof_buf=dma_alloc_coherent(&d->pdev->dev,DMA_PROOF_BYTES,&d->proof_dma,GFP_KERNEL);
  if(!d->proof_buf){rc=-ENOMEM;goto unlock;}
  if(d->proof_dma>0xffffffffULL-DMA_PROOF_BYTES){dma_free_coherent(&d->pdev->dev,DMA_PROOF_BYTES,d->proof_buf,d->proof_dma);d->proof_buf=NULL;rc=-ERANGE;goto unlock;}
  d->proof_blob.data=d->proof_buf;d->proof_blob.size=DMA_PROOF_BYTES;
  debugfs_create_blob("dma-proof-buffer.bin",0400,d->directory,&d->proof_blob);
 }
 d->proof_valid=false;memset(d->proof_buf,0xa5,DMA_PROOF_BYTES);dma_wmb();
 deadline=jiffies+msecs_to_jiffies(10000);
 {unsigned args[4]={(unsigned)d->proof_dma+4096+offset,n,seed,seq};
 for(i=0;i<4;i++){rc=packet_exchange(d,0x50000000u|(i<<16)|epoch,args[i],&v,deadline);if(rc||v)goto uncertain;}}
 d->proof_seq=seq;
 rc=packet_exchange(d,0x51000000u|epoch,0,&v,deadline);if(rc)goto uncertain;
 if(v){unsigned target_error=v,diagnostic;
  /* A replied target error permits read-only frozen diagnostics, never retry. */
  for(i=0;i<32;i++){
   rc=packet_exchange(d,0x52000000u|(i<<16)|epoch,0,&diagnostic,deadline);
   if(rc)break;
   record(d,"DMA FAILURE report[%u]=%08x\n",i,diagnostic);
  }
  v=target_error;rc=-EIO;goto uncertain;
 }
 for(i=0;i<32;i++){rc=packet_exchange(d,0x52000000u|(i<<16)|epoch,0,&w[8+i],deadline);if(rc)goto uncertain;}
 if(w[8]!=0x31414d44||w[9]!=seq||w[10]!=(unsigned)d->proof_dma+4096+offset||w[11]!=n||w[12]!=seed||w[13]||w[16]||w[17]||w[18]!=7||w[19]!=2||w[20]||w[21]||w[22]!=1||w[23]){rc=-EPROTO;goto uncertain;}
 dma_rmb();
 for(i=0;i<DMA_PROOF_BYTES;i++){
  unsigned j=i-(4096+offset);u8 expected=j<n?(u8)(j*13u^seed^(j>>8)):0xa5;
  if(((u8*)d->proof_buf)[i]!=expected){rc=-EILSEQ;goto uncertain;}
 }
 d->proof_valid=true;
 record(d,"DMA PROOF seq=%u length=%u offset=%u complete; all %u bytes and guards checked\n",seq,n,offset,DMA_PROOF_BYTES);
copy:
 session_log_end(d);if(copy_to_user((void __user*)arg,w,1056))rc=-EFAULT;goto unlock;
uncertain:
 if(!rc)rc=-EIO;d->proof_valid=false;d->mu_failed=true;d->ready=false;
 record(d,"DMA PROOF uncertain rc=%d target=%u; coherent mapping retained until reboot\n",rc,v);session_log_end(d);
unlock:mutex_unlock(&d->session_lock);
free:kfree(w);return rc;
}

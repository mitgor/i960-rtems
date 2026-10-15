/* Retained coherent slots; userspace supplies bytes, never DMA addresses. */
static long wad_ring_ioctl(struct file*file,unsigned cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned*w,op,epoch,slot,i,g,v=0;int rc=0;
 unsigned char*b;struct wr_record *request,*response,*complete;unsigned long deadline;
 if(cmd!=0xc0204d0bu)return pingpong_ioctl(file,cmd,arg);
 w=memdup_user((void __user*)arg,32+WR_BLOCK);if(IS_ERR(w))return PTR_ERR(w);
 op=w[0];epoch=w[1];slot=w[2];g=w[3];
 if(op<1||op>4||!epoch||epoch>65535||slot>=2||w[7]||((op==2||op==4)&&(w[4]||w[5]))||(op==1&&(slot||g||w[4]||w[5]||!w[6]||w[6]>268435456u))){rc=-EINVAL;goto free;}
 if(op!=3)for(i=8;i<8+WR_BLOCK/4;i++)if(w[i]){rc=-EINVAL;goto free;}
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto unlock;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto unlock;}
 deadline=jiffies+msecs_to_jiffies(10000);
 if(op==1){
  if(d->wr_buf[0]||d->wr_buf[1]){rc=-EBUSY;goto unlock;}
  for(i=0;i<2;i++){
   d->wr_buf[i]=dma_alloc_coherent(&d->pdev->dev,WR_BYTES,&d->wr_bus[i],GFP_KERNEL);
   if(!d->wr_buf[i]||d->wr_bus[i]>0xffffffffULL-WR_BYTES||(d->wr_bus[i]&63)){rc=-ENOMEM;goto uncertain;}
   memset(d->wr_buf[i],0xa5,WR_BYTES);memset((u8*)d->wr_buf[i]+WR_REQUEST,0,192);
   d->wr_next[i]=i+1;
  }
  d->wr_total=w[6];dma_wmb();
  for(i=0;i<2;i++){rc=packet_exchange(d,0x77000000u|((6+i)<<16)|epoch,(unsigned)d->wr_bus[i],&v,deadline);if(rc||v)goto uncertain;w[8+i]=(unsigned)d->wr_bus[i];}
  goto copy;
 }
 if(!d->wr_buf[slot]||w[6]!=d->wr_total||!g||((g-1)&1)!=slot||g+(op==4?2:0)!=d->wr_next[slot]){rc=-ESTALE;goto unlock;}
 b=d->wr_buf[slot];request=(void*)(b+WR_REQUEST);response=(void*)(b+WR_RESPONSE);complete=(void*)(b+WR_COMPLETE);
 if(READ_ONCE(request->w[7])!=g){rc=-EAGAIN;goto unlock;}dma_rmb();
 if(!wr_record_valid(request,WR_REQ_MAGIC,g,d->wr_total)||READ_ONCE(request->w[7])!=g){rc=-EPROTO;goto uncertain;}
 if(op!=4&&g>2&&(!wr_record_valid(complete,WR_END_MAGIC,g-2,d->wr_total)||!wr_record_matches(complete,response))){rc=-EPROTO;goto uncertain;}
 for(i=0;i<WR_REQUEST;i++)if(b[i]!=0xa5){rc=-EILSEQ;goto uncertain;}
 for(i=WR_DATA+WR_BLOCK;i<WR_BYTES;i++)if(b[i]!=0xa5){rc=-EILSEQ;goto uncertain;}
 if(op==4){
  if(!wr_record_valid(complete,WR_END_MAGIC,g,d->wr_total)||!wr_record_matches(complete,response)||!wr_record_matches(complete,request)){rc=-EPROTO;goto uncertain;}
  memcpy(w+8,request,64);memcpy(w+24,response,64);memcpy(w+40,complete,64);goto copy;
 }
 if(op==2){if(w[4]||w[5]){rc=-EINVAL;goto unlock;}memcpy(w+8,request,64);memcpy(w+24,complete,64);goto copy;}
 if(w[4]!=request->w[3]||w[5]!=request->w[4]){rc=-ESTALE;goto unlock;}
 for(i=w[5];i<WR_BLOCK;i++)if(((u8*)(w+8))[i]){rc=-EINVAL;goto unlock;}
 memcpy(b+WR_DATA,w+8,WR_BLOCK);
 /* Header plus payload become visible before the committed generation. */
 response->w[7]=0;for(i=0;i<16;i++)if(i!=7)response->w[i]=request->w[i];response->w[0]=WR_RSP_MAGIC;
 dma_wmb();WRITE_ONCE(response->w[7],g);d->wr_next[slot]+=2;
 memset(w+8,0,WR_BLOCK);memcpy(w+8,response,64);
copy:session_log_end(d);if(copy_to_user((void __user*)arg,w,32+WR_BLOCK))rc=-EFAULT;goto unlock;
uncertain:if(!rc)rc=-EIO;d->mu_failed=true;d->ready=false;record(d,"WAD ring uncertain rc=%d; retain mappings until reboot\n",rc);session_log_end(d);
unlock:mutex_unlock(&d->session_lock);
free:kfree(w);return rc;
}

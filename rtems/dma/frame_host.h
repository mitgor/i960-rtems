/* Dedicated coherent mapping, never freed after resident ownership. No user
 * DMA address is accepted. The renderer pin spans submit, validation and ACK. */
#include <linux/crc32.h>
#define FRAME_DMA_BYTES 73728u
#ifndef FRAME_DMA_DIAG
#define FRAME_DMA_DIAG(d,e) ((void)0)
#endif
static long frame_dma_ioctl(struct file*file,unsigned cmd,unsigned long arg){
 struct experiment*d=file->private_data;unsigned*w,op,epoch,g,off,i,v=0;int rc=0;unsigned long deadline;
 if(cmd!=0xc4204d08u)return upload_ioctl(file,cmd,arg);
 w=memdup_user((void __user*)arg,1056);if(IS_ERR(w))return PTR_ERR(w);
 op=w[0];epoch=w[1];g=w[2];off=w[3];
 if(op<1||op>3||!epoch||epoch>65535||!g||w[4]||w[5]||w[6]||w[7]||(op==2&&off)||(op==1&&off>1)||(op==3&&((off&1023)||off>72704))){rc=-EINVAL;goto free;}
 for(i=8;i<264;i++)if(w[i]){rc=-EINVAL;goto free;}
 mutex_lock(&d->session_lock);
 if(d->removed||d->pinned||!d->owned||!d->mu_resident||d->pending||d->runner_uncertain||!d->irq_may_run||d->response_ready||d->sequence!=1||d->mu_failed||d->mu_halted){rc=-EBUSY;goto unlock;}
 if(epoch!=d->monitor_epoch){rc=-ESTALE;goto unlock;}
 if(op==3){
  if(!d->frame_dma_valid||g!=d->frame_dma_gen){rc=-ESTALE;goto unlock;}
  dma_rmb();memcpy(w+8,(u8*)d->frame_dma_buf+off,1024);goto copy;
 }
 deadline=jiffies+msecs_to_jiffies(10000);
 if(op==1){
  if(d->frame_dma_pending){rc=-EBUSY;goto unlock;}
  if(g<=d->frame_dma_gen){rc=-ESTALE;goto unlock;}
  rc=packet_exchange(d,0x6b000000u|epoch,0,&v,deadline);if(rc)goto uncertain;if(v!=g){rc=-ESTALE;goto unlock;}
  if(!d->frame_dma_buf){
   d->frame_dma_buf=dma_alloc_coherent(&d->pdev->dev,FRAME_DMA_BYTES,&d->frame_dma_bus,GFP_KERNEL);if(!d->frame_dma_buf){rc=-ENOMEM;goto unlock;}
   if(d->frame_dma_bus>0xffffffffULL-FRAME_DMA_BYTES){dma_free_coherent(&d->pdev->dev,FRAME_DMA_BYTES,d->frame_dma_buf,d->frame_dma_bus);d->frame_dma_buf=NULL;rc=-ERANGE;goto unlock;}
   d->frame_dma_blob.data=d->frame_dma_buf;d->frame_dma_blob.size=FRAME_DMA_BYTES;debugfs_create_blob("frame-dma-buffer.bin",0400,d->directory,&d->frame_dma_blob);
  }
  d->frame_dma_no_crc=off;
  rc=packet_exchange(d,0x6b060000u|epoch,off,&v,deadline);if(rc||v)goto uncertain;
  d->frame_dma_valid=false;memset(d->frame_dma_buf,0xa5,FRAME_DMA_BYTES);dma_wmb();
  rc=packet_exchange(d,0x6b030000u|epoch,(unsigned)d->frame_dma_bus+4096,&v,deadline);if(rc||v)goto uncertain;
  d->frame_dma_gen=g;d->frame_dma_pending=true;
  rc=packet_exchange(d,0x6b040000u|epoch,g,&v,deadline);if(rc||v)goto uncertain;goto copy;
 }
 if(!d->frame_dma_pending||g!=d->frame_dma_gen){rc=-ESTALE;goto unlock;}
 rc=packet_exchange(d,0x6b050000u|epoch,1,&v,deadline);if(rc)goto uncertain;
 if(v==1){rc=-EAGAIN;goto unlock;}if(v!=2){rc=-EPROTO;goto uncertain;}
 for(i=0;i<16;i++){rc=packet_exchange(d,0x6b050000u|epoch,i,w+8+i,deadline);if(rc)goto uncertain;}
 if(w[8]!=0x314d4446||w[9]!=2||w[10]!=g||w[11]!=(unsigned)d->frame_dma_bus+4096||w[12]<0xc0240000||w[12]>0xc0e30000||w[13]!=w[14]||w[15]||w[16]!=w[23]||w[17]||w[18]||w[19]!=7||w[20]>=200000||w[21]||w[22]!=d->frame_dma_no_crc||(w[22]&&w[13])||w[23]<0xc0f4c010||w[23]>0xc0f8bfe0||(w[23]&31)){rc=-EPROTO;goto uncertain;}
 dma_rmb();
 for(i=0;i<4096;i++)if(((u8*)d->frame_dma_buf)[i]!=0xa5||((u8*)d->frame_dma_buf)[69632+i]!=0xa5){rc=-EILSEQ;goto uncertain;}
 if(!d->frame_dma_no_crc&&(crc32_le(~0u,(u8*)d->frame_dma_buf+4096,65536)^~0u)!=w[13]){rc=-EILSEQ;goto uncertain;}
 rc=packet_exchange(d,0x6b000000u|epoch,0,&v,deadline);if(rc)goto uncertain;if(v!=g){rc=-ESTALE;goto uncertain;}
 d->frame_dma_pending=false;d->frame_dma_valid=true;
 record(d,"FRAME DMA generation=%u checksum=%08x complete; ownership and guards validated\n",g,w[13]);
copy:session_log_end(d);if(copy_to_user((void __user*)arg,w,1056))rc=-EFAULT;goto unlock;
uncertain:if(!rc)rc=-EIO;d->frame_dma_valid=false;d->mu_failed=true;d->ready=false;record(d,"FRAME DMA uncertain rc=%d target=%u; retain mapping and image\n",rc,v);FRAME_DMA_DIAG(d,epoch);session_log_end(d);
unlock:mutex_unlock(&d->session_lock);
free:kfree(w);return rc;
}

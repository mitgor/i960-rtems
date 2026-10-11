/* Same session lock and pending-command retention as STOP1. Intentional
 * omission is selected before submission, never inferred from a timeout. */
static int stop_wait(struct experiment*d,u32 expected){unsigned int i;
 for(i=0;i<800;i++){
  if(readl(d->bar+ODB)&1)return -EPROTO;
  if(readl(d->bar+0x28)!=0x1fb||readl(d->bar+0x34)!=0xff)return -EIO;
  if(readl(d->bar+0x1c)==expected)return 0;
  usleep_range(1000,1500);
 }
 return -ETIMEDOUT;
}
static int stop_exchange(struct experiment*d){int rc;u32 epoch=d->stop_epoch;
 rc=stop_wait(d,0x71000000u|epoch);if(rc)return rc;
 if(d->stop_case>=3)msleep(120);
 if(readl(d->bar+ODB)&1)return -EPROTO;
 record(d,"STOPCASE READY case=%u pending=%u sequence=%u epoch=%u\n",d->stop_case,d->pending,d->sequence,epoch);
 if(d->stop_case!=3){writel(0x72000000u|epoch,d->bar+0x14);readl(d->bar+0x14);}
 else record(d,"STOPCASE intentionally omitting STOP\n");
 rc=stop_wait(d,0x73000000u|epoch);if(rc)return rc;
 record(d,"STOPCASE DRAINED case=%u pending=%u sequence=%u\n",d->stop_case,d->pending,d->sequence);
 if(d->stop_case!=4){writel(0x74000000u|epoch,d->bar+0x14);readl(d->bar+0x14);}
 else record(d,"STOPCASE intentionally omitting RELEASE; await bounded callback return\n");
 return 0;
}

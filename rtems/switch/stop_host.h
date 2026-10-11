/* Serialized under the existing session lock, inside the outstanding callback.
 * Refuse completion before RELEASE, mask drift, stale words and timeout. */
static int stop_wait(struct experiment*d,u32 expected){unsigned int i;u32 v;
 for(i=0;i<800;i++){
  if(readl(d->bar+ODB)&1)return -EPROTO;
  if(readl(d->bar+0x28)!=0x1fb||readl(d->bar+0x34)!=0xff)return -EIO;
  v=readl(d->bar+0x1c);if(v==expected)return 0;
  usleep_range(1000,1500);
 }
 return -ETIMEDOUT;
}
static int stop_exchange(struct experiment*d){int rc;u32 epoch=d->stop_epoch;
 rc=stop_wait(d,0x71000000u|epoch);if(rc)return rc;
 msleep(d->stop_delay_ms);
 if(readl(d->bar+ODB)&1)return -EPROTO;
 record(d,"STOP1 READY; callback pending=%u sequence=%u delay_ms=%u epoch=%u\n",d->pending,d->sequence,d->stop_delay_ms,epoch);
 writel(0x72000000u|epoch,d->bar+0x14);readl(d->bar+0x14);
 rc=stop_wait(d,0x73000000u|epoch);if(rc)return rc;
 record(d,"STOP1 DRAINED; callback pending=%u sequence=%u; sending RELEASE\n",d->pending,d->sequence);
 writel(0x74000000u|epoch,d->bar+0x14);readl(d->bar+0x14);return 0;
}

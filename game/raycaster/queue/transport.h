/* Paired targeted reads are additional evidence, never a replacement audit. */
static int fq_targeted(struct experiment*d)
{
 unsigned int i,mask;const u8*r;int rc;
 rc=read_pair(d,BIO_BASE+BIO_OUTPUT,64,54);if(rc)return rc;
 r=d->capture[54].data;
 if(fq_word(r)!=FQ_MAGIC||fq_word(r+4)!=1||fq_word(r+8)>FQ_CORRUPT||fq_word(r+40)!=d->sequence)return -ENODATA;
 mask=fq_word(r+16);if(mask>3)return -ENODATA;
 for(i=44;i<64;i++)if(r[i])return -ENODATA;
 for(i=0;i<2;i++){
  if(fq_word(r+32+4*i)!=((mask&(1u<<i))?FQ_FRAME:0))return -ENODATA;
  if(!(mask&(1u<<i)))continue;
  rc=read_pair(d,STAGING_BASE+FQ_OFFSET+i*FQ_SLOT_SIZE,FQ_SLOT_SIZE,56+2*i);if(rc)return rc;
  if(!fq_valid(d->capture[56+2*i].data,fq_word(r+12),fq_word(r+24+4*i),i))return -ENODATA;
 }
 return 0;
}
static int fq_match_audit(struct experiment*d)
{
 const u8*r=d->capture[54].data;unsigned int i;
 if(memcmp(r,d->stage[6].data+BIO_OFFSET+BIO_OUTPUT,64))return -ENODATA;
 for(i=0;i<2;i++)if((fq_word(r+16)&(1u<<i))&&
    memcmp(d->capture[56+2*i].data,d->stage[6].data+FQ_OFFSET+i*FQ_SLOT_SIZE,FQ_SLOT_SIZE))return -ENODATA;
 return 0;
}

/* Fixed data-only change. Never change DMA, completion, or error-print paths.
 * Dirty is set before the write and included in all resource-retention gates. */
static int quiet_pair(struct experiment *d,u32 address,const u8 *expected,u16 n)
{
    u8 first[256];int rc;
    if(n>sizeof(first)) return -EINVAL;
    rc=issue(d,0x20,n,address-STAGING_BASE,0xa5,ARRAY_SIZE(d->capture));
    if(rc) return rc;
    memcpy(first,d->dma_buf,n);
    rc=issue(d,0x20,n,address-STAGING_BASE,0x5a,ARRAY_SIZE(d->capture));
    if(rc) return rc;
    if(memcmp(first,d->dma_buf,n) || memcmp(first,expected,n)) return -ENODATA;
    record(d,"QUIET PAIR address=%08x bytes=%u data=%*phN\n",address,n,n,first);
    return 0;
}
static int quiet_check(struct experiment *d)
{
    u8 expected[sizeof(quiet_original)];
    if(!d->quiet_dirty) return -EPERM;
    memcpy(expected,quiet_original,sizeof(expected));expected[0]=0;
    return quiet_pair(d,QUIET_ADDRESS,expected,sizeof(expected));
}
static int quiet_cache(struct experiment *d)
{
    int rc=load_table(d,exec_ram_pointer,32);
    if(!rc) rc=load_expect(d,0x017d);
    if(!rc) rc=load_table(d,d->capture[22].data,43);
    if(!rc) rc=load_expect(d,0x017e);
    return rc;
}
static int quiet_begin(struct experiment *d)
{
    static const u8 pointer[]={0x80,0x07,0x11,0xc0};
    static const u8 methods[]={0x90,0xce,0x04,0xc0,0xd0,0xce,0x04,0xc0};
    u8 word[4];int rc;
    d->quiet_armed=true;
    rc=quiet_pair(d,0xc011e22c,pointer,sizeof(pointer));if(rc) return rc;
    rc=quiet_pair(d,0xc0110860,methods,sizeof(methods));if(rc) return rc;
    rc=quiet_pair(d,0xc000a2a0,quiet_printf,sizeof(quiet_printf));if(rc) return rc;
    rc=quiet_pair(d,0xc000a120,quiet_uart,sizeof(quiet_uart));if(rc) return rc;
    rc=quiet_pair(d,QUIET_ADDRESS,quiet_original,sizeof(quiet_original));if(rc) return rc;
    memcpy(word,quiet_original,4);word[0]=0;
    d->quiet_dirty=true;
    rc=exec_upload(d,word,4,QUIET_OFFSET,ARRAY_SIZE(d->capture));if(rc) return rc;
    rc=quiet_cache(d);if(rc) return rc;
    rc=quiet_check(d);if(rc) return rc;
    record(d,"QUIET BEGIN: only upload format first byte suppressed; DMA and completion unchanged\n");
    return 0;
}
static int quiet_end(struct experiment *d)
{
    int rc;
    /* A failed write may have left either exact old or exact new data.
     * Restore from the pinned preimage, then verify the whole 80-byte region. */
    if(d->pending || d->runner_uncertain) return -EBUSY;
    rc=exec_upload(d,quiet_original,4,QUIET_OFFSET,ARRAY_SIZE(d->capture));if(rc) return rc;
    rc=quiet_cache(d);if(rc) return rc;
    rc=quiet_pair(d,QUIET_ADDRESS,quiet_original,sizeof(quiet_original));if(rc) return rc;
    d->quiet_dirty=false;
    record(d,"QUIET END: original format and neighboring handler restored byte-for-byte\n");
    return 0;
}

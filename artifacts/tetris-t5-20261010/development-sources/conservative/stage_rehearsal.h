/* Included after issue(): fixed no-program staging transaction.
 * Every write attempt sets dirty BEFORE submission. A known-complete error
 * enters restoration; uncertain completion stops all commands and pins DMA.
 */
static int stage_hash(struct experiment *d, const u8 *data,
                      const u8 *expected, const char *label)
{
    struct crypto_shash *tfm;
    struct shash_desc *desc;
    u8 digest[32];
    int rc;
    tfm = crypto_alloc_shash("sha256", 0, 0);
    if (IS_ERR(tfm)) return PTR_ERR(tfm);
    desc = kzalloc(sizeof(*desc) + crypto_shash_descsize(tfm), GFP_KERNEL);
    if (!desc) { crypto_free_shash(tfm); return -ENOMEM; }
    desc->tfm = tfm;
    rc = crypto_shash_digest(desc, data, IMAGE_WINDOW, digest);
    if (!rc) {
        record(d, "stage %s sha256=%*phN\n", label, 32, digest);
        if (memcmp(digest, expected, 32)) rc = -ENODATA;
    }
    kfree(desc);
    crypto_free_shash(tfm);
    return rc;
}

static int stage_read_pair(struct experiment *d, unsigned int slot,
                           const u8 *hash, const char *label)
{
    unsigned int off, pass;
    int rc;
    for (pass = 0; pass < 2; pass++) {
        for (off = 0; off < IMAGE_WINDOW; off += MAX_READ) {
            u16 count = min_t(u32, MAX_READ, IMAGE_WINDOW - off);
            rc = issue(d, 0x20, count, off, pass ? 0x5a : 0xa5,
                       ARRAY_SIZE(d->capture));
            if (rc) return rc;
            memcpy(d->stage[slot + pass].data + off, d->dma_buf, count);
        }
    }
    if (memcmp(d->stage[slot].data, d->stage[slot + 1].data, IMAGE_WINDOW))
        return -ENODATA;
    rc = stage_hash(d, d->stage[slot].data, hash, label);
    if (!rc) record(d, "VERIFIED stage %s: paired 524288-byte reads and pinned SHA256\n", label);
    return rc;
}

/* Included after stage read/hash helpers. Only uses existing stock 20/21 and
 * temporary returning 6F callbacks. Never invokes flash commands. */
static int load_digest(const void *data, unsigned int size, u8 digest[32])
{
    struct crypto_shash *tfm = crypto_alloc_shash("sha256",0,0);
    struct shash_desc *desc;
    int rc;
    if (IS_ERR(tfm)) return PTR_ERR(tfm);
    desc = kzalloc(sizeof(*desc)+crypto_shash_descsize(tfm),GFP_KERNEL);
    if (!desc) { crypto_free_shash(tfm); return -ENOMEM; }
    desc->tfm=tfm;
    rc=crypto_shash_digest(desc,data,size,digest);
    kfree(desc);crypto_free_shash(tfm);return rc;
}
static int load_chunks(struct experiment *d,const u8 *data)
{
    u32 off;
    int rc;
    for(off=0;off<d->payload->size;off+=MAX_READ) {
        u16 count=min_t(u32,MAX_READ,d->payload->size-off);
        d->upload_data=data+off;
        rc=issue(d,0x21,count,off,0xa5,ARRAY_SIZE(d->capture));
        d->upload_data=NULL;
        if(rc) return rc;
    }
    return 0;
}
static int load_expect(struct experiment *d,u16 expected)
{
    unsigned int i;
    int rc;
    for(i=0;i<4;i++) {
        d->exec_expected_status=0xffff;
        rc=issue(d,0x6f,0,0,0xa5,34);
        if(rc) return rc;
        if(d->exec_last_status==expected) return 0;
        /* Only harmless ROM PING / cache-control callbacks can repeat here.
         * Never used while the executable runner could remain installed. */
        if(d->exec_last_status!=0x017e && d->exec_last_status!=0x017d) return -ENODATA;
        rc=issue(d,0x1c,0,0,0x5a,3);
        if(rc) return rc;
        msleep(20);
    }
    return -ENODATA;
}
static int load_code(struct experiment *d,const u8 *code,u32 offset,u16 size,
                     unsigned int upload_slot,unsigned int read_slot)
{
    int rc=exec_upload(d,code,size,offset,upload_slot);
    if(!rc) rc=read_pair(d,STAGING_BASE+offset,EXEC_REGION_SIZE,read_slot);
    if(!rc && memcmp(code,d->capture[read_slot].data,size)) rc=-ENODATA;
    return rc;
}
static int load_table(struct experiment *d,const u8 *pointer,unsigned int slot)
{
    int rc=exec_upload(d,pointer,4,EXEC_TABLE_OFFSET,31);
    if(!rc) rc=read_pair(d,EXEC_TABLE_ADDRESS,4,slot);
    if(!rc && memcmp(pointer,d->capture[slot].data,4)) rc=-ENODATA;
    return rc;
}
static int load_output(struct experiment *d)
{
    unsigned int pass,off;
    int rc;
    for(pass=0;pass<2;pass++) for(off=0;off<IMAGE_WINDOW;off+=MAX_READ) {
        u16 count=min_t(u32,MAX_READ,IMAGE_WINDOW-off);
        rc=issue(d,0x20,count,off,pass?0x5a:0xa5,ARRAY_SIZE(d->capture));
        if(rc) return rc;
        memcpy(d->stage[6+pass].data+off,d->dma_buf,count);
    }
    if(memcmp(d->stage[6].data,d->stage[7].data,IMAGE_WINDOW) ||
       !bio_response_valid(d->stage[2].data,d->stage[6].data,IMAGE_WINDOW))
        return -ENODATA;
    record(d,"VERIFIED buffer response sequence=%u status=%u bytes=%u; paired reads and immutable guards\n",
           bio_word(d->stage[6].data+BIO_OFFSET+28),
           bio_word(d->stage[6].data+BIO_OFFSET+20),
           bio_word(d->stage[6].data+BIO_OFFSET+24));
    return 0;
}
/* Persistent BIO1 session. Same transport and pinned runner as loadrun.
 * Full paired image verification remains on every STEP, including immutable
 * bytes. Only the BIO block is uploaded after OPEN. Never retries user code. */
static int session_close(struct experiment *d)
{
    int rc=0, step;
    if(d->pending || d->runner_uncertain) return -EBUSY;
    if(d->exec_dirty) {
        rc=load_table(d,d->capture[22].data,43);
        if(!rc) rc=load_expect(d,0x017e);
        if(rc) return rc;
        rc=load_code(d,d->capture[24].data,EXEC_RAM_OFFSET,EXEC_RAM_SIZE,45,46);
        if(!rc && memcmp(d->capture[24].data,d->capture[46].data,EXEC_REGION_SIZE)) rc=-ENODATA;
        if(rc) return rc;
        rc=load_code(d,d->capture[26].data,EXEC_FLASH_OFFSET,EXEC_FLASH_SIZE,48,49);
        if(!rc && memcmp(d->capture[26].data,d->capture[49].data,EXEC_REGION_SIZE)) rc=-ENODATA;
        if(rc) return rc;
        rc=exec_upload(d,d->capture[18].data,16,LOAD_RESULT_OFFSET,52);
        if(!rc) rc=read_pair(d,LOAD_RESULT_ADDRESS,16,52);
        if(!rc && memcmp(d->capture[18].data,d->capture[52].data,16)) rc=-ENODATA;
        if(rc) return rc;
        d->exec_dirty=false;
    }
    if(d->stage_dirty) {
        rc=load_chunks(d,d->stage[0].data);
        if(rc) return rc;
        rc=stage_read_pair(d,4,stage_candidate_sha256,"session-restored");
        if(!rc && memcmp(d->stage[0].data,d->stage[4].data,IMAGE_WINDOW)) rc=-ENODATA;
        if(rc) return rc;
        d->stage_dirty=false;
    }
    step=issue(d,0x1c,0,0,0x5a,3);
    if(!step && !sp_profile(d->capture[3].data)) step=-ENODATA;
    d->exec_armed=false;d->load_armed=false;d->ready=false;
    record(d,"SESSION CLOSE rc=%d pending=%u exec-dirty=%u stage-dirty=%u\n",
           step,d->pending,d->exec_dirty,d->stage_dirty);
    return step;
}
static int session_open(struct experiment *d)
{
    u8 expected[32];u32 word;int rc;
    if(!d->runtime_verified) return -EPERM;
    rc=stage_read_pair(d,0,stage_candidate_sha256,"session-original");
    if(rc) return rc;
    d->exec_armed=true;d->load_armed=true;
    rc=read_pair(d,EXEC_TABLE_ADDRESS,4,22);if(rc) return rc;
    if(sp_word(d->capture[22].data)!=0xfefe001cu) return -ENODATA;
    rc=read_pair(d,EXEC_RAM_ADDRESS,EXEC_REGION_SIZE,24);if(rc) return rc;
    rc=read_pair(d,EXEC_FLASH_ADDRESS,EXEC_REGION_SIZE,26);if(rc) return rc;
    rc=read_pair(d,LOAD_RESULT_ADDRESS,16,18);if(rc) return rc;
    memcpy(d->runner_code,exec_flash_code,EXEC_FLASH_SIZE);
    word=cpu_to_le32(payload_argument);memcpy(d->runner_code+16,&word,4);
    word=cpu_to_le32(STAGING_BASE+entry_offset);memcpy(d->runner_code+24,&word,4);
    memcpy(d->stage[4].data,d->stage[0].data,IMAGE_WINDOW);
    memcpy(d->stage[4].data,d->payload->data,d->payload->size);
    rc=load_digest(d->stage[4].data,IMAGE_WINDOW,expected);if(rc) return rc;
    d->stage_dirty=true;
    rc=load_chunks(d,d->payload->data);if(rc) return rc;
    rc=stage_read_pair(d,2,expected,"session-uploaded");if(rc) return rc;
    d->exec_dirty=true;
    rc=load_code(d,exec_ram_code,EXEC_RAM_OFFSET,EXEC_RAM_SIZE,28,29);if(rc) return rc;
    rc=load_code(d,d->runner_code,EXEC_FLASH_OFFSET,EXEC_FLASH_SIZE,35,36);if(rc) return rc;
    d->ready=true;
    record(d,"SESSION OPEN ready; original saved; no user callback armed\n");
    return 0;
}
static int session_step(struct experiment *d,const u8 *request)
{
    static const u8 sentinel[16]={0xde,0xad,0xbe,0xef};
    int rc;u64 start=ktime_get_ns();
    if(!d->ready || d->pending || d->runner_uncertain) return -EPERM;
    if(!bio_request_valid(request) || bio_word(request+8)<=d->sequence) return -EINVAL;
    /* Consume sequence before submission: a failed request is never replayed. */
    d->sequence=bio_word(request+8);
    memcpy(d->stage[2].data+BIO_OFFSET,request,BIO_SIZE);
    d->upload_data=request;
    rc=issue(d,0x21,BIO_SIZE,BIO_OFFSET,0xa5,ARRAY_SIZE(d->capture));
    d->upload_data=NULL;if(rc) return rc;
    /* CPU cache coherence handshake; harmless callback may repeat. */
    rc=load_table(d,exec_ram_pointer,32);if(rc) return rc;
    rc=load_expect(d,0x017d);if(rc) return rc;
    rc=exec_upload(d,sentinel,16,LOAD_RESULT_OFFSET,20);if(rc) return rc;
    d->runner_uncertain=true; /* before the first possible arm write */
    rc=load_table(d,exec_flash_pointer,39);if(rc) return rc;
    d->exec_expected_status=0x017f;
    rc=issue(d,0x6f,0,0,0x5a,41);if(rc) return rc;
    rc=read_pair(d,EXEC_TABLE_ADDRESS,4,43);if(rc) return rc;
    if(sp_word(d->capture[43].data)!=0xfefe001cu) return -ENODATA;
    d->runner_uncertain=false;
    rc=read_pair(d,LOAD_RESULT_ADDRESS,16,20);if(rc) return rc;
    if(sp_word(d->capture[20].data+4)!=0x52554e31u || sp_word(d->capture[20].data)) return -ENODATA;
    rc=load_output(d);if(rc) return rc;
    record(d,"SESSION STEP sequence=%u elapsed_ns=%llu; full paired image valid; PING dispatch\n",
           d->sequence,(unsigned long long)(ktime_get_ns()-start));
    return 0;
}
/* Probe performs read-only preflight. OPEN does the borrowing. */
static int run_stage(struct experiment *d) { return 0; }

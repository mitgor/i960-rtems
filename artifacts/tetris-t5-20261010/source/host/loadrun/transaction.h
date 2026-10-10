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
static int run_stage(struct experiment *d)
{
    static const u8 sentinel[16]={0xde,0xad,0xbe,0xef};
    u8 expected[32],payload_sha[32];
    u32 word;
    u64 timing_start=ktime_get_ns(),timing_call=0,timing_return=0,timing_output=0;
    bool payload_attempted=false,code_attempted=false,result_attempted=false;
    bool runner_table_attempted=false,runner_disarmed=false;
    int rc,step,restore_rc=0,test_rc;
    if(!d->runtime_verified) return -EPERM;
    rc=stage_read_pair(d,0,stage_candidate_sha256,"firmware-before-load");
    if(rc) return rc;
    d->exec_armed=true;d->load_armed=true;
    rc=read_pair(d,EXEC_TABLE_ADDRESS,4,22);
    if(rc) goto done;
    if(sp_word(d->capture[22].data)!=0xfefe001cu) {rc=-ENODATA;goto done;}
    rc=read_pair(d,EXEC_RAM_ADDRESS,EXEC_REGION_SIZE,24);if(rc) goto done;
    rc=read_pair(d,EXEC_FLASH_ADDRESS,EXEC_REGION_SIZE,26);if(rc) goto done;
    rc=read_pair(d,LOAD_RESULT_ADDRESS,16,18);if(rc) goto done;
    memcpy(d->runner_code,exec_flash_code,EXEC_FLASH_SIZE);
    word=cpu_to_le32(payload_argument);memcpy(d->runner_code+16,&word,4);
    word=cpu_to_le32(STAGING_BASE+entry_offset);memcpy(d->runner_code+24,&word,4);
    rc=load_digest(d->payload->data,d->payload->size,payload_sha);if(rc) goto done;
    record(d,"payload bytes=%zu entry=%08x argument=%08x sha256=%*phN\n",
           d->payload->size,STAGING_BASE+entry_offset,payload_argument,32,payload_sha);
    memcpy(d->stage[4].data,d->stage[0].data,IMAGE_WINDOW);
    memcpy(d->stage[4].data,d->payload->data,d->payload->size);
    rc=load_digest(d->stage[4].data,IMAGE_WINDOW,expected);if(rc) goto done;
    d->stage_dirty=true;payload_attempted=true;
    rc=load_chunks(d,d->payload->data);if(rc) goto restore;
    rc=stage_read_pair(d,2,expected,"uploaded-payload");if(rc) goto restore;
    d->exec_dirty=true;code_attempted=true;
    rc=load_code(d,exec_ram_code,EXEC_RAM_OFFSET,EXEC_RAM_SIZE,28,29);if(rc) goto restore;
    rc=load_table(d,exec_ram_pointer,32);if(rc) goto restore;
    rc=load_expect(d,0x017d);if(rc) goto restore;
    record(d,"VERIFIED cache-control callback returned 017D\n");
    rc=load_code(d,d->runner_code,EXEC_FLASH_OFFSET,EXEC_FLASH_SIZE,35,36);if(rc) goto restore;
    result_attempted=true;
    rc=exec_upload(d,sentinel,16,LOAD_RESULT_OFFSET,20);if(rc) goto restore;
    runner_table_attempted=true;
    rc=load_table(d,exec_flash_pointer,39);if(rc) goto restore;
    d->exec_expected_status=0x017f;
    record(d,"EXECUTE payload once; no retry after this submission\n");
    timing_call=ktime_get_ns();
    rc=issue(d,0x6f,0,0,0x5a,41);
    timing_return=ktime_get_ns();
    if(rc) goto restore;
    rc=read_pair(d,EXEC_TABLE_ADDRESS,4,43);if(rc) goto restore;
    if(sp_word(d->capture[43].data)!=0xfefe001cu) {rc=-ENODATA;goto restore;}
    runner_disarmed=true;
    rc=read_pair(d,LOAD_RESULT_ADDRESS,16,20);if(rc) goto restore;
    if(sp_word(d->capture[20].data+4)!=0x52554e31u) {rc=-ENODATA;goto restore;}
    record(d,"PAYLOAD RETURN value=%08x decimal=%u marker=52554e31; runner self-disarmed\n",
           sp_word(d->capture[20].data),sp_word(d->capture[20].data));
    if(buffer_io) rc=load_output(d);
    timing_output=ktime_get_ns();
restore:
    test_rc=rc;
    if(d->pending || (runner_table_attempted && !runner_disarmed)) goto done;
    if(code_attempted) {
        step=load_table(d,d->capture[22].data,43);
        if(!step) step=load_expect(d,0x017e);
        if(step) {rc=step;goto done;}
        step=load_code(d,d->capture[24].data,EXEC_RAM_OFFSET,EXEC_RAM_SIZE,45,46);
        if(!step && memcmp(d->capture[24].data,d->capture[46].data,EXEC_REGION_SIZE)) step=-ENODATA;
        if(step) restore_rc=step;
        if(d->pending) {rc=step;goto done;}
        step=load_code(d,d->capture[26].data,EXEC_FLASH_OFFSET,EXEC_FLASH_SIZE,48,49);
        if(!step && memcmp(d->capture[26].data,d->capture[49].data,EXEC_REGION_SIZE)) step=-ENODATA;
        if(step && !restore_rc) restore_rc=step;
        if(d->pending) {rc=step;goto done;}
        if(result_attempted) {
            step=exec_upload(d,d->capture[18].data,16,LOAD_RESULT_OFFSET,52);
            if(!step) step=read_pair(d,LOAD_RESULT_ADDRESS,16,52);
            if(!step && memcmp(d->capture[18].data,d->capture[52].data,16)) step=-ENODATA;
            if(step && !restore_rc) restore_rc=step;
            if(d->pending) {rc=step;goto done;}
        }
        if(!restore_rc) d->exec_dirty=false;
    }
    if(payload_attempted) {
        step=load_chunks(d,d->stage[0].data);
        if(d->pending) {rc=step;goto done;}
        if(step && !restore_rc) restore_rc=step;
        step=stage_read_pair(d,4,stage_candidate_sha256,"restored-firmware");
        if(!step && memcmp(d->stage[0].data,d->stage[4].data,IMAGE_WINDOW)) step=-ENODATA;
        if(!step) d->stage_dirty=false;
        if(step && !restore_rc) restore_rc=step;
    }
    rc=test_rc ? test_rc:restore_rc;
    if(!d->pending) {
        step=issue(d,0x1c,0,0,0x5a,3);
        if(!step && !sp_profile(d->capture[3].data)) step=-ENODATA;
        if(!rc) rc=step;
    }
    if(!rc) record(d,"RESTORED firmware image, PING dispatch, code and result RAM; stock health verified\n");
done:
    if(!rc && timing_call && timing_return && timing_output)
        record(d,"TIMING setup_ns=%llu call_ns=%llu output_ns=%llu restore_ns=%llu\n",
               (unsigned long long)(timing_call-timing_start),
               (unsigned long long)(timing_return-timing_call),
               (unsigned long long)(timing_output-timing_return),
               (unsigned long long)(ktime_get_ns()-timing_output));
    d->upload_data=NULL;d->load_armed=false;d->exec_armed=false;
    return rc;
}

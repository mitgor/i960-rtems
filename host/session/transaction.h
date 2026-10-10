/* Persistent BIO1 session. Same transport and pinned runner as loadrun.
 * Paired payload/code checks on every STEP; full allocation every 32 STEP
 * calls and on CLOSE. Only the BIO block is uploaded after OPEN. Never retries user code. */
static int session_close(struct experiment *d)
{
    int rc=0, step, audit_rc=0;
    if(d->pending || d->runner_uncertain) return -EBUSY;
    if(d->output_valid) {
        audit_rc=session_output(d,IMAGE_WINDOW);
        d->output_valid=false;
        if(d->pending) return audit_rc;
    }
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
    if(!step) step=audit_rc;
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
    d->steps=0;d->output_valid=false;
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
    /* First-entry cache handshake. Subsequent calls follow the runner's
     * self-disarm + dcctl invalidation; no intervening 6F dispatch reloads the
     * table. The unchanged runner invalidates I/D caches again on entry. */
    if(!d->steps) {
        rc=load_table(d,exec_ram_pointer,32);if(rc) return rc;
        rc=load_expect(d,0x017d);if(rc) return rc;
    }
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
    d->steps++;
    d->output_length=(d->steps%32)?BIO_IMAGE_SIZE:IMAGE_WINDOW;
    rc=session_output(d,d->output_length);if(rc) return rc;
    d->output_valid=true;
    record(d,"SESSION STEP sequence=%u elapsed_ns=%llu audit_bytes=%u; paired immutable bytes valid; PING dispatch\n",
           d->sequence,(unsigned long long)(ktime_get_ns()-start),d->output_length);
    return 0;
}
/* Probe performs read-only preflight. OPEN does the borrowing. */
static int run_stage(struct experiment *d) { (void)d;return 0; }

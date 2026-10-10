static int one(int fail,int timeout)
{
    struct experiment d={0};struct firmware fw;unsigned int i;int rc,n,boundary;
    u8 *payload=calloc(1,BIO_IMAGE_SIZE),*b=payload+BIO_OFFSET;
    put(b,BIO_MAGIC);put(b+4,1);put(b+8,42);put(b+12,4);put(b+16,8192);put(b+20,BIO_PENDING);
    memcpy(b+BIO_INPUT+1,"abc",3);
    memset(b+BIO_GUARD1,0xa5,16);memset(b+BIO_OUTPUT,0xcc,BIO_OUTPUT_MAX);memset(b+BIO_GUARD2,0x5a,16);
    memset(card,0,sizeof(card));memcpy(card,original,IMAGE_WINDOW);put(table,0xfefe001c);
    calls=executions=0;fail_at=fail;timeout_mode=timeout;payload_argument=BIO_BASE;
    fw.size=BIO_IMAGE_SIZE;fw.data=payload;d.payload=&fw;d.runtime_verified=true;
    for(i=0;i<54;i++)d.capture[i].data=calloc(1,128);
    for(i=0;i<8;i++)d.stage[i].data=calloc(1,IMAGE_WINDOW);
    rc=session_open(&d);
    if(!rc) rc=session_step(&d,b);
    if(!rc) {
        boundary=calls;
        assert(session_step(&d,b)==-EINVAL && calls==boundary); /* stale */
        put(b+8,43);b[BIO_GUARD1]^=1;
        assert(session_step(&d,b)==-EINVAL && calls==boundary); /* malformed */
        b[BIO_GUARD1]^=1;
        d.steps=31; /* exercise periodic full audit in the fault sweep */
        rc=session_step(&d,b);
    }
    boundary=calls;
    if(d.pending || d.runner_uncertain) {
        assert(session_close(&d)==-EBUSY && calls==boundary);
        assert(d.exec_dirty || d.stage_dirty || d.pending);
    } else {
        int close_rc=session_close(&d);
        if(!rc) rc=close_rc;
    }
    n=calls;
    assert(executions<=2);
    if(fail) assert(rc && calls>=fail);
    if(!fail && !corrupt) assert(!rc && executions==2 && !d.exec_dirty && !d.stage_dirty);
    if(d.pending) assert(calls==fail);
    if(!d.stage_dirty && !d.exec_dirty) {
        assert(!memcmp(card,original,IMAGE_WINDOW));assert(sp_word(table)==0xfefe001c);
        for(i=IMAGE_WINDOW;i<sizeof(card);i++) assert(!card[i]);
    }
    if(corrupt) assert(rc);
    if(corrupt==6) assert(d.stage_dirty);
    assert(!d.upload_data);
    for(i=0;i<54;i++)free(d.capture[i].data);
    for(i=0;i<8;i++)free(d.stage[i].data);
    free(payload);return n;
}
int main(int argc,char **argv)
{
    int i,n;FILE *f;assert(argc==2);
    f=fopen(argv[1],"rb");assert(f);assert(fread(original,1,IMAGE_WINDOW,f)==IMAGE_WINDOW);fclose(f);
    n=one(0,0);
    for(i=1;i<=n;i++) {one(i,0);one(i,1);}
    for(corrupt=1;corrupt<=6;corrupt++) one(0,0);
    printf("session: %d command-boundary faults, stale/malformed requests, 6 output corruptions; ASan/UBSan passed\n",2*n);
    return 0;
}

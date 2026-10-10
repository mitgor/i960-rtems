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

static int stage_upload(struct experiment *d, unsigned int index, bool restore)
{
    const struct stage_patch *p = &stage_patches[index];
    int rc;
    d->upload_data = restore ? p->before : p->after;
    record(d, "stage %s patch=%u offset=%08x bytes=%u\n",
           restore ? "restore" : "apply", index, p->offset, p->size);
    rc = issue(d, 0x21, p->size, p->offset, 0xa5, ARRAY_SIZE(d->capture));
    d->upload_data = NULL;
    return rc;
}

static int run_stage(struct experiment *d)
{
    unsigned int i, attempted = 0;
    int rc, test_rc = 0, restore_rc = 0, step;
    if (!d->runtime_verified) return -EPERM;
    rc = stage_read_pair(d, 0, stage_stock_sha256, "before-stock");
    if (rc) return rc; /* No uploads unless the entire stock preimage is exact. */
    for (i = 0; i < ARRAY_SIZE(stage_patches); i++) {
        const struct stage_patch *p = &stage_patches[i];
        if (memcmp(d->stage[0].data + p->offset, p->before, p->size))
            return -ENODATA;
    }
    d->stage_armed = true;
    for (i = 0; i < ARRAY_SIZE(stage_patches); i++) {
        d->stage_dirty = true;
        attempted = i + 1;
        rc = stage_upload(d, i, false);
        if (rc) goto restore;
    }
    rc = stage_read_pair(d, 2, stage_candidate_sha256, "candidate");
restore:
    test_rc = rc;
    if (d->pending) goto done;
    /* Restore every possibly touched patch, including a failed upload. */
    for (i = 0; i < attempted; i++) {
        step = stage_upload(d, i, true);
        if (step && !restore_rc) restore_rc = step;
        if (d->pending) { rc = test_rc ? test_rc : step; goto done; }
    }
    step = stage_read_pair(d, 4, stage_stock_sha256, "restored-stock");
    if (!step && memcmp(d->stage[0].data, d->stage[4].data, IMAGE_WINDOW))
        step = -ENODATA;
    if (!step) {
        d->stage_dirty = false;
        record(d, "RESTORED full staging image to exact original stock bytes\n");
    }
    if (step && !restore_rc) restore_rc = step;
    rc = test_rc ? test_rc : restore_rc;
    if (!d->pending) {
        step = issue(d, 0x1c, 0, 0, 0x5a, 3);
        if (!step && !sp_profile(d->capture[3].data)) step = -ENODATA;
        if (!rc) rc = step;
    }
done:
    d->stage_armed = false;
    d->upload_data = NULL;
    return rc;
}

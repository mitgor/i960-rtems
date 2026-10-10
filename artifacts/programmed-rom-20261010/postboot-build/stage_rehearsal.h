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

/* Postboot validation: only Enquiry2, normal staging reads, table reads,
 * and returning 6F after exact full image and dispatch validation. */
static int run_stage(struct experiment *d)
{
    int rc;
    if (!d->runtime_verified) return -EPERM;
    rc = stage_read_pair(d, 0, stage_candidate_sha256, "boot-candidate");
    if (rc) return rc;
    d->rom_table_armed = true;
    rc = read_pair(d, EXEC_TABLE_ADDRESS, 4, 22);
    d->rom_table_armed = false;
    if (rc) return rc;
    if (sp_word(d->capture[22].data) != 0xfefe001cu) return -ENODATA;
    record(d, "VERIFIED boot-installed dispatch=FEFE001C\n");
    d->boot_verified = true;
    d->exec_expected_status = 0x017e;
    rc = issue(d, 0x6f, 0, 0, 0xa5, 34);
    if (!rc) rc = issue(d, 0x6f, 0, 0, 0x5a, 41);
    d->boot_verified = false;
    if (rc) return rc;
    record(d, "VERIFIED ROM-resident 6F returned 017E twice after reboot\n");
    rc = issue(d, 0x1c, 0, 0, 0x5a, 3);
    if (!rc && !sp_profile(d->capture[3].data)) rc = -ENODATA;
    if (!rc) rc = stage_read_pair(d, 4, stage_candidate_sha256, "boot-after-ping");
    return rc;
}

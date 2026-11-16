/* Stock-boot-block compatible, deliberately small raw-image loader.
 * The stock reset block has already initialized DRAM and calls this copied
 * loader with the flash source in g0 and the DRAM destination in g1.  This
 * does not reinitialize the 80303 or claim to be an independent reset block.
 */
typedef unsigned int u32;

#define FLASH_SOURCE 0xfef47000u
#define RAM_DEST     0xc0010000u
#define STATUS       ((volatile u32 *)0xc0001f00u)
#define MAGIC        0x31544e52u /* "RNT1" in little-endian flash */
#define MAX_PAYLOAD  0x70000u
#ifdef STAGE2_NATIVE_TEST
#define STAGE_SYNC() ((void)0)
#else
#define STAGE_SYNC() __asm__ volatile("syncf" ::: "memory")
#endif

/* This routine is also compiled into the native test harness.  Keeping the
 * bounds and byte-wise FNV here tests the same copy code used by the ROM. */
u32 stage2_copy(const u32 *source, u32 *dest, u32 max_payload, u32 *detail)
{
    u32 bytes, expected, hash = 2166136261u, i, word;
    if (source[0] != MAGIC) return 0x1001u;
    bytes = source[1];
    expected = source[2];
    if (bytes == 0 || bytes > max_payload || (bytes & 3u) || source[3] != 0u)
        return 0x1002u;
    source += 4;
    for (i = 0; i < bytes / 4u; ++i) {
        word = source[i];
        hash ^= word & 255u; hash *= 16777619u;
        hash ^= (word >> 8) & 255u; hash *= 16777619u;
        hash ^= (word >> 16) & 255u; hash *= 16777619u;
        hash ^= (word >> 24) & 255u; hash *= 16777619u;
    }
    *detail = hash;
    if (hash != expected) return 0x1003u;
    for (i = 0; i < bytes / 4u; ++i) dest[i] = source[i];
    STAGE_SYNC();
    return 0x2000u;
}

#ifndef STAGE2_NATIVE_TEST
void stage2(const u32 *source, u32 *dest)
{
    u32 result, detail = 0;
    STATUS[0] = 0x32544753u; /* SGT2: entered stage two */
    if ((u32)source != FLASH_SOURCE || (u32)dest != RAM_DEST) {
        STATUS[1] = 0x1001u;
        for (;;) __asm__ volatile("syncf");
    }
    result = stage2_copy(source, dest, MAX_PAYLOAD, &detail);
    STATUS[1] = result;
    STATUS[2] = result == 0x2000u ? source[1] : detail;
    STATUS[3] = result == 0x2000u ? detail : 0;
    __asm__ volatile("syncf" ::: "memory");
    if (result != 0x2000u) for (;;) __asm__ volatile("syncf");
    /* Return to the stock boot block, which enables D-cache and branches to
     * the trailer's RTEMS entry.  No stock controller runtime is loaded. */
}
#endif

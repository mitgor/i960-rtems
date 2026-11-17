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
#ifdef ACCELE160_PCI_RELEASE
#include "pci_release.h"
#ifndef ACCELE160_PCI_RELEASE_OPTIONS
#define ACCELE160_PCI_RELEASE_OPTIONS 0u
#endif
/* Same access widths as the stock runtime (stob/stos/st) on the local
 * 80303 register blocks. */
static accele160_u32 mmr_read(accele160_u32 address, accele160_u32 size, void *context)
{
    (void)context;
    if (size == 1) return *(volatile unsigned char *)address;
    if (size == 2) return *(volatile unsigned short *)address;
    return *(volatile u32 *)address;
}
static void mmr_write(accele160_u32 address, accele160_u32 size,
                      accele160_u32 value, void *context)
{
    (void)context;
    if (size == 1) *(volatile unsigned char *)address = (unsigned char)value;
    else if (size == 2) *(volatile unsigned short *)address = (unsigned short)value;
    else *(volatile u32 *)address = value;
}
/* First native code after the stock reset block. Program the stock host
 * identity and clear EBCR Configuration Cycle Retry here, before anything
 * that can fail, so that a bad payload, an RTEMS fault or a park no longer
 * leaves the host BIOS retrying configuration cycles forever. */
static void release_host_pci(void)
{
    static const accele160_mmr mmr = {mmr_read, mmr_write, 0};
    accele160_pci_release(&mmr, ACCELE160_PCI_RELEASE_OPTIONS,
                          *(volatile unsigned short *)0xfef30000u,
                          (accele160_pci_release_report *)ACCELE160_PCI_RELEASE_REPORT);
    __asm__ volatile("syncf" ::: "memory");
}
#endif
void stage2(const u32 *source, u32 *dest)
{
    u32 result, detail = 0;
    STATUS[0] = 0x32544753u; /* SGT2: entered stage two */
#ifdef ACCELE160_PCI_RELEASE
    release_host_pci();
#endif
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

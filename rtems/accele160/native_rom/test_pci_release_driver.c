/* Host driver for test_pci_release.py: run the real release routine against
 * a byte-array register model and print every store in order.
 * argv: OPTIONS ROM_SIGNATURE INITIAL_EBCR INITIAL_BRIDGE_COMMAND (hex). */
#include <stdio.h>
#include <stdlib.h>
#include "pci_release.h"

static unsigned char regs[0x2000];

static accele160_u32 mmr_read(accele160_u32 a, accele160_u32 size, void *c)
{
    accele160_u32 value = 0, i;
    (void)c;
    if (a < 0x1000 || a + size > 0x1400) { printf("BAD-READ %x\n", a); exit(2); }
    for (i = 0; i < size; ++i) value |= (accele160_u32)regs[a + i] << (8 * i);
    return value;
}

static void mmr_write(accele160_u32 a, accele160_u32 size, accele160_u32 v, void *c)
{
    accele160_u32 i;
    (void)c;
    if (a < 0x1000 || a + size > 0x1400 || (size != 1 && size != 2 && size != 4) ||
        (a & (size - 1))) { printf("BAD-WRITE %x %u\n", a, size); exit(2); }
    printf("W %04x %u %x retry-before=%u\n", a, size, v, (regs[0x1040] >> 2) & 1u);
    for (i = 0; i < size; ++i) regs[a + i] = (unsigned char)(v >> (8 * i));
}

int main(int argc, char **argv)
{
    accele160_mmr mmr = {mmr_read, mmr_write, 0};
    accele160_pci_release_report report = {0};
    accele160_u32 options, signature, ebcr, command, count;
    if (argc != 5) return 2;
    options = strtoul(argv[1], 0, 16);
    signature = strtoul(argv[2], 0, 16);
    ebcr = strtoul(argv[3], 0, 16);
    command = strtoul(argv[4], 0, 16);
    regs[0x1040] = (unsigned char)ebcr; regs[0x1041] = (unsigned char)(ebcr >> 8);
    regs[0x1004] = (unsigned char)command; regs[0x1005] = (unsigned char)(command >> 8);
    count = accele160_pci_release(&mmr, options, signature, &report);
    printf("REPORT %x %x %x %x %x %x %x %u %u\n", report.marker, report.ebcr_before,
           report.ebcr_after, report.flags, report.atu_id, report.atu_subsystem,
           report.bridge_command_before, report.writes, count);
    return 0;
}

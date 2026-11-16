/* Stock-equivalent host PCI identity and configuration-retry release.
 *
 * Intel 80303 initialization mode 3 (application note 273395-005, section
 * 2.3): with RETRY strapped high the primary PCI interface answers every
 * configuration cycle with Retry until the core clears the Configuration
 * Cycle Retry bit, EBCR (local 0x1040) bit 2. Stock firmware 6.00-05 programs
 * the ATU and bridge identity, then writes EBCR = 0x48 and prints
 * "BIOS Cfg Wait...". A native image that never does this leaves the host
 * BIOS retrying forever. See docs/ACCELE160-EBCR-RELEASE-EXPERIMENT.md.
 */
#ifndef ACCELE160_PCI_RELEASE_H
#define ACCELE160_PCI_RELEASE_H

typedef unsigned int accele160_u32;

typedef struct {
    accele160_u32 (*read)(accele160_u32 address, accele160_u32 size, void *context);
    void (*write)(accele160_u32 address, accele160_u32 size,
                  accele160_u32 value, void *context);
    void *context;
} accele160_mmr;

/* Keep the stock expansion-ROM window only when the image still carries the
 * x86 option ROM signature; otherwise (or when HIDE is set) write ERLR = 0,
 * which is the stock firmware's own no-ROM path. */
#define ACCELE160_PCI_HIDE_OPTION_ROM 1u

typedef struct {
    accele160_u32 marker;          /* "PCI0" */
    accele160_u32 ebcr_before;     /* reset/strap value seen before any write */
    accele160_u32 ebcr_after;      /* readback after the releasing write */
    accele160_u32 flags;           /* bit 0 ROM hidden, bit 1 ROM signature seen */
    accele160_u32 atu_id;          /* readback of 0x1200: device << 16 | vendor */
    accele160_u32 atu_subsystem;   /* readback of 0x122c */
    accele160_u32 bridge_command_before;
    accele160_u32 writes;          /* register stores issued */
} accele160_pci_release_report;

#define ACCELE160_PCI_RELEASE_MARKER 0x30494350u /* "PCI0", little-endian */
#define ACCELE160_PCI_RELEASE_REPORT 0xc0001ee0u /* host-visible BAR + 0x1ee0 */
#define ACCELE160_EBCR 0x1040u
#define ACCELE160_EBCR_CONFIG_RETRY 4u
#define ACCELE160_EBCR_STOCK_RELEASE 0x48u

/* rom_signature is the 16-bit word at flash 0xfef30000 (0xaa55 for a valid
 * x86 option ROM). Returns the number of register stores issued. */
accele160_u32 accele160_pci_release(const accele160_mmr *mmr,
                                    accele160_u32 options,
                                    accele160_u32 rom_signature,
                                    accele160_pci_release_report *report);

#endif

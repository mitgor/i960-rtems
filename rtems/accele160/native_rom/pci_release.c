/* See pci_release.h. The table is the ordered list of stores the stock
 * 6.00-05 runtime makes into the bridge, ATU and messaging-unit blocks from
 * its entry through the EBCR release and the MU masking that follows it,
 * captured offline with
 *   rtems/accele160/emulator/pci_register_trace.py
 * (artifacts/current/accele160-pci-release-20261117/stock-pci-reg-writes.json,
 * "seq" below). Stock routines: ATU c0051190, secondary ATU c00513f0, bridge
 * c0051560, interrupt routing c0051b44, release c0052df4. Every ATU value was
 * also cross-checked against the saved live PCI dump of the working card
 * (artifacts/current/accele160-startup-20261016/live-readonly-state.txt).
 *
 * Deliberate differences from stock, all listed in the experiment document:
 *  - the secondary-bus scan (16 SOCCAR selects, seq 46..61) is not run;
 *  - the messaging-unit masking (seq 66..72) runs before the EBCR release
 *    instead of directly after it, so that the release is the last store;
 *  - SISR is written as an aligned 16-bit store (stock uses an unaligned
 *    32-bit store at 0x1042 that also zeroes the low half of PBISR);
 *  - ERLR may be forced to zero to hide the x86 option ROM.
 * Values that stock derives from board model 32 / subsystem 0x0054 are fixed
 * here; this routine is only for that board.
 */
#include "pci_release.h"

enum { PLAIN, SAVE_BRIDGE_COMMAND, RESTORE_BRIDGE_COMMAND, ROM_LIMIT, ROM_BASE };

static const struct {
    unsigned short address;
    unsigned char size;
    unsigned char kind;
    accele160_u32 value;
} writes[] = {
    /* ATU identity and inbound window, stock c0051190 (seq 1..15) */
    {0x1200, 2, PLAIN, 0x1069},      /* ATUVID: Mylex */
    {0x1202, 2, PLAIN, 0x0050},      /* ATUDID */
    {0x122c, 2, PLAIN, 0x1069},      /* ASVIR */
    {0x122e, 2, PLAIN, 0x0054},      /* ASIR, board model 32 */
    {0x120a, 1, PLAIN, 0x04},        /* subclass: RAID */
    {0x120b, 1, PLAIN, 0x01},        /* base class: mass storage */
    {0x120c, 1, PLAIN, 0x10},        /* ATUCLSR */
    {0x120d, 1, PLAIN, 0x40},        /* ATULT */
    {0x1240, 4, PLAIN, 0xffffe000},  /* PIALR: 8 KiB inbound BAR */
    {0x1244, 4, PLAIN, 0xc0000000},  /* PIATVR */
    {0x1206, 2, PLAIN, 0xffff},      /* PATUSR: clear status */
    {0x1274, 4, ROM_LIMIT, 0xffff8000}, /* ERLR: 32 KiB option ROM, or 0 */
    {0x1278, 4, ROM_BASE, 0xfef30000},  /* ERTVR: flash 0x30000 */
    {0x1288, 4, PLAIN, 0x00000106},  /* ATUCR */
    {0x12bc, 4, PLAIN, 0x000000fc},  /* PATUIMR */
    /* secondary ATU, stock c00513f0 (seq 16..23) */
    {0x1298, 2, PLAIN, 0x0000},      /* SATUCMD off while reprogramming */
    {0x124c, 4, PLAIN, 0xff000000},  /* SIALR */
    {0x1250, 4, PLAIN, 0xc0000000},  /* SIATVR */
    {0x1248, 4, PLAIN, 0xfe000008},  /* SIABAR */
    {0x1268, 4, PLAIN, 0xfc000000},  /* SOMWVR */
    {0x1298, 2, PLAIN, 0x0016},      /* SATUCMD */
    {0x1206, 2, PLAIN, 0xffff},      /* PATUSR: clear status */
    {0x12c0, 4, PLAIN, 0x000000fc},  /* SATUIMR */
    /* PCI-to-PCI bridge, stock c0051560 (seq 24..45) */
    {0x1004, 2, SAVE_BRIDGE_COMMAND, 0x0000},
    {0x1044, 4, PLAIN, 0xffffffff},  /* PBISR: clear */
    {0x1048, 4, PLAIN, 0xffffffff},  /* SBISR: clear */
    {0x1034, 2, PLAIN, 0x1069},      /* BSVIR */
    {0x1036, 2, PLAIN, 0x0050},      /* BSIR */
    {0x1020, 2, PLAIN, 0x0000},      /* MBR */
    {0x1022, 2, PLAIN, 0x0000},      /* MLR */
    {0x101c, 1, PLAIN, 0x00},        /* IOBR */
    {0x101d, 1, PLAIN, 0x00},        /* IOLR */
    {0x1054, 1, PLAIN, 0x00},        /* SIOBR */
    {0x1055, 1, PLAIN, 0x00},        /* SIOLR */
    {0x100c, 1, PLAIN, 0x10},        /* CLSR */
    {0x100d, 1, PLAIN, 0x40},        /* PLTR */
    {0x1024, 2, PLAIN, 0x0000},      /* PMBR */
    {0x1026, 2, PLAIN, 0x0000},      /* PMLR */
    {0x1058, 2, PLAIN, 0xfe00},      /* SMBR */
    {0x105a, 2, PLAIN, 0xffff},      /* SMLR */
    {0x105c, 2, PLAIN, 0x0004},      /* SDER */
    {0x101b, 1, PLAIN, 0x40},        /* SLTR */
    {0x101a, 1, PLAIN, 0x00},        /* SUBBNR */
    {0x1004, 2, RESTORE_BRIDGE_COMMAND, 0x0000},
    {0x103e, 2, PLAIN, 0x0200},      /* BCR */
    /* interrupt routing and private devices, stock c0051b44 (seq 62..64) */
    {0x1050, 4, PLAIN, 0x0000000e},  /* PIRSR: S_INTA# to the core */
    {0x1042, 2, PLAIN, 0x03ff},      /* SISR: hide secondary devices */
    {0x104c, 4, PLAIN, 0x00001554},  /* SACR */
    /* Messaging unit, stock c004e450 (seq 66..72). Stock runs this directly
     * after the release; here it runs before, so the host never sees the
     * unmasked reset state. The host driver later unmasks OIMR itself. */
    {0x1324, 4, PLAIN, 0xffffffff},  /* IISR: clear inbound status */
    {0x1328, 4, PLAIN, 0xffffffff},  /* IIMR: mask inbound interrupts */
    {0x1334, 4, PLAIN, 0xffffffff},  /* OIMR: no P_INTA# from the MU */
    {0x1310, 4, PLAIN, 0x00000000},  /* IMR0 */
    {0x1314, 4, PLAIN, 0x00000000},  /* IMR1 */
    {0x1318, 4, PLAIN, 0x00000000},  /* OMR0 */
    {0x131c, 4, PLAIN, 0x00000000},  /* OMR1 */
    /* stock c0052df4 (seq 65): clear Configuration Cycle Retry. Last. */
    {ACCELE160_EBCR, 2, PLAIN, ACCELE160_EBCR_STOCK_RELEASE},
};

accele160_u32 accele160_pci_release(const accele160_mmr *mmr,
                                    accele160_u32 options,
                                    accele160_u32 rom_signature,
                                    accele160_pci_release_report *report)
{
    const int rom = rom_signature == 0xaa55u &&
                    !(options & ACCELE160_PCI_HIDE_OPTION_ROM);
    accele160_u32 bridge_command = 0, count = 0, i, value;

    report->ebcr_before = mmr->read(ACCELE160_EBCR, 2, mmr->context);
    report->flags = (rom ? 0u : 1u) | (rom_signature == 0xaa55u ? 2u : 0u);
    for (i = 0; i < sizeof writes / sizeof writes[0]; ++i) {
        value = writes[i].value;
        switch (writes[i].kind) {
        case SAVE_BRIDGE_COMMAND:
            bridge_command = mmr->read(0x1004, 2, mmr->context);
            break;
        case RESTORE_BRIDGE_COMMAND:
            value = bridge_command;
            break;
        case ROM_LIMIT:
            if (!rom) value = 0;
            break;
        case ROM_BASE:
            if (!rom) continue; /* stock's no-ROM path leaves ERTVR alone */
            break;
        }
        mmr->write(writes[i].address, writes[i].size, value, mmr->context);
        ++count;
    }
    report->ebcr_after = mmr->read(ACCELE160_EBCR, 2, mmr->context);
    report->atu_id = mmr->read(0x1200, 4, mmr->context);
    report->atu_subsystem = mmr->read(0x122c, 4, mmr->context);
    report->bridge_command_before = bridge_command;
    report->writes = count;
    report->marker = ACCELE160_PCI_RELEASE_MARKER; /* last: record is complete */
    return count;
}

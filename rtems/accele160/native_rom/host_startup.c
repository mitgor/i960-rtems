#include "host_startup.h"

accele160_host_snapshot accele160_sample_host_startup(
    accele160_read32 read32, void *context)
{
    accele160_host_snapshot result;
    result.bridge_pci_command = read32(0x1004u, context);
    result.raid_pci_command = read32(0x1204u, context);
    result.inbound_doorbell = read32(0x1320u, context);
    result.inbound_status = read32(0x1324u, context);
    result.inbound_mask = read32(0x1328u, context);
    result.ready_flags = 0;
    if ((result.bridge_pci_command & 4u) == 4u)
        result.ready_flags |= ACCELE160_READY_BRIDGE_PCI;
    if ((result.raid_pci_command & 6u) == 6u)
        result.ready_flags |= ACCELE160_READY_RAID_PCI;
    if ((result.inbound_doorbell & 2u) == 2u)
        result.ready_flags |= ACCELE160_READY_BOOT_DOORBELL;
    return result;
}

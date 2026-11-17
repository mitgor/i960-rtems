#ifndef ACCELE160_HOST_STARTUP_H
#define ACCELE160_HOST_STARTUP_H

/* The stock firmware checks these three host-driven conditions before its
 * post-reset startup continues. This observer never writes a register. */
enum {
    ACCELE160_READY_BRIDGE_PCI = 1u,
    ACCELE160_READY_RAID_PCI = 2u,
    ACCELE160_READY_BOOT_DOORBELL = 4u
};

typedef unsigned int (*accele160_read32)(unsigned int address, void *context);

typedef struct {
    unsigned int bridge_pci_command;
    unsigned int raid_pci_command;
    unsigned int inbound_doorbell;
    unsigned int inbound_status;
    unsigned int inbound_mask;
    unsigned int ready_flags;
} accele160_host_snapshot;

accele160_host_snapshot accele160_sample_host_startup(
    accele160_read32 read32, void *context);

#endif

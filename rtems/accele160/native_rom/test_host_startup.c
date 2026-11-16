/* Exercise the native read-only startup observer against a bounded MMIO fake. */
#include "host_startup.h"
#include <assert.h>

typedef struct {
    unsigned int bridge, raid, doorbell, status, mask;
    unsigned int reads[5], count;
} fake_mmio;

static unsigned int fake_read(unsigned int address, void *context)
{
    fake_mmio *m = (fake_mmio *)context;
    assert(m->count < 5);
    m->reads[m->count++] = address;
    switch (address) {
        case 0x1004u: return m->bridge;
        case 0x1204u: return m->raid;
        case 0x1320u: return m->doorbell;
        case 0x1324u: return m->status;
        case 0x1328u: return m->mask;
        default: assert(0); return 0;
    }
}

static accele160_host_snapshot sample(fake_mmio *m)
{
    static const unsigned int expected[] = {
        0x1004u, 0x1204u, 0x1320u, 0x1324u, 0x1328u
    };
    unsigned int i;
    accele160_host_snapshot s;
    m->count = 0;
    s = accele160_sample_host_startup(fake_read, m);
    assert(m->count == 5);
    for (i = 0; i < 5; ++i) assert(m->reads[i] == expected[i]);
    assert(s.bridge_pci_command == m->bridge);
    assert(s.raid_pci_command == m->raid);
    assert(s.inbound_doorbell == m->doorbell);
    assert(s.inbound_status == m->status);
    assert(s.inbound_mask == m->mask);
    return s;
}

int main(void)
{
    fake_mmio m = {0};
    accele160_host_snapshot s;
    m.mask = 0xffffffffu;
    s = sample(&m);
    assert(s.ready_flags == 0);
    m.bridge = 4;
    s = sample(&m);
    assert(s.ready_flags == ACCELE160_READY_BRIDGE_PCI);
    m.raid = 2; /* Bus master alone does not satisfy the stock gate. */
    s = sample(&m);
    assert(s.ready_flags == ACCELE160_READY_BRIDGE_PCI);
    m.raid = 6;
    m.status = 4; /* A pending MU request is separate from boot doorbell 2. */
    s = sample(&m);
    assert(s.ready_flags == (ACCELE160_READY_BRIDGE_PCI |
                             ACCELE160_READY_RAID_PCI));
    m.doorbell = 2;
    s = sample(&m);
    assert(s.ready_flags == (ACCELE160_READY_BRIDGE_PCI |
                             ACCELE160_READY_RAID_PCI |
                             ACCELE160_READY_BOOT_DOORBELL));
    return 0;
}

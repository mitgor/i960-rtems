/* Validate only the two observed read-only follow-up command shapes. */
#include "host_mailbox.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void read64(const char *path, unsigned char *bytes)
{
    FILE *file = fopen(path, "rb");
    assert(file);
    assert(fread(bytes, 1, 64, file) == 64);
    assert(fgetc(file) == EOF);
    assert(fclose(file) == 0);
}

static void put32(unsigned char *p, unsigned int value)
{
    p[0] = (unsigned char)value;
    p[1] = (unsigned char)(value >> 8);
    p[2] = (unsigned char)(value >> 16);
    p[3] = (unsigned char)(value >> 24);
}

int main(int argc, char **argv)
{
    unsigned char setup_bytes[64], slot[64], changed[64];
    accele160_mem_mbox_request setup;
    accele160_ring_followup_request out;
    unsigned int index;
    assert(argc == 4);
    read64(argv[1], setup_bytes);
    assert(accele160_parse_set_mem_mbox(setup_bytes, 64, &setup) == 0);
    for (index = 1; index <= 2; ++index) {
        read64(argv[index + 1], slot);
        memset(&out, 0xa5, sizeof(out));
        assert(accele160_parse_ring_followup(slot, 64, &setup, index, &out) == 0);
        assert(out.slot_index == index);
        assert(out.command_id == (index == 1 ? 2u : 1u));
        assert(out.ioctl == (index == 1 ? 0x11u : 0x05u));
        assert(out.output_bytes == (index == 1 ? 128u : 512u));
        assert(out.output_bus_address == (index == 1 ? 0x0630e000u : 0x0500ae00u));
        memcpy(changed, slot, 64);
        put32(changed + 32, setup.health_bus + (index == 1 ? 4u : 0u));
        assert(accele160_parse_ring_followup(changed, 64, &setup,
                                              index, &out) == ACCELE160_MAILBOX_ADDRESS);
        assert(accele160_parse_ring_followup(slot, 64, &setup,
                                              3u, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
        memcpy(changed, slot, 64);
        changed[3] = 0x10;
        assert(accele160_parse_ring_followup(changed, 64, &setup,
                                              index, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
        memcpy(changed, slot, 64);
        changed[21] = 0;
        assert(accele160_parse_ring_followup(changed, 64, &setup,
                                              index, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
        memcpy(changed, slot, 64);
        put32(changed + 32, setup.status_ring_bus);
        assert(accele160_parse_ring_followup(changed, 64, &setup,
                                              index, &out) == ACCELE160_MAILBOX_ADDRESS);
        memcpy(changed, slot, 64);
        put32(changed + 32, 0x20000000u);
        assert(accele160_parse_ring_followup(changed, 64, &setup,
                                              index, &out) == ACCELE160_MAILBOX_ADDRESS);
        memcpy(changed, slot, 64);
        changed[36] = 1;
        assert(accele160_parse_ring_followup(changed, 64, &setup,
                                              index, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
        assert(accele160_parse_ring_followup(slot, 63, &setup,
                                              index, &out) == ACCELE160_MAILBOX_SHORT);
    }
    puts("follow-up ring parser PASS (read-only)");
    return 0;
}

/* Validate the two observed later Linux slot shapes without completing them. */
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

static unsigned int get32(const unsigned char *p)
{
    return (unsigned int)p[0] | ((unsigned int)p[1] << 8) |
           ((unsigned int)p[2] << 16) | ((unsigned int)p[3] << 24);
}

int main(int argc, char **argv)
{
    unsigned char setup_bytes[64], slot[64], changed[64];
    accele160_mem_mbox_request setup;
    accele160_ring_next_request out;
    unsigned int index;
    assert(argc == 4);
    read64(argv[1], setup_bytes);
    assert(accele160_parse_set_mem_mbox(setup_bytes, 64, &setup) == 0);
    for (index = 3; index <= 4; ++index) {
        read64(argv[index - 1], slot);
        memset(&out, 0xa5, sizeof(out));
        assert(accele160_parse_ring_next(slot, 64, &setup, index, &out) == 0);
        assert(out.slot_index == index);
        assert(out.command_id == (index == 3 ? 1u :
                                  ((unsigned int)slot[0] |
                                   ((unsigned int)slot[1] << 8))));
        assert(out.opcode == (index == 3 ? 1u : 2u));
        assert(out.output_bytes == (index == 3 ? 1004u : 36u));
        assert(out.output_bus_address == get32(slot + 32));
        assert(out.sense_bus_address ==
               (index == 3 ? 0u : get32(slot + 8)));
        memcpy(changed, slot, 64);
        changed[3] ^= 0x40u;
        assert(accele160_parse_ring_next(changed, 64, &setup,
                                         index, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
        memcpy(changed, slot, 64);
        changed[index == 3 ? 21 : 22] ^= 1u;
        assert(accele160_parse_ring_next(changed, 64, &setup,
                                         index, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
        memcpy(changed, slot, 64);
        put32(changed + 32, setup.command_ring_bus);
        assert(accele160_parse_ring_next(changed, 64, &setup,
                                         index, &out) == ACCELE160_MAILBOX_ADDRESS);
        memcpy(changed, slot, 64);
        put32(changed + 32, 0x20000000u);
        assert(accele160_parse_ring_next(changed, 64, &setup,
                                         index, &out) == ACCELE160_MAILBOX_ADDRESS);
        assert(accele160_parse_ring_next(slot, 63, &setup,
                                         index, &out) == ACCELE160_MAILBOX_SHORT);
    }
    read64(argv[3], slot);
    memcpy(changed, slot, 64);
    put32(changed + 8, setup.status_ring_bus);
    assert(accele160_parse_ring_next(changed, 64, &setup,
                                     4u, &out) == ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, slot, 64);
    put32(changed + 8, get32(changed + 32));
    assert(accele160_parse_ring_next(changed, 64, &setup,
                                     4u, &out) == ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, slot, 64);
    changed[0] = 0;
    changed[1] = 0;
    assert(accele160_parse_ring_next(changed, 64, &setup,
                                     4u, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
    memcpy(changed, slot, 64);
    changed[0] = 0x43u;
    changed[1] = 1u;
    put32(changed + 8, 0x06182000u);
    put32(changed + 32, 0x06188400u);
    assert(accele160_parse_ring_next(changed, 64, &setup, 4u, &out) == 0);
    assert(out.command_id == 0x0143u && out.sense_bus_address == 0x06182000u &&
           out.output_bus_address == 0x06188400u);
    changed[0] = 0x83u;
    changed[1] = 0u;
    assert(accele160_parse_ring_next(changed, 64, &setup, 4u, &out) == 0);
    assert(out.command_id == 0x0083u);
    assert(accele160_parse_ring_next(slot, 64, &setup,
                                     5u, &out) == ACCELE160_MAILBOX_UNSUPPORTED);
    puts("next ring parser PASS (read-only)");
    return 0;
}

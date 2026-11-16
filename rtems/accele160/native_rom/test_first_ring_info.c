/* Read-only first myrs ring-slot parsing against the captured stock slot. */
#include "host_mailbox.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void read_exact(const char *path, unsigned char *out, size_t length)
{
    FILE *file = fopen(path, "rb");
    assert(file);
    assert(fread(out, 1, length, file) == length);
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
    accele160_ring_info_request out = {0, 0, 0};
    assert(argc == 3);
    read_exact(argv[1], setup_bytes, sizeof(setup_bytes));
    read_exact(argv[2], slot, sizeof(slot));
    assert(accele160_parse_set_mem_mbox(setup_bytes, 64, &setup) == 0);
    assert(accele160_parse_first_ring_info(slot, 64, &setup, &out) == 0);
    assert(out.command_id == 1u && out.output_bus_address == 0x0611c400u &&
           out.output_bytes == 1004u);
    memcpy(changed, slot, sizeof(changed));
    changed[3] = 0x10;
    assert(accele160_parse_first_ring_info(changed, 64, &setup, &out) ==
           ACCELE160_MAILBOX_UNSUPPORTED);
    memcpy(changed, slot, sizeof(changed));
    changed[40] = 0xff;
    assert(accele160_parse_first_ring_info(changed, 64, &setup, &out) ==
           ACCELE160_MAILBOX_UNSUPPORTED);
    memcpy(changed, slot, sizeof(changed));
    changed[32] |= 1;
    assert(accele160_parse_first_ring_info(changed, 64, &setup, &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, slot, sizeof(changed));
    put32(changed + 32, setup.command_ring_bus);
    assert(accele160_parse_first_ring_info(changed, 64, &setup, &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, slot, sizeof(changed));
    put32(changed + 32, setup.status_ring_bus);
    assert(accele160_parse_first_ring_info(changed, 64, &setup, &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, slot, sizeof(changed));
    put32(changed + 32, 0x1ffffd00u);
    assert(accele160_parse_first_ring_info(changed, 64, &setup, &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    assert(accele160_parse_first_ring_info(slot, 63, &setup, &out) ==
           ACCELE160_MAILBOX_SHORT);
    assert(accele160_parse_first_ring_info(0, 64, &setup, &out) ==
           ACCELE160_MAILBOX_SHORT);
    assert(accele160_parse_first_ring_info(slot, 64, 0, &out) ==
           ACCELE160_MAILBOX_SHORT);
    assert(accele160_parse_first_ring_info(slot, 64, &setup, 0) ==
           ACCELE160_MAILBOX_SHORT);
    assert(out.command_id == 1u && out.output_bus_address == 0x0611c400u &&
           out.output_bytes == 1004u);
    puts("first ring GET_CTLR_INFO observer parser PASS");
    return 0;
}

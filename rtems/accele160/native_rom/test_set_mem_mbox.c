/* One observed Debian myrs SET_MEM_MBOX request, with fail-closed mutations. */
#include "host_mailbox.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void put32(unsigned char *p, unsigned int value)
{
    p[0] = (unsigned char)value;
    p[1] = (unsigned char)(value >> 8);
    p[2] = (unsigned char)(value >> 16);
    p[3] = (unsigned char)(value >> 24);
}

static void rejects(const unsigned char *source, unsigned int offset,
                    unsigned char value, unsigned int reason)
{
    unsigned char changed[64];
    accele160_mem_mbox_request out = {0xfeedu, 0xbeefu, 0xfaceu, 0xcafeu};
    memcpy(changed, source, sizeof(changed));
    changed[offset] = value;
    assert(accele160_parse_set_mem_mbox(changed, sizeof(changed), &out) == reason);
    assert(out.command_id == 0xfeedu && out.command_ring_bus == 0xbeefu &&
           out.status_ring_bus == 0xfaceu && out.health_bus == 0xcafeu);
}

int main(int argc, char **argv)
{
    FILE *input;
    unsigned char packet[64], changed[64];
    accele160_mem_mbox_request out = {0, 0, 0, 0};
    assert(argc == 2);
    input = fopen(argv[1], "rb");
    assert(input);
    assert(fread(packet, 1, sizeof(packet), input) == sizeof(packet));
    assert(fgetc(input) == EOF);
    assert(fclose(input) == 0);
    assert(accele160_parse_set_mem_mbox(packet, sizeof(packet), &out) == 0);
    assert(out.command_id == 1u && out.command_ring_bus == 0x06340000u &&
           out.status_ring_bus == 0x06199000u && out.health_bus == 0x0619a000u);
    rejects(packet, 0, 2, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(packet, 3, 0x10, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(packet, 4, 0x21, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(packet, 21, 0, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(packet, 22, 0, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(packet, 23, 1, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(packet, 48, 1, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(packet, 28, 1, ACCELE160_MAILBOX_ADDRESS);
    rejects(packet, 32, 1, ACCELE160_MAILBOX_ADDRESS);
    rejects(packet, 36, 1, ACCELE160_MAILBOX_ADDRESS);
    rejects(packet, 40, 1, ACCELE160_MAILBOX_ADDRESS);
    rejects(packet, 44, 1, ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, packet, sizeof(changed));
    put32(changed + 40, out.command_ring_bus);
    assert(accele160_parse_set_mem_mbox(changed, sizeof(changed), &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, packet, sizeof(changed));
    put32(changed + 24, out.status_ring_bus);
    assert(accele160_parse_set_mem_mbox(changed, sizeof(changed), &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, packet, sizeof(changed));
    put32(changed + 32, out.status_ring_bus - 0x1000u);
    assert(accele160_parse_set_mem_mbox(changed, sizeof(changed), &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    memcpy(changed, packet, sizeof(changed));
    put32(changed + 24, 0x1ffff000u);
    assert(accele160_parse_set_mem_mbox(changed, sizeof(changed), &out) == 0);
    put32(changed + 32, 0x1ffff000u);
    assert(accele160_parse_set_mem_mbox(changed, sizeof(changed), &out) ==
           ACCELE160_MAILBOX_ADDRESS);
    assert(accele160_parse_set_mem_mbox(packet, 63, &out) ==
           ACCELE160_MAILBOX_SHORT);
    assert(accele160_parse_set_mem_mbox(0, 64, &out) ==
           ACCELE160_MAILBOX_SHORT);
    assert(accele160_parse_set_mem_mbox(packet, 64, 0) ==
           ACCELE160_MAILBOX_SHORT);
    puts("SET_MEM_MBOX parser PASS");
    return 0;
}

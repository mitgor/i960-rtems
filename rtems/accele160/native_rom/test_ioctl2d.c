#include "host_mailbox.h"
#include "controller_info.h"
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

int main(int argc, char **argv)
{
    unsigned char request[64], expected[512], descriptor[512];
    unsigned char actual[512], changed[64];
    accele160_controller_info_request parsed = {0, 0, 0};
    FILE *stock;
    assert(argc == 4);
    read_exact(argv[1], request, sizeof(request));
    read_exact(argv[2], expected, sizeof(expected));
    stock = fopen(argv[3], "rb");
    assert(stock);
    assert(fseek(stock, 0xe0000L, SEEK_SET) == 0);
    assert(fread(descriptor, 1, sizeof(descriptor), stock) == sizeof(descriptor));
    assert(fclose(stock) == 0);
    assert(memcmp(descriptor, expected, sizeof(descriptor)) == 0);
    assert(accele160_parse_ioctl2d(request, sizeof(request), &parsed) == 0);
    assert(parsed.command_id == 0x7f &&
           parsed.output_bus_address == 0x9f3e0 &&
           parsed.output_bytes == 512);
    memset(actual, 0xa5, sizeof(actual));
    assert(accele160_compose_ioctl2d(actual, sizeof(actual),
                                    descriptor, sizeof(descriptor)) == 0);
    assert(memcmp(actual, expected, sizeof(actual)) == 0);
    descriptor[0x60] ^= 0x5a;
    assert(accele160_compose_ioctl2d(actual, sizeof(actual),
                                    descriptor, sizeof(descriptor)) == 0);
    assert(actual[0x60] == descriptor[0x60]);
    descriptor[0x60] ^= 0x5a;
    memcpy(changed, request, sizeof(changed));
    changed[40] = 0xff;
    assert(accele160_parse_ioctl2d(changed, sizeof(changed), &parsed) ==
           ACCELE160_MAILBOX_UNSUPPORTED);
    memcpy(changed, request, sizeof(changed));
    changed[32] |= 1;
    assert(accele160_parse_ioctl2d(changed, sizeof(changed), &parsed) ==
           ACCELE160_MAILBOX_ADDRESS);
    memset(actual, 0xa5, sizeof(actual));
    assert(accele160_compose_ioctl2d(actual, 511,
                                    descriptor, sizeof(descriptor)) == 1);
    assert(actual[0] == 0xa5);
    descriptor[0] = 0;
    assert(accele160_compose_ioctl2d(actual, sizeof(actual),
                                    descriptor, sizeof(descriptor)) == 2);
    assert(actual[0] == 0xa5);
    puts("IOCTL 0x2d stock-replay parser/composer PASS");
    return 0;
}

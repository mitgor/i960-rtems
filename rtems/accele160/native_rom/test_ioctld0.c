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
    unsigned char request[64], expected[128], actual[128], changed[64];
    accele160_controller_info_request parsed = {0, 0, 0};
    assert(argc == 3);
    read_exact(argv[1], request, sizeof(request));
    read_exact(argv[2], expected, sizeof(expected));
    assert(accele160_parse_ioctld0(request, sizeof(request), &parsed) == 0);
    assert(parsed.command_id == 0x7f &&
           parsed.output_bus_address == 0x9f3e0 &&
           parsed.output_bytes == 128);
    memset(actual, 0xa5, sizeof(actual));
    assert(accele160_compose_ioctld0(actual, sizeof(actual)) == 0);
    assert(memcmp(actual, expected, sizeof(actual)) == 0);
    memcpy(changed, request, sizeof(changed));
    changed[40] = 127;
    assert(accele160_parse_ioctld0(changed, sizeof(changed), &parsed) ==
           ACCELE160_MAILBOX_UNSUPPORTED);
    memcpy(changed, request, sizeof(changed));
    changed[32] |= 1;
    assert(accele160_parse_ioctld0(changed, sizeof(changed), &parsed) ==
           ACCELE160_MAILBOX_ADDRESS);
    memset(actual, 0xa5, sizeof(actual));
    assert(accele160_compose_ioctld0(actual, 127) == 1);
    assert(actual[0] == 0xa5);
    puts("IOCTL 0xd0 stock-replay parser/composer PASS");
    return 0;
}

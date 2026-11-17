/* Check the proposed first ring reply against stock model DMA and status. */
#include "controller_info.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
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
    unsigned char *flash;
    unsigned char expected[ACCELE160_RING_CONTROLLER_INFO_BYTES];
    unsigned char actual[ACCELE160_RING_CONTROLLER_INFO_BYTES];
    unsigned char status[ACCELE160_RING_STATUS_BYTES];
    unsigned char expected_status[ACCELE160_RING_STATUS_BYTES];
    assert(argc == 4);
    flash = malloc(0x100000u);
    assert(flash);
    read_exact(argv[1], flash, 0x100000u);
    read_exact(argv[2], expected, sizeof(expected));
    read_exact(argv[3], expected_status, sizeof(expected_status));
    memset(actual, 0xa5, sizeof(actual));
    assert(accele160_compose_first_ring_info(
        actual, sizeof(actual), flash + 0xe0000u, 0x390u,
        flash + 0xf0040u, 16u) == 0);
    assert(memcmp(actual, expected, sizeof(actual)) == 0);
    assert(accele160_compose_first_ring_status(status, sizeof(status)) == 0);
    assert(memcmp(status, expected_status, sizeof(status)) == 0);
    actual[0] = 0xa5;
    assert(accele160_compose_first_ring_info(
        actual, sizeof(actual) - 1u, flash + 0xe0000u, 0x390u,
        flash + 0xf0040u, 16u) == 1);
    assert(actual[0] == 0xa5);
    flash[0xe0000u] = 0;
    assert(accele160_compose_first_ring_info(
        actual, sizeof(actual), flash + 0xe0000u, 0x390u,
        flash + 0xf0040u, 16u) == 2);
    assert(actual[0] == 0xa5);
    free(flash);
    puts("first ring reply composer matches stock model fixture");
    return 0;
}

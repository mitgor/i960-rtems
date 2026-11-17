/* Compare the exact target-0 pdev composer with the stock DMA1 source. */
#include "controller_info.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void read_exact(const char *path, unsigned char *bytes, size_t length)
{
    FILE *file = fopen(path, "rb");
    assert(file);
    assert(fread(bytes, 1, length, file) == length);
    assert(fgetc(file) == EOF);
    assert(fclose(file) == 0);
}

int main(int argc, char **argv)
{
    unsigned char *flash;
    unsigned char expected[512], actual[512];
    assert(argc == 3);
    flash = malloc(0x100000u);
    assert(flash);
    read_exact(argv[1], flash, 0x100000u);
    read_exact(argv[2], expected, sizeof(expected));
    memset(actual, 0xa5, sizeof(actual));
    assert(accele160_compose_first_ring_pdev(
        actual, sizeof(actual), flash + 0xf0040u, 16u) == 0);
    assert(memcmp(actual, expected, sizeof(actual)) == 0);
    actual[0] = 0xa5;
    assert(accele160_compose_first_ring_pdev(
        actual, sizeof(actual) - 1u, flash + 0xf0040u, 16u) == 1);
    assert(actual[0] == 0xa5);
    flash[0xf0040u] = 'X';
    assert(accele160_compose_first_ring_pdev(
        actual, sizeof(actual), flash + 0xf0040u, 16u) == 2);
    assert(actual[0] == 0xa5);
    free(flash);
    puts("first target-0 pdev reply composer matches stock source");
    return 0;
}

/* Prove the existing ROM 0x11 composer matches the independent ring source. */
#include "controller_info.h"
#include <assert.h>
#include <stdio.h>
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
    unsigned char ring_source[128], legacy_reply[128], composed[128];
    assert(argc == 3);
    read_exact(argv[1], ring_source, sizeof(ring_source));
    read_exact(argv[2], legacy_reply, sizeof(legacy_reply));
    assert(memcmp(ring_source, legacy_reply, sizeof(ring_source)) == 0);
    memset(composed, 0xa5, sizeof(composed));
    assert(accele160_compose_ioctl11(composed, sizeof(composed)) == 0);
    assert(memcmp(composed, ring_source, sizeof(composed)) == 0);
    composed[0] = 0xa5;
    assert(accele160_compose_ioctl11(composed, sizeof(composed) - 1u) == 1);
    assert(composed[0] == 0xa5);
    puts("first ring health output draft matches two independent stock captures");
    return 0;
}

#include "controller_info.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void read_exact(const char *path, unsigned char *out, size_t length)
{
    FILE *file = fopen(path, "rb");
    assert(file);
    assert(fread(out, 1, length, file) == length);
    assert(fclose(file) == 0);
}

int main(int argc, char **argv)
{
    unsigned char descriptor[0x390], product[16], expected[512], actual[512];
    unsigned char changed[0x390];
    assert(argc == 4);
    {
        FILE *stock = fopen(argv[1], "rb");
        assert(stock);
        assert(fseek(stock, 0xe0000, SEEK_SET) == 0);
        assert(fread(descriptor, 1, sizeof(descriptor), stock) ==
               sizeof(descriptor));
        assert(fseek(stock, 0xf0040, SEEK_SET) == 0);
        assert(fread(product, 1, sizeof(product), stock) == sizeof(product));
        assert(fclose(stock) == 0);
    }
    read_exact(argv[2], expected, sizeof(expected));
    memset(actual, 0xa5, sizeof(actual));
    assert(accele160_compose_controller_info(actual, sizeof(actual),
               descriptor, sizeof(descriptor), product, sizeof(product)) == 0);
    assert(memcmp(actual, expected, sizeof(actual)) == 0);
    {
        unsigned char other_descriptor[0x390], other_product[16];
        FILE *other = fopen(argv[3], "rb");
        assert(other);
        assert(fseek(other, 0xe0000, SEEK_SET) == 0);
        assert(fread(other_descriptor, 1, sizeof(other_descriptor), other) ==
               sizeof(other_descriptor));
        assert(fseek(other, 0xf0040, SEEK_SET) == 0);
        assert(fread(other_product, 1, sizeof(other_product), other) ==
               sizeof(other_product));
        assert(fclose(other) == 0);
        assert(accele160_compose_controller_info(actual, sizeof(actual),
                   other_descriptor, sizeof(other_descriptor),
                   other_product, sizeof(other_product)) == 0);
        assert(memcmp(actual + 0x60, other_descriptor + 0x384, 11) == 0);
        memset(actual + 0x60, 0, 11);
        memset(expected + 0x60, 0, 11);
        assert(memcmp(actual, expected, sizeof(actual)) == 0);
    }
    memcpy(changed, descriptor, sizeof(changed));
    changed[0x384] = '9';
    assert(accele160_compose_controller_info(actual, sizeof(actual), changed,
               sizeof(changed), product, sizeof(product)) == 0);
    assert(actual[0x60] == '9' && actual[0x61] == descriptor[0x385]);
    memset(actual, 0xa5, sizeof(actual));
    changed[0x384] = 'X';
    assert(accele160_compose_controller_info(actual, sizeof(actual), changed,
               sizeof(changed), product, sizeof(product)) == 4);
    assert(actual[0] == 0xa5);
    assert(accele160_compose_controller_info(actual, 511, descriptor,
               sizeof(descriptor), product, sizeof(product)) == 1);
    assert(actual[0] == 0xa5);
    puts("GET_CTLR_INFO stock-replay composer PASS");
    return 0;
}

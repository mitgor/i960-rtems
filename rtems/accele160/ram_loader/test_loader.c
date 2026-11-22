#include "loader.h"
#include "../native_rom/updater.h"
#include <assert.h>

static unsigned char image[ACCELE160_RAM_MAX_BYTES];
static unsigned char page[ACCELE160_RAM_CHUNK_BYTES];
static const unsigned char page_sha256[32] = {
    0xc8,0xf5,0xd0,0x34,0x1d,0x54,0xd9,0x51,
    0xa7,0x1b,0x13,0x6e,0x6e,0x2a,0xfc,0xb1,
    0x4d,0x11,0xed,0x84,0x89,0xa7,0xae,0x12,
    0x6a,0x8f,0xee,0x0d,0xf6,0xec,0xf1,0x93
};

int main(void)
{
    accele160_ram_loader loader = {0};
    unsigned int i, address = 0, digest;
    for (i = 0; i < sizeof(page); ++i) page[i] = (unsigned char)i;
    digest = accele160_fnv32(page, sizeof(page));
    assert(accele160_ram_begin(&loader, image, 0, 0, page_sha256) ==
           ACCELE160_RAM_ARGUMENT);
    assert(accele160_ram_begin(&loader, image,
           ACCELE160_RAM_MAX_BYTES + ACCELE160_RAM_CHUNK_BYTES, 0,
           page_sha256) == ACCELE160_RAM_ARGUMENT);
    assert(accele160_ram_begin(&loader, image, sizeof(page),
           sizeof(page), page_sha256) == ACCELE160_RAM_ARGUMENT);
    assert(accele160_ram_begin(&loader, image, sizeof(page), 2,
           page_sha256) == ACCELE160_RAM_ARGUMENT);
    assert(accele160_ram_begin(&loader, image, sizeof(page), 0,
           page_sha256) == ACCELE160_RAM_OK);
    assert(accele160_ram_begin(&loader, image, sizeof(page), 0,
           page_sha256) == ACCELE160_RAM_STATE);
    assert(accele160_ram_entry(&loader, &address) == ACCELE160_RAM_STATE);
    assert(accele160_ram_chunk(&loader, 1, page, sizeof(page), digest) ==
           ACCELE160_RAM_ORDER);
    assert(accele160_ram_chunk(&loader, 0, page, sizeof(page), digest ^ 1u) ==
           ACCELE160_RAM_CHUNK_HASH);
    assert(accele160_ram_seal(&loader) == ACCELE160_RAM_STATE);
    assert(accele160_ram_chunk(&loader, 0, page, sizeof(page), digest) ==
           ACCELE160_RAM_OK);
    assert(accele160_ram_chunk(&loader, 0, page, sizeof(page), digest) ==
           ACCELE160_RAM_ORDER);
    assert(accele160_ram_seal(&loader) == ACCELE160_RAM_OK);
    assert(accele160_ram_abort(&loader) == ACCELE160_RAM_OK);
    image[0] = 0;
    assert(accele160_ram_begin(&loader, image, sizeof(page), 0,
           page_sha256) == ACCELE160_RAM_OK);
    page[0] ^= 1u;
    digest = accele160_fnv32(page, sizeof(page));
    assert(accele160_ram_chunk(&loader, 0, page, sizeof(page), digest) ==
           ACCELE160_RAM_OK);
    assert(accele160_ram_seal(&loader) == ACCELE160_RAM_IMAGE_HASH);
    assert(accele160_ram_entry(&loader, &address) == ACCELE160_RAM_STATE);
    assert(accele160_ram_abort(&loader) == ACCELE160_RAM_OK);
    page[0] ^= 1u;
    digest = accele160_fnv32(page, sizeof(page));
    assert(accele160_ram_begin(&loader, image, sizeof(page), 0,
           page_sha256) == ACCELE160_RAM_OK);
    assert(accele160_ram_chunk(&loader, 0, page, sizeof(page), digest) ==
           ACCELE160_RAM_OK);
    assert(accele160_ram_seal(&loader) == ACCELE160_RAM_OK);
    assert(accele160_ram_entry(&loader, &address) == ACCELE160_RAM_OK);
    assert(address == ACCELE160_RAM_LOAD_ADDRESS);
    assert(accele160_ram_abort(&loader) == ACCELE160_RAM_STATE);
    return 0;
}

#include "loader.h"
#include "../native_rom/updater.h"

int accele160_ram_begin(accele160_ram_loader *loader, unsigned char *buffer,
    unsigned int image_bytes, unsigned int entry_offset,
    const unsigned char expected_sha256[32])
{
    unsigned int i;
    if (!loader || !buffer || !expected_sha256 ||
        image_bytes == 0u || image_bytes > ACCELE160_RAM_MAX_BYTES ||
        (image_bytes & (ACCELE160_RAM_CHUNK_BYTES - 1u)) != 0u ||
        entry_offset >= image_bytes || (entry_offset & 3u) != 0u)
        return ACCELE160_RAM_ARGUMENT;
    if (loader->state != 0u) return ACCELE160_RAM_STATE;
    loader->buffer = buffer;
    loader->image_bytes = image_bytes;
    loader->entry_offset = entry_offset;
    loader->next_chunk = 0u;
    for (i = 0; i < 32u; ++i) loader->expected_sha256[i] = expected_sha256[i];
    loader->state = 1u;
    return ACCELE160_RAM_OK;
}

int accele160_ram_chunk(accele160_ram_loader *loader, unsigned int index,
    const unsigned char *bytes, unsigned int length, unsigned int fnv32)
{
    unsigned int i, offset;
    if (!loader || !bytes || length != ACCELE160_RAM_CHUNK_BYTES)
        return ACCELE160_RAM_ARGUMENT;
    if (loader->state != 1u) return ACCELE160_RAM_STATE;
    if (index != loader->next_chunk ||
        index >= loader->image_bytes / ACCELE160_RAM_CHUNK_BYTES)
        return ACCELE160_RAM_ORDER;
    if (accele160_fnv32(bytes, length) != fnv32)
        return ACCELE160_RAM_CHUNK_HASH;
    offset = index * ACCELE160_RAM_CHUNK_BYTES;
    for (i = 0; i < length; ++i) loader->buffer[offset + i] = bytes[i];
    ++loader->next_chunk;
    return ACCELE160_RAM_OK;
}

int accele160_ram_seal(accele160_ram_loader *loader)
{
    unsigned char actual[32];
    unsigned int i, mismatch = 0u;
    if (!loader) return ACCELE160_RAM_ARGUMENT;
    if (loader->state != 1u ||
        loader->next_chunk != loader->image_bytes / ACCELE160_RAM_CHUNK_BYTES)
        return ACCELE160_RAM_STATE;
    accele160_sha256(loader->buffer, loader->image_bytes, actual);
    for (i = 0; i < 32u; ++i) mismatch |= actual[i] ^ loader->expected_sha256[i];
    if (mismatch) return ACCELE160_RAM_IMAGE_HASH;
    loader->state = 2u;
    return ACCELE160_RAM_OK;
}

int accele160_ram_entry(accele160_ram_loader *loader, unsigned int *address)
{
    if (!loader || !address) return ACCELE160_RAM_ARGUMENT;
    if (loader->state != 2u) return ACCELE160_RAM_STATE;
    *address = ACCELE160_RAM_LOAD_ADDRESS + loader->entry_offset;
    loader->state = 3u;
    return ACCELE160_RAM_OK;
}

int accele160_ram_abort(accele160_ram_loader *loader)
{
    if (!loader) return ACCELE160_RAM_ARGUMENT;
    if (loader->state == 3u) return ACCELE160_RAM_STATE;
    loader->state = 0u;
    loader->buffer = 0;
    loader->image_bytes = 0u;
    loader->entry_offset = 0u;
    loader->next_chunk = 0u;
    return ACCELE160_RAM_OK;
}

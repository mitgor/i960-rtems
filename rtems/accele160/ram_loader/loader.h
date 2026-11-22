#ifndef ACCELE160_RAM_LOADER_H
#define ACCELE160_RAM_LOADER_H

#define ACCELE160_RAM_LOAD_ADDRESS 0xc0710000u
#define ACCELE160_RAM_MAX_BYTES 0x000e0000u
#define ACCELE160_RAM_CHUNK_BYTES 4096u

enum accele160_ram_result {
    ACCELE160_RAM_OK = 0,
    ACCELE160_RAM_ARGUMENT = 1,
    ACCELE160_RAM_STATE = 2,
    ACCELE160_RAM_ORDER = 3,
    ACCELE160_RAM_CHUNK_HASH = 4,
    ACCELE160_RAM_IMAGE_HASH = 5
};

typedef struct {
    unsigned char *buffer;
    unsigned int image_bytes;
    unsigned int entry_offset;
    unsigned int next_chunk;
    unsigned int state; /* 0 idle, 1 receiving, 2 sealed, 3 running */
    unsigned char expected_sha256[32];
} accele160_ram_loader;

int accele160_ram_begin(accele160_ram_loader *loader, unsigned char *buffer,
    unsigned int image_bytes, unsigned int entry_offset,
    const unsigned char expected_sha256[32]);
int accele160_ram_chunk(accele160_ram_loader *loader, unsigned int index,
    const unsigned char *bytes, unsigned int length, unsigned int fnv32);
int accele160_ram_seal(accele160_ram_loader *loader);
int accele160_ram_entry(accele160_ram_loader *loader, unsigned int *address);
int accele160_ram_abort(accele160_ram_loader *loader);

#endif

#ifndef ACCELE160_UPDATER_H
#define ACCELE160_UPDATER_H

/* Image admission is independent of the PCI transport and flash hardware.
 * The caller owns a 1 MiB DRAM buffer and supplies the current flash image. */
#define ACCELE160_UPDATE_IMAGE_BYTES 0x100000u
#define ACCELE160_UPDATE_CHUNK_BYTES 4096u
#define ACCELE160_UPDATE_CHUNKS 256u
#define ACCELE160_UPDATE_MUTABLE_FIRST 0x40000u
#define ACCELE160_UPDATE_MUTABLE_END 0xc0000u

enum accele160_update_result {
    ACCELE160_UPDATE_OK = 0,
    ACCELE160_UPDATE_ARGUMENT = 1,
    ACCELE160_UPDATE_STATE = 2,
    ACCELE160_UPDATE_SEQUENCE = 3,
    ACCELE160_UPDATE_CHUNK_HASH = 4,
    ACCELE160_UPDATE_IMAGE_HASH = 5,
    ACCELE160_UPDATE_PROTECTED = 6,
    ACCELE160_UPDATE_BASE_HASH = 7,
    ACCELE160_UPDATE_NO_WRITER = 8,
    ACCELE160_UPDATE_WRITE_FAILED = 9,
    ACCELE160_UPDATE_VERIFY_FAILED = 10
};

typedef struct {
    unsigned char *buffer;
    const volatile unsigned char *flash;
    unsigned char base_sha256[32];
    unsigned char target_sha256[32];
    unsigned int next_chunk;
    unsigned int state; /* 0 idle, 1 receiving, 2 sealed, 3 applied, 4 failed */
} accele160_updater;

typedef int (*accele160_update_write_block)(
    unsigned int flash_offset, const unsigned char *bytes,
    unsigned int length, void *context);

void accele160_sha256(const volatile unsigned char *data, unsigned int length,
                      unsigned char out[32]);
unsigned int accele160_fnv32(const unsigned char *data, unsigned int length);
int accele160_update_begin(accele160_updater *u, unsigned char *buffer,
    const volatile unsigned char *flash, const unsigned char base_sha256[32],
    const unsigned char target_sha256[32]);
int accele160_update_chunk(accele160_updater *u, unsigned int index,
    const unsigned char *bytes, unsigned int length, unsigned int fnv32);
int accele160_update_seal(accele160_updater *u);
/* Abandon a RAM-only session. A failed/partial flash write (state 4) cannot
 * be cleared by software; that condition needs external recovery. */
int accele160_update_abort(accele160_updater *u);
/* Only a separately qualified flash backend may call apply. It must leave
 * the chip in read-array mode; apply independently verifies every changed
 * 64 KiB block after the callback. No writer is linked into the ROM here. */
int accele160_update_apply(accele160_updater *u,
    accele160_update_write_block write_block, void *context);

#endif

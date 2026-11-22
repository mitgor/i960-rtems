#ifndef ACCELE160_UPDATER_SERVICE_H
#define ACCELE160_UPDATER_SERVICE_H

#include "updater.h"

/* Two separate host-visible odd pages: control at c0801000, 4 KiB data at
 * c0803000. The host selects each through PIATVR; firmware addresses are
 * local. The image buffer occupies c0900000..c09fffff. */
#define ACCELE160_UPDATE_CONTROL_ADDRESS 0xc0801000u
#define ACCELE160_UPDATE_DATA_ADDRESS 0xc0803000u
#define ACCELE160_UPDATE_BUFFER_ADDRESS 0xc0900000u
#define ACCELE160_UPDATE_FLASH_ADDRESS 0xfef00000u
#define ACCELE160_UPDATE_MAGIC 0x31445055u /* UPD1 */
#define ACCELE160_UPDATE_VERSION 2u
#define ACCELE160_UPDATE_CAP_WRITER 1u

#define ACCELE160_UPDATE_CMD_BEGIN 1u
#define ACCELE160_UPDATE_CMD_CHUNK 2u
#define ACCELE160_UPDATE_CMD_SEAL 3u
#define ACCELE160_UPDATE_CMD_ABORT 4u
#define ACCELE160_UPDATE_CMD_APPLY 5u
#define ACCELE160_UPDATE_BASE_SHA_OFFSET 128u
#define ACCELE160_UPDATE_TARGET_SHA_OFFSET 160u

typedef struct {
    accele160_updater updater;
    unsigned int acknowledged;
    unsigned char chunk[ACCELE160_UPDATE_CHUNK_BYTES];
} accele160_update_service;

/* Control is a 4 KiB little-endian page. Words 0..10 are magic, sequence,
 * acknowledged, command, chunk index, length, FNV32, result, state,
 * next chunk, version, capabilities (word 11). Bit 0 advertises a linked
 * writer. Base SHA-256 occupies bytes 128..159; target SHA-256
 * occupies bytes 160..191. The host publishes sequence last; firmware
 * publishes acknowledged last. */
void accele160_update_service_init(accele160_update_service *s,
                                   volatile unsigned int *control);
void accele160_update_service_poll(accele160_update_service *s,
    volatile unsigned int *control, const volatile unsigned char *data,
    unsigned char *buffer, const volatile unsigned char *flash,
    accele160_update_write_block write_block, void *write_context);

#endif

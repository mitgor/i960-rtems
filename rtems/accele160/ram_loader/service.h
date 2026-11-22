#ifndef ACCELE160_RAM_SERVICE_H
#define ACCELE160_RAM_SERVICE_H

#include "loader.h"

#define ACCELE160_RAM_CONTROL_ADDRESS 0xc0805000u
#define ACCELE160_RAM_DATA_ADDRESS 0xc0807000u
#define ACCELE160_RAM_MAGIC 0x314d4152u /* RAM1 */
#define ACCELE160_RAM_VERSION 1u
#define ACCELE160_RAM_CMD_BEGIN 1u
#define ACCELE160_RAM_CMD_CHUNK 2u
#define ACCELE160_RAM_CMD_SEAL 3u
#define ACCELE160_RAM_CMD_RUN 4u
#define ACCELE160_RAM_CMD_ABORT 5u
#define ACCELE160_RAM_SHA_OFFSET 128u

typedef unsigned int (*accele160_ram_run)(unsigned int entry,
    volatile unsigned int *control, void *context);

typedef struct {
    accele160_ram_loader loader;
    unsigned int acknowledged;
    unsigned char chunk[ACCELE160_RAM_CHUNK_BYTES];
} accele160_ram_service;

/* Control words: magic, seq, ack, command, chunk index, image/chunk length,
 * FNV, result, state, next chunk, version, entry offset, run result.
 * Expected SHA-256 occupies bytes 128..159. */
void accele160_ram_service_init(accele160_ram_service *service,
    volatile unsigned int *control);
void accele160_ram_service_poll(accele160_ram_service *service,
    volatile unsigned int *control, const volatile unsigned char *data,
    unsigned char *image, accele160_ram_run run, void *context);

#endif

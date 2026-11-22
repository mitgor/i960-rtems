#include "service.h"
#include "../native_rom/updater.h"
#include <assert.h>

static unsigned int control[1024], called;
static unsigned char data[ACCELE160_RAM_CHUNK_BYTES];
static unsigned char image[ACCELE160_RAM_MAX_BYTES];
static const unsigned char digest[32] = {
    0xc8,0xf5,0xd0,0x34,0x1d,0x54,0xd9,0x51,
    0xa7,0x1b,0x13,0x6e,0x6e,0x2a,0xfc,0xb1,
    0x4d,0x11,0xed,0x84,0x89,0xa7,0xae,0x12,
    0x6a,0x8f,0xee,0x0d,0xf6,0xec,0xf1,0x93
};

static unsigned int run(unsigned int entry, volatile unsigned int *words,
                        void *context)
{
    (void)context;
    assert(entry == ACCELE160_RAM_LOAD_ADDRESS);
    assert(words[8] == 1u || words[8] == 2u);
    ++called;
    return 0x9601abcd;
}

static void submit(accele160_ram_service *service, unsigned int seq,
                   unsigned int command)
{
    control[3] = command;
    control[1] = seq;
    accele160_ram_service_poll(service, control, data, image, run, 0);
    assert(control[2] == seq);
}

int main(void)
{
    accele160_ram_service service;
    unsigned int i;
    for (i = 0; i < sizeof(data); ++i) data[i] = (unsigned char)i;
    accele160_ram_service_init(&service, control);
    assert(control[0] == ACCELE160_RAM_MAGIC &&
           control[10] == ACCELE160_RAM_VERSION);
    submit(&service, 1, ACCELE160_RAM_CMD_RUN);
    assert(control[7] == ACCELE160_RAM_STATE && called == 0);
    for (i = 0; i < 32u; ++i)
        ((unsigned char *)control)[ACCELE160_RAM_SHA_OFFSET+i] = digest[i];
    control[5] = sizeof(data);
    control[11] = 0;
    submit(&service, 2, ACCELE160_RAM_CMD_BEGIN);
    assert(control[7] == ACCELE160_RAM_OK && control[8] == 1);
    control[4] = 0;
    control[5] = sizeof(data);
    control[6] = accele160_fnv32(data, sizeof(data)) ^ 1u;
    submit(&service, 3, ACCELE160_RAM_CMD_CHUNK);
    assert(control[7] == ACCELE160_RAM_CHUNK_HASH && control[9] == 0);
    control[6] ^= 1u;
    submit(&service, 4, ACCELE160_RAM_CMD_CHUNK);
    assert(control[7] == ACCELE160_RAM_OK && control[9] == 1);
    submit(&service, 5, ACCELE160_RAM_CMD_SEAL);
    assert(control[7] == ACCELE160_RAM_OK && control[8] == 2);
    submit(&service, 6, ACCELE160_RAM_CMD_RUN);
    assert(control[7] == ACCELE160_RAM_OK && control[8] == 3);
    assert(control[12] == 0x9601abcd && called == 1);
    submit(&service, 7, ACCELE160_RAM_CMD_ABORT);
    assert(control[7] == ACCELE160_RAM_STATE && control[8] == 3);
    return 0;
}

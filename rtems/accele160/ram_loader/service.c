#include "service.h"

void accele160_ram_service_init(accele160_ram_service *service,
    volatile unsigned int *control)
{
    unsigned int i;
    for (i = 0; i < sizeof(*service); ++i) ((unsigned char *)service)[i] = 0u;
    for (i = 0; i < 40u; ++i) control[i] = 0u;
    control[0] = ACCELE160_RAM_MAGIC;
    control[10] = ACCELE160_RAM_VERSION;
}

void accele160_ram_service_poll(accele160_ram_service *service,
    volatile unsigned int *control, const volatile unsigned char *data,
    unsigned char *image, accele160_ram_run run, void *context)
{
    unsigned int seq, cmd, index, length, digest, result, i, entry;
    unsigned char expected[32];
    if (!service || !control || !data || !image) return;
    if (control[0] != ACCELE160_RAM_MAGIC) return;
    seq = control[1];
    if (seq == service->acknowledged) return;
    if (seq == 0u || seq != service->acknowledged + 1u) {
        control[7] = ACCELE160_RAM_ORDER;
        return;
    }
    cmd = control[3];
    index = control[4];
    length = control[5];
    digest = control[6];
    if (cmd == ACCELE160_RAM_CMD_BEGIN) {
        for (i = 0; i < 32u; ++i)
            expected[i] = ((volatile unsigned char *)control)[ACCELE160_RAM_SHA_OFFSET+i];
        result = accele160_ram_begin(&service->loader, image, length,
                                    control[11], expected);
    } else if (cmd == ACCELE160_RAM_CMD_CHUNK) {
        if (length != ACCELE160_RAM_CHUNK_BYTES) result = ACCELE160_RAM_ARGUMENT;
        else {
            for (i = 0; i < ACCELE160_RAM_CHUNK_BYTES; ++i)
                service->chunk[i] = data[i];
            result = accele160_ram_chunk(&service->loader, index, service->chunk,
                                        length, digest);
        }
    } else if (cmd == ACCELE160_RAM_CMD_SEAL) {
        result = accele160_ram_seal(&service->loader);
    } else if (cmd == ACCELE160_RAM_CMD_RUN) {
        if (!run) result = ACCELE160_RAM_ARGUMENT;
        else {
            result = accele160_ram_entry(&service->loader, &entry);
            if (result == ACCELE160_RAM_OK) control[12] = run(entry, control, context);
        }
    } else if (cmd == ACCELE160_RAM_CMD_ABORT) {
        result = accele160_ram_abort(&service->loader);
    } else result = ACCELE160_RAM_ARGUMENT;
    control[7] = result;
    control[8] = service->loader.state;
    control[9] = service->loader.next_chunk;
    service->acknowledged = seq;
    control[2] = seq;
}

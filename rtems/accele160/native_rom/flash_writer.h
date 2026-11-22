#ifndef ACCELE160_FLASH_WRITER_H
#define ACCELE160_FLASH_WRITER_H

/* Intel 28F008S3 byte-wide command interface. The caller supplies an
 * independently verified 64 KiB image and owns the flash aperture. */
typedef struct {
    unsigned char (*read8)(unsigned int offset, void *context);
    void (*write8)(unsigned int offset, unsigned char value, void *context);
    void *context;
    unsigned int max_status_polls;
    unsigned int last_status;
    unsigned int failed_offset;
} accele160_s3_io;

enum accele160_s3_result {
    ACCELE160_S3_OK = 0,
    ACCELE160_S3_ARGUMENT = 1,
    ACCELE160_S3_IDENTITY = 2,
    ACCELE160_S3_LOCKED = 3,
    ACCELE160_S3_TIMEOUT = 4,
    ACCELE160_S3_STATUS = 5,
    ACCELE160_S3_ERASE_VERIFY = 6,
    ACCELE160_S3_PROGRAM_VERIFY = 7,
    ACCELE160_S3_GATE = 8
};

/* Nonprogramming ID/lock command probe. Always restores read-array mode. */
int accele160_s3_probe(accele160_s3_io *io);
/* Only offsets 0x40000..0xb0000 and exact 64 KiB lengths are accepted.
 * A failure may leave a block partially erased/programmed; never retry in
 * the same session. */
int accele160_s3_write_block(unsigned int offset,
    const unsigned char *bytes, unsigned int length, void *context);

#endif

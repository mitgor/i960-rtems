#include "flash_writer.h"

#define S3_BLOCK 0x10000u
#define S3_FIRST 0x40000u
#define S3_END 0xc0000u
#define S3_READY 0x80u
#define S3_ERRORS 0x3au /* erase, program, VPP, protection */

static void array_mode(accele160_s3_io *io, unsigned int address)
{
    io->write8(address, 0xffu, io->context);
}

static int ready(accele160_s3_io *io, unsigned int address)
{
    unsigned int poll, status = 0u;
    for (poll = 0; poll < io->max_status_polls; ++poll) {
        status = io->read8(address, io->context);
        if (status & S3_READY) {
            io->last_status = status;
            if (status & S3_ERRORS) return ACCELE160_S3_STATUS;
            return ACCELE160_S3_OK;
        }
    }
    io->last_status = status;
    return ACCELE160_S3_TIMEOUT;
}

int accele160_s3_probe(accele160_s3_io *io)
{
    unsigned int block;
    int result = ACCELE160_S3_OK;
    if (!io || !io->read8 || !io->write8 || !io->max_status_polls)
        return ACCELE160_S3_ARGUMENT;
    io->write8(0u, 0x90u, io->context);
    if (io->read8(0u, io->context) != 0x89u ||
        io->read8(1u, io->context) != 0xa6u)
        result = ACCELE160_S3_IDENTITY;
    else if (io->read8(3u, io->context) != 0u)
        result = ACCELE160_S3_LOCKED;
    else for (block = S3_FIRST; block < S3_END; block += S3_BLOCK)
        if (io->read8(block + 2u, io->context) != 0u) {
            io->failed_offset = block;
            result = ACCELE160_S3_LOCKED;
            break;
        }
    array_mode(io, 0u);
    return result;
}

int accele160_s3_write_block(unsigned int offset,
    const unsigned char *bytes, unsigned int length, void *context)
{
    accele160_s3_io *io = (accele160_s3_io *)context;
    unsigned int i, address;
    int result;
    if (!io || !io->read8 || !io->write8 || !io->max_status_polls ||
        !bytes || length != S3_BLOCK || offset < S3_FIRST ||
        offset >= S3_END || (offset & (S3_BLOCK - 1u)))
        return ACCELE160_S3_ARGUMENT;
    io->failed_offset = offset;
    /* Probe immediately before each block; a lock change fails closed. */
    result = accele160_s3_probe(io);
    if (result) return result;
    io->write8(offset, 0x50u, io->context);
    io->write8(offset, 0x20u, io->context);
    io->write8(offset, 0xd0u, io->context);
    result = ready(io, offset);
    if (result == ACCELE160_S3_TIMEOUT) return result;
    array_mode(io, offset);
    if (result) return result;
    for (i = 0; i < S3_BLOCK; ++i)
        if (io->read8(offset + i, io->context) != 0xffu) {
            io->failed_offset = offset + i;
            return ACCELE160_S3_ERASE_VERIFY;
        }
    for (i = 0; i < S3_BLOCK; ++i) {
        if (bytes[i] == 0xffu) continue;
        address = offset + i;
        io->write8(address, 0x50u, io->context);
        io->write8(address, 0x40u, io->context);
        io->write8(address, bytes[i], io->context);
        result = ready(io, address);
        if (result == ACCELE160_S3_TIMEOUT) {
            io->failed_offset = address;
            return result;
        }
        array_mode(io, address);
        if (result) {
            io->failed_offset = address;
            return result;
        }
        if (io->read8(address, io->context) != bytes[i]) {
            io->failed_offset = address;
            return ACCELE160_S3_PROGRAM_VERIFY;
        }
    }
    /* The higher-level apply path performs a second full-block comparison. */
    return ACCELE160_S3_OK;
}

#include "flash_writer.h"

/* Stock 6.00-05 sets e0500000 bit 3 before its erase/program loop and clears
 * it afterward. The physical voltage and write strobe still need measurement. */
#define FLASH_GATE_BIT 0x08u
#define FIRST_BLOCK 0x40000u
#define LAST_BLOCK 0xc0000u
#define BLOCK_BYTES 0x10000u

#ifdef ACCELE160_FLASH_BACKEND_TEST
static unsigned char (*test_flash_read)(unsigned int);
static void (*test_flash_write)(unsigned int, unsigned char);
static unsigned char (*test_gate_read)(void);
static void (*test_gate_write)(unsigned char);

void accele160_flash_backend_set_test_io(
    unsigned char (*flash_read)(unsigned int),
    void (*flash_write)(unsigned int, unsigned char),
    unsigned char (*gate_read)(void),
    void (*gate_write)(unsigned char))
{
    test_flash_read = flash_read;
    test_flash_write = flash_write;
    test_gate_read = gate_read;
    test_gate_write = gate_write;
}

static unsigned char control_read(void) { return test_gate_read(); }
static void control_write(unsigned char value) { test_gate_write(value); }
#else
static volatile unsigned char *const flash_control =
    (volatile unsigned char *)(unsigned long)0xe0500000u;
static unsigned char control_read(void) { return *flash_control; }
static void control_write(unsigned char value)
{
    *flash_control = value;
    __asm__ volatile("syncf" ::: "memory");
}
#endif

static unsigned char flash_read8(unsigned int offset, void *context)
{
    (void)context;
#ifdef ACCELE160_FLASH_BACKEND_TEST
    return test_flash_read(offset);
#else
    return *(volatile unsigned char *)(unsigned long)(0xfef00000u + offset);
#endif
}

static void flash_write8(unsigned int offset, unsigned char value, void *context)
{
    (void)context;
#ifdef ACCELE160_FLASH_BACKEND_TEST
    test_flash_write(offset, value);
#else
    *(volatile unsigned char *)(unsigned long)(0xfef00000u + offset) = value;
    __asm__ volatile("syncf" ::: "memory");
#endif
}

accele160_s3_io accele160_flash_backend = {
    flash_read8, flash_write8, 0, 100000000u, 0u, 0u
};

static void report_result(unsigned int result)
{
#ifndef ACCELE160_FLASH_BACKEND_TEST
    volatile unsigned int *control =
        (volatile unsigned int *)(unsigned long)0xc0801000u;
    control[12] = result;
    control[13] = accele160_flash_backend.last_status;
    control[14] = accele160_flash_backend.failed_offset;
    __asm__ volatile("syncf" ::: "memory");
#else
    (void)result;
#endif
}

int accele160_flash_backend_write_block(unsigned int offset,
    const unsigned char *bytes, unsigned int length, void *context)
{
    unsigned char initial;
    int result;
    (void)context;
    accele160_flash_backend.last_status = 0u;
    accele160_flash_backend.failed_offset = offset;
    if (!bytes || length != BLOCK_BYTES || offset < FIRST_BLOCK ||
        offset >= LAST_BLOCK || (offset & (BLOCK_BYTES - 1u))) {
        report_result(ACCELE160_S3_ARGUMENT);
        return ACCELE160_S3_ARGUMENT;
    }
    initial = control_read();
    if (initial & FLASH_GATE_BIT) {
        report_result(ACCELE160_S3_GATE);
        return ACCELE160_S3_GATE;
    }
    control_write(initial | FLASH_GATE_BIT);
    if (!(control_read() & FLASH_GATE_BIT)) {
        control_write(initial);
        report_result(ACCELE160_S3_GATE);
        return ACCELE160_S3_GATE;
    }
    result = accele160_s3_write_block(offset, bytes, length,
                                      &accele160_flash_backend);
    control_write(initial);
    if (control_read() & FLASH_GATE_BIT) result = ACCELE160_S3_GATE;
    report_result((unsigned int)result);
    return result;
}

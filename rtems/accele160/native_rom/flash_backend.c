#include "flash_writer.h"

/* Stock 6.00-05 sets e0500000 bit 3 before its erase/program loop and clears
 * it afterward. The physical voltage and write strobe still need measurement.
 *
 * Stock never reads its gate write back. It reads this address as input pins
 * (boot block feffc0fc bit 1, loader fef43e8c bit 0, runtime c0052f64 and
 * c0082d6c) and writes only the constants 8 and 0 (boot block feff18a0 and
 * feff18dc, diagnostics fefcb0b4 and fefcb0e0) or a RAM shadow. So the gate
 * value is not built from a read, and a read is not a pass/fail condition.
 * With VPP below lockout the chip itself refuses the erase and sets SR.3,
 * which the writer returns as ACCELE160_S3_STATUS. */
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

/* UPD1 word 15 is report only: e0500000 as read while the gate was requested. */
static void report_result(unsigned int result, unsigned int gate_seen)
{
#ifndef ACCELE160_FLASH_BACKEND_TEST
    volatile unsigned int *control =
        (volatile unsigned int *)(unsigned long)0xc0801000u;
    control[12] = result;
    control[13] = accele160_flash_backend.last_status;
    control[14] = accele160_flash_backend.failed_offset;
    control[15] = gate_seen;
    __asm__ volatile("syncf" ::: "memory");
#else
    (void)result;
    (void)gate_seen;
#endif
}

int accele160_flash_backend_write_block(unsigned int offset,
    const unsigned char *bytes, unsigned int length, void *context)
{
    unsigned int gate_seen;
    int result;
    (void)context;
    accele160_flash_backend.last_status = 0u;
    accele160_flash_backend.failed_offset = offset;
    if (!bytes || length != BLOCK_BYTES || offset < FIRST_BLOCK ||
        offset >= LAST_BLOCK || (offset & (BLOCK_BYTES - 1u))) {
        report_result(ACCELE160_S3_ARGUMENT, 0u);
        return ACCELE160_S3_ARGUMENT;
    }
    control_write(FLASH_GATE_BIT);
    gate_seen = control_read();
    result = accele160_s3_write_block(offset, bytes, length,
                                      &accele160_flash_backend);
    control_write(0u);
    report_result((unsigned int)result, gate_seen);
    return result;
}

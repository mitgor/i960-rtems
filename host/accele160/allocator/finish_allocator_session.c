/* Finish one completed operation-3 session after exact capture review.
 * This submits no card command and touches only the fixed 16-byte result slot.
 */
#define _POSIX_C_SOURCE 200809L
#define _FILE_OFFSET_BITS 64
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/mman.h>
#include <unistd.h>

#define CONFIG "/sys/bus/pci/devices/0000:37:09.1/config"
#define RESOURCE "/sys/bus/pci/devices/0000:37:09.1/resource0"
#define STATUS "/sys/kernel/debug/accele-allocprobe/status"
#define RELEASE "/sys/kernel/debug/accele-allocprobe/release"
#define PAGE 4096

static void fail(const char *message) { perror(message); exit(1); }
static uint32_t word(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void read_exact(const char *path, uint8_t *out) {
    int fd = open(path, O_RDONLY); uint8_t extra;
    if (fd < 0) fail(path);
    if (read(fd, out, PAGE) != PAGE || read(fd, &extra, 1) != 0)
        { errno = EINVAL; fail("capture size"); }
    close(fd);
}
static uint32_t config_word(int fd) {
    uint8_t b[4];
    if (pread(fd, b, 4, 0x44) != 4) fail("read PIATVR");
    return word(b);
}
static void set_translation(int fd, uint32_t value) {
    uint8_t b[4] = {value, value >> 8, value >> 16, value >> 24};
    if (pwrite(fd, b, 4, 0x44) != 4 || config_word(fd) != value)
        { errno = EIO; fail("PIATVR readback"); }
}
static void snapshot(volatile uint8_t *bar, uint8_t *out) {
    for (size_t i = 0; i < PAGE; ++i) out[i] = bar[PAGE + i];
    __sync_synchronize();
}

int main(int argc, char **argv) {
    uint8_t before[PAGE], post_call[PAGE], table_before[PAGE], table_now[PAGE], now[PAGE];
    char status[280]; int lock, cfg, resource, fd; ssize_t n;
    volatile uint8_t *bar;
    if (argc != 4) {
        fprintf(stderr, "usage: %s PAGE_BEFORE PAGE_AFTER_CALL TABLE_BEFORE\n", argv[0]);
        return 2;
    }
    lock = open("/run/lock/i960-loadrun.lock", O_RDWR | O_CREAT, 0600);
    if (lock < 0 || flock(lock, LOCK_EX | LOCK_NB)) fail("global card lock");
    read_exact(argv[1], before); read_exact(argv[2], post_call);
    read_exact(argv[3], table_before);
    if (memcmp(before, post_call, 0x820) ||
        memcmp(before + 0x830, post_call + 0x830, PAGE - 0x830) ||
        before[0x820] != 0xff || word(post_call + 0x820) != 0x4f4c4c41u ||
        word(post_call + 0x824) != 0x16161031u ||
        word(post_call + 0x82c) != 0x40000u)
        { errno = EINVAL; fail("capture preflight"); }
    fd = open(STATUS, O_RDONLY); if (fd < 0) fail(STATUS);
    n = read(fd, status, sizeof(status) - 1); if (n < 0) fail("status read");
    status[n] = 0; close(fd);
    if (!strstr(status, "started=1 done=1 status=0 residual=0 released=0"))
        { errno = EBUSY; fail("command not completed and retained"); }
    cfg = open(CONFIG, O_RDWR | O_SYNC); if (cfg < 0) fail(CONFIG);
    if (config_word(cfg) != 0xc0000000u)
        { errno = EINVAL; fail("nondefault PIATVR"); }
    resource = open(RESOURCE, O_RDWR | O_SYNC); if (resource < 0) fail(RESOURCE);
    bar = mmap(NULL, 2 * PAGE, PROT_READ | PROT_WRITE, MAP_SHARED, resource, 0);
    if (bar == MAP_FAILED) fail("BAR0 mmap");
    set_translation(cfg, 0xc0384000u);
    snapshot(bar, table_now);
    if (memcmp(table_before + 0x2a0, table_now + 0x2a0, 0x800)) {
        set_translation(cfg, 0xc0000000u);
        errno = EIO; fail("live allocator metadata differs from preimage");
    }
    set_translation(cfg, 0xc000e000u);
    snapshot(bar, now);
    if (memcmp(now, post_call, PAGE)) {
        set_translation(cfg, 0xc0000000u);
        errno = EIO; fail("live page differs from captured post-call page");
    }
    for (size_t i = 0; i < 16; ++i) bar[PAGE + 0x820 + i] = before[0x820 + i];
    __sync_synchronize();
    snapshot(bar, now);
    if (memcmp(now, before, PAGE)) {
        set_translation(cfg, 0xc0000000u);
        errno = EIO; fail("result-slot restoration mismatch");
    }
    set_translation(cfg, 0xc0000000u);
    fd = open(RELEASE, O_WRONLY); if (fd < 0) fail(RELEASE);
    if (write(fd, "release\n", 8) != 8) fail("release companion");
    close(fd);
    printf("result_slot_restored=1 metadata_restored=1 PIATVR=%08x released=1\n",
           config_word(cfg));
    munmap((void *)bar, 2 * PAGE); close(resource); close(cfg); close(lock);
    return 0;
}

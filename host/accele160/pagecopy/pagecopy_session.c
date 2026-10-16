/* Fixed 512 KiB reserve, staging-to-even-page copy and release proof.
 * Both command companions are preloaded but idle. A timeout retains them and
 * the allocation for diagnosis; the program never frees an uncertain grant.
 */
#define _POSIX_C_SOURCE 200809L
#define _FILE_OFFSET_BITS 64
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#define DEVICE "/sys/bus/pci/devices/0000:37:09.1"
#define PAGE 4096u
#define META_FIRST 0x2a0u
#define META_BYTES 0x800u
#define OWNER 0x96016004u
#define SIZE 0x80000u

static int cfg = -1, resource = -1;
static volatile uint8_t *bar;
static uint32_t original_translation;
static int translated, started;

static void die(const char *why) { perror(why); exit(1); }
static uint32_t word(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
           (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}
static void put_word(uint8_t *p, uint32_t v) {
    p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24;
}
static uint32_t fnv_page(const uint8_t *p) {
    uint32_t h = 0x811c9dc5u;
    for (size_t i = 0; i < PAGE; ++i) h = (h ^ p[i]) * 0x01000193u;
    return h;
}
static uint32_t config_word(void) {
    uint8_t b[4]; if (pread(cfg, b, 4, 0x44) != 4) die("PIATVR read");
    return word(b);
}
static void translate(uint32_t value) {
    uint8_t b[4] = {value, value >> 8, value >> 16, value >> 24};
    if (pwrite(cfg, b, 4, 0x44) != 4 || config_word() != value)
        { errno = EIO; die("PIATVR readback"); }
    translated = value != original_translation;
}
static void cleanup(void) {
    if (cfg >= 0 && translated) translate(original_translation);
    if (bar) munmap((void *)bar, 2 * PAGE);
    if (resource >= 0) close(resource);
    if (cfg >= 0) close(cfg);
    if (started) fprintf(stderr, "PENDING: keep both companions and retained RAM for inspection\n");
}
static void snapshot(uint8_t *out) {
    for (size_t i = 0; i < PAGE; ++i) out[i] = bar[PAGE + i];
    __sync_synchronize();
}
static void save(const char *path, const uint8_t *bytes) {
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0) die(path);
    if (write(fd, bytes, PAGE) != PAGE || fsync(fd)) die("capture write");
    close(fd);
}
static void write_result(const uint8_t *bytes) {
    for (size_t i = 0; i < 16; ++i) bar[PAGE + 0x820 + i] = bytes[i];
    __sync_synchronize();
}
static void read_file(const char *path, char *out, size_t cap) {
    int fd = open(path, O_RDONLY); ssize_t n;
    if (fd < 0) die(path);
    n = read(fd, out, cap - 1); if (n < 0) die("status read");
    out[n] = 0; close(fd);
}
static void control(const char *path, const char *value) {
    int fd = open(path, O_WRONLY); size_t n = strlen(value);
    if (fd < 0 || write(fd, value, n) != (ssize_t)n) die(path);
    close(fd);
}
static void command(const char *name, const char *status_output) {
    char path[160], status[320];
    struct timespec pause = {.tv_sec = 0, .tv_nsec = 50000000};
    snprintf(path, sizeof(path), "/sys/kernel/debug/accele-%s/status", name);
    read_file(path, status, sizeof(status));
    if (!strstr(status, "started=0 done=0")) { errno = EBUSY; die("companion already started"); }
    snprintf(path, sizeof(path), "/sys/kernel/debug/accele-%s/start", name);
    control(path, "probe\n");
    started = 1;
    snprintf(path, sizeof(path), "/sys/kernel/debug/accele-%s/status", name);
    for (int i = 0; i < 100; ++i) {
        read_file(path, status, sizeof(status));
        if (strstr(status, "started=1 done=1")) break;
        nanosleep(&pause, NULL);
    }
    int fd = open(status_output, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0) die(status_output);
    if (write(fd, status, strlen(status)) != (ssize_t)strlen(status) || fsync(fd))
        die("save command status");
    close(fd);
    if (!strstr(status, "started=1 done=1 status=0 residual=0"))
        { errno = ETIMEDOUT; die("command incomplete or failed"); }
}
static void release_companion(const char *name) {
    char path[160];
    snprintf(path, sizeof(path), "/sys/kernel/debug/accele-%s/release", name);
    control(path, "release\n");
}
static int expected_grant(const uint8_t *before, const uint8_t *after, uint32_t ptr) {
    unsigned first = (ptr - 0xc0000000u) / 0x8000u;
    if (ptr < 0xc0618000u || ptr > 0xc0710000u || (ptr & 0x7fffu)) return 0;
    for (unsigned i = 0; i < 256; ++i) {
        uint32_t bc = word(before + META_FIRST + 4 * i);
        uint32_t bo = word(before + META_FIRST + 0x400 + 4 * i);
        uint32_t ac = word(after + META_FIRST + 4 * i);
        uint32_t ao = word(after + META_FIRST + 0x400 + 4 * i);
        if (i >= first && i < first + 16) {
            if (bc || bo || ac != 16 || ao != OWNER) return 0;
        } else if (bc != ac || bo != ao) return 0;
    }
    return 1;
}

int main(int argc, char **argv) {
    uint8_t page_before[PAGE], page_reserved[PAGE], page_after[PAGE];
    uint8_t table_before[PAGE], table_reserved[PAGE], table_after[PAGE];
    uint8_t staging_before[PAGE], staging_pattern[PAGE], staging_readback[PAGE];
    uint8_t page_copied[PAGE], control_record[16];
    uint8_t sentinel[16], check[PAGE]; uint32_t ptr, hash;
    if (argc != 2) {
        fprintf(stderr, "usage: %s OUTPUT_DIRECTORY\n", argv[0]);
        return 2;
    }
    cfg = open(DEVICE "/config", O_RDWR | O_SYNC); if (cfg < 0) die("PCI config");
    original_translation = config_word();
    if (original_translation != 0xc0000000u) { errno = EINVAL; die("unexpected PIATVR"); }
    resource = open(DEVICE "/resource0", O_RDWR | O_SYNC); if (resource < 0) die("BAR0");
    bar = mmap(NULL, 2 * PAGE, PROT_READ | PROT_WRITE, MAP_SHARED, resource, 0);
    if (bar == MAP_FAILED) { bar = NULL; die("BAR0 mmap"); }
    if (atexit(cleanup)) die("atexit");
    char output[512];
#define SAVE(file, bytes) do { snprintf(output, sizeof(output), "%s/%s", argv[1], file); save(output, bytes); } while (0)
    translate(0xc0384000u); snapshot(table_before); SAVE("table-before.bin", table_before);
    translate(0xc000e000u); snapshot(page_before); SAVE("page-before.bin", page_before);
    for (size_t i = 0; i < PAGE; ++i)
        if (page_before[i] != 0xff) { errno = EINVAL; die("result page not erased"); }
    memset(sentinel, 0xa5, sizeof(sentinel)); write_result(sentinel);
    snapshot(check);
    if (memcmp(check + 0x820, sentinel, 16)) { errno = EIO; die("sentinel readback"); }
    translate(original_translation);
    snprintf(output, sizeof(output), "%s/reserve-status.txt", argv[1]);
    command("reserve", output);
    translate(0xc000e000u); snapshot(page_reserved); SAVE("page-reserved.bin", page_reserved);
    ptr = word(page_reserved + 0x828);
    if (word(page_reserved + 0x820) != 0x4f4c4c41u ||
        word(page_reserved + 0x824) != 0x16161041u ||
        word(page_reserved + 0x82c) != SIZE ||
        word(page_reserved + 0x840) != 0x56525352u ||
        word(page_reserved + 0x844) != ptr ||
        word(page_reserved + 0x848) != SIZE ||
        word(page_reserved + 0x84c) != OWNER)
        { errno = EIO; die("reserve result mismatch"); }
    translate(0xc0384000u); snapshot(table_reserved); SAVE("table-reserved.bin", table_reserved);
    if (!expected_grant(table_before, table_reserved, ptr))
        { errno = EIO; die("allocator grant metadata mismatch"); }
    translate(0xc000e000u); write_result(page_before + 0x820);
    snapshot(check);
    memcpy(page_reserved + 0x820, page_before + 0x820, 16);
    if (memcmp(check, page_reserved, PAGE)) { errno = EIO; die("reserved page result restoration"); }
    translate(original_translation);
    release_companion("reserve");

    /* Last odd page is the only source. The first grant page is even and
     * cannot be directly addressed by this BAR, so card-side copy matters.
     */
    translate(ptr + 0x7e000u);
    snapshot(staging_before); SAVE("staging-before.bin", staging_before);
    for (size_t i = 0; i < PAGE; ++i)
        staging_pattern[i] = (uint8_t)(((i * 53u + 0x96u) ^ (i >> 3)) & 0xffu);
    SAVE("staging-pattern.bin", staging_pattern);
    for (size_t i = 0; i < PAGE; ++i) bar[PAGE + i] = staging_pattern[i];
    __sync_synchronize();
    snapshot(staging_readback); SAVE("staging-readback.bin", staging_readback);
    if (memcmp(staging_pattern, staging_readback, PAGE))
        { errno = EIO; die("staging readback mismatch"); }
    hash = fnv_page(staging_pattern);
    translate(0xc000e000u); snapshot(check);
    for (size_t i = 0x860; i < 0x870; ++i)
        if (check[i] != 0xff) { errno = EINVAL; die("copy control record not erased"); }
    put_word(control_record + 0, 0x59504f43u);
    put_word(control_record + 4, 0x16161061u);
    put_word(control_record + 8, 0); /* fixed first even target page */
    put_word(control_record + 12, hash);
    for (size_t i = 0; i < 16; ++i) bar[PAGE + 0x860 + i] = control_record[i];
    memset(sentinel, 0xa5, sizeof(sentinel)); write_result(sentinel);
    snapshot(check);
    if (memcmp(check + 0x860, control_record, 16) ||
        memcmp(check + 0x820, sentinel, 16))
        { errno = EIO; die("copy control or sentinel readback"); }
    translate(original_translation);
    snprintf(output, sizeof(output), "%s/copy-status.txt", argv[1]);
    command("copy", output);
    translate(0xc000e000u); snapshot(page_copied); SAVE("page-copied.bin", page_copied);
    if (word(page_copied + 0x820) != 0x59504f43u ||
        word(page_copied + 0x824) != 0x16161061u ||
        word(page_copied + 0x828) != 0 ||
        word(page_copied + 0x82c) != hash ||
        memcmp(page_copied + 0x860, control_record, 16))
        { errno = EIO; die("card-side copy result mismatch"); }
    for (size_t i = 0; i < 16; ++i) bar[PAGE + 0x860 + i] = page_before[0x860 + i];
    write_result(page_before + 0x820);
    snapshot(check);
    if (memcmp(check, page_reserved, PAGE))
        { errno = EIO; die("copy controls did not restore"); }
    translate(ptr + 0x7e000u);
    for (size_t i = 0; i < PAGE; ++i) bar[PAGE + i] = staging_before[i];
    __sync_synchronize();
    snapshot(check); SAVE("staging-restored.bin", check);
    if (memcmp(check, staging_before, PAGE))
        { errno = EIO; die("staging page did not restore"); }
    translate(0xc0384000u); snapshot(check);
    if (memcmp(check + META_FIRST, table_reserved + META_FIRST, META_BYTES))
        { errno = EIO; die("copy changed allocator metadata"); }
    translate(original_translation);
    release_companion("copy");

    memset(sentinel, 0xa5, sizeof(sentinel));
    translate(0xc000e000u); write_result(sentinel);
    snapshot(check);
    if (memcmp(check + 0x820, sentinel, 16)) { errno = EIO; die("release sentinel readback"); }
    translate(original_translation);
    snprintf(output, sizeof(output), "%s/release-status.txt", argv[1]);
    command("release", output);
    translate(0xc000e000u); snapshot(page_after); SAVE("page-after.bin", page_after);
    if (word(page_after + 0x820) != 0x45455246u ||
        word(page_after + 0x824) != 0x16161051u ||
        word(page_after + 0x828) != ptr ||
        word(page_after + 0x82c) != SIZE ||
        memcmp(page_after + 0x840, page_before + 0x840, 16))
        { errno = EIO; die("release result or state mismatch"); }
    translate(0xc0384000u); snapshot(table_after); SAVE("table-after.bin", table_after);
    if (memcmp(table_before + META_FIRST, table_after + META_FIRST, META_BYTES))
        { errno = EIO; die("allocator metadata did not restore"); }
    translate(0xc000e000u); write_result(page_before + 0x820);
    snapshot(check);
    if (memcmp(check, page_before, PAGE)) { errno = EIO; die("loader page did not restore"); }
    translate(original_translation);
    release_companion("release");
    started = 0;
    printf("pointer=%08x size=%u copied_even_page=%08x fnv=%08x metadata_restored=1 loader_page_restored=1 PIATVR=%08x companions_released=1\n",
           ptr, SIZE, ptr, hash, config_word());
    return 0;
}

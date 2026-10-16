/* Exact, bounded MMIO result staging and 0x8f operation-3 allocator call on AcceleRAID 160.
 * Run only after the separately audited firmware image has been programmed.
 * The command companion is loaded but submits nothing until start is written.
 * If completion does not arrive, leave its module and RAM result slot retained.
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
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define CONFIG "/sys/bus/pci/devices/0000:37:09.1/config"
#define RESOURCE "/sys/bus/pci/devices/0000:37:09.1/resource0"
#define STATUS "/sys/kernel/debug/accele-allocprobe/status"
#define START "/sys/kernel/debug/accele-allocprobe/start"
#define RELEASE "/sys/kernel/debug/accele-allocprobe/release"
#define PAGE 4096u
#define RESULT 16u
#define NONCE 0x16161031u

static int config_fd = -1, resource_fd = -1;
static volatile uint8_t *bar;
static uint32_t translation;
static int translated, staged, completed;

static void die(const char *message)
{
    fprintf(stderr, "%s: %s\n", message, strerror(errno));
    exit(1);
}

static uint32_t word(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static uint32_t config_word(void)
{
    uint8_t b[4];
    if (pread(config_fd, b, 4, 0x44) != 4) die("read PIATVR");
    return word(b);
}

static void set_translation(uint32_t value)
{
    uint8_t b[4] = { value, value >> 8, value >> 16, value >> 24 };
    if (pwrite(config_fd, b, 4, 0x44) != 4) die("write PIATVR");
    if (config_word() != value) { errno = EIO; die("PIATVR readback"); }
    translated = value != translation;
}

static void cleanup(void)
{
    if (config_fd >= 0 && translated) set_translation(translation);
    if (bar) munmap((void *)bar, 2 * PAGE);
    if (resource_fd >= 0) close(resource_fd);
    if (config_fd >= 0) close(config_fd);
    if (staged && !completed)
        fprintf(stderr, "PENDING: keep RAM and command module pinned; inspect card before any cleanup\n");
}

static void read_page(uint8_t *out)
{
    size_t i;
    for (i = 0; i < PAGE; ++i) out[i] = bar[PAGE + i];
    __sync_synchronize();
}

static void write_bytes(size_t offset, const uint8_t *bytes, size_t count)
{
    size_t i;
    for (i = 0; i < count; ++i) bar[PAGE + offset + i] = bytes[i];
    __sync_synchronize();
}

static void control_file(const char *path, const char *value)
{
    int fd = open(path, O_WRONLY);
    size_t n = strlen(value);
    if (fd < 0) die(path);
    if (write(fd, value, n) != (ssize_t)n) die(path);
    close(fd);
}

static void read_status(char *out, size_t capacity)
{
    int fd = open(STATUS, O_RDONLY);
    ssize_t n;
    if (fd < 0) die(STATUS);
    n = read(fd, out, capacity - 1);
    if (n < 0) die("read status");
    out[n] = 0;
    close(fd);
}

static int field(const char *status, const char *name)
{
    char key[40];
    const char *at;
    snprintf(key, sizeof(key), "%s=", name);
    at = strstr(status, key);
    if (!at) { errno = EINVAL; die("status field missing"); }
    return atoi(at + strlen(key));
}

static void save(const char *path, const uint8_t *data, size_t n)
{
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0) die(path);
    if (write(fd, data, n) != (ssize_t)n || fsync(fd)) die("save capture");
    close(fd);
}

int main(int argc, char **argv)
{
    uint8_t original[PAGE], after[PAGE], table_before[PAGE], table_after[PAGE], sentinel[RESULT];
    char status[300];
    struct timespec pause = { .tv_sec = 0, .tv_nsec = 50000000 };
    int i, command_status, residual, good;

    if (argc != 5) {
        fprintf(stderr, "usage: %s PAGE_BEFORE PAGE_AFTER TABLE_BEFORE TABLE_AFTER\n", argv[0]);
        return 2;
    }
    config_fd = open(CONFIG, O_RDWR | O_SYNC);
    if (config_fd < 0) die(CONFIG);
    translation = config_word();
    if (translation != 0xc0000000u) { errno = EINVAL; die("unexpected PIATVR"); }
    resource_fd = open(RESOURCE, O_RDWR | O_SYNC);
    if (resource_fd < 0) die(RESOURCE);
    bar = mmap(NULL, 2 * PAGE, PROT_READ | PROT_WRITE, MAP_SHARED, resource_fd, 0);
    if (bar == MAP_FAILED) { bar = NULL; die("mmap BAR0"); }
    if (atexit(cleanup)) die("atexit");
    read_status(status, sizeof(status));
    if (field(status, "started") != 0) { errno = EBUSY; die("command already started"); }

    /* PIATVR is aligned to 8 KiB: upper BAR page maps c000f000..ffff. */
    set_translation(0xc0384000u);
    read_page(table_before);
    save(argv[3], table_before, PAGE);
    set_translation(0xc000e000u);
    read_page(original);
    for (i = 0; i < (int)PAGE; ++i)
        if (original[i] != 0xff) { errno = EINVAL; die("c000f000 page not erased"); }
    save(argv[1], original, PAGE);
    memset(sentinel, 0xa5, sizeof(sentinel));
    write_bytes(0x820, sentinel, RESULT);
    read_page(after);
    if (memcmp(after + 0x820, sentinel, RESULT)) {
        write_bytes(0x820, original + 0x820, RESULT);
        errno = EIO; die("payload MMIO readback mismatch");
    }
    staged = 1;
    set_translation(translation);
    control_file(START, "probe\n");
    for (i = 0; i < 100; ++i) {
        read_status(status, sizeof(status));
        if (field(status, "done") == 1) break;
        nanosleep(&pause, NULL);
    }
    if (i == 100) { errno = ETIMEDOUT; die("command completion timeout"); }
    completed = 1;
    command_status = field(status, "status");
    residual = field(status, "residual");
    printf("command_status=%d residual=%d\n", command_status, residual);
    set_translation(0xc000e000u);
    read_page(after);
    save(argv[2], after, PAGE);
    good = command_status == 0 && residual == 0 &&
           word(after + 0x820) == 0x4f4c4c41u &&
           word(after + 0x824) == NONCE &&
           word(after + 0x828) >= 0xc0618000u &&
           word(after + 0x828) < 0xc0790000u &&
           (word(after + 0x828) & 0x7fffu) == 0 &&
           word(after + 0x82c) == 0x40000u;
    printf("result=%08x,%08x,%08x,%08x verified=%d\n",
           word(after + 0x820), word(after + 0x824),
           word(after + 0x828), word(after + 0x82c), good);
    set_translation(0xc0384000u);
    read_page(table_after);
    save(argv[4], table_after, PAGE);
    /* Only 0x2a0..0xa9f contains the 256 count and 256 owner words.
     * Adjacent stock firmware state at 0xaa0 can advance independently.
     */
    if (memcmp(table_before + 0x2a0, table_after + 0x2a0, 0x800))
        { errno = EIO; die("allocator count/owner arrays not restored"); }
    set_translation(0xc000e000u);
    write_bytes(0x820, original + 0x820, RESULT);
    read_page(after);
    if (memcmp(after, original, PAGE)) { errno = EIO; die("full-page restoration mismatch"); }
    set_translation(translation);
    control_file(RELEASE, "release\n");
    printf("full_page_restored=1 allocator_metadata_restored=1 PIATVR=%08x released=1\n", config_word());
    return good ? 0 : 1;
}

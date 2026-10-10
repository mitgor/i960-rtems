/* Linux host sender. See README.md and PROTOCOL.md for ownership and recovery. */
#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE 1
#define _DARWIN_C_SOURCE 1
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>
#include <errno.h>
#include <ctype.h>
#include <limits.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <dirent.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <sys/mman.h>
#include "mu.h"

#define WINDOW 0x2000u
#define TIMEOUT_NS UINT64_C(2000000000)
#ifndef LOADCTL_TEST
static volatile uint32_t *bar;
#endif
static uint16_t seq;

#ifndef LOADCTL_TEST
static uint32_t rd(int off) { return bar[off / 4]; }
static void wr(int off, uint32_t v) { bar[off / 4] = v; __sync_synchronize(); }
static uint64_t now_ns(void)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) { perror("clock_gettime"); exit(1); }
    return (uint64_t)t.tv_sec * UINT64_C(1000000000) + (uint64_t)t.tv_nsec;
}
static void poll_pause(void)
{
    const struct timespec t = {0, 50000}; /* 50 us; deadline remains monotonic */
    nanosleep(&t, NULL);
}
#else
static uint32_t rd(int off);
static void wr(int off, uint32_t v);
static uint64_t now_ns(void);
static void poll_pause(void);
#endif

static int known_status(uint32_t o)
{
    unsigned int s = o & 0xffffu;
    return s == ST_READY || s == ST_OK || s == ST_BADOP ||
           s == ST_BADADDR || s == ST_BADSTATE;
}

/* Complete any pending transaction before choosing a fresh sequence. Never
 * resend an unacknowledged WRITE: the card may already have incremented dst. */
static int synchronize(void)
{
    uint64_t start = now_ns();
    uint32_t o, incoming;
    do {
        o = rd(R_OMR0);
        if (!known_status(o)) {
            fprintf(stderr, "loader unavailable or handed off: OMR0=0x%08" PRIx32 "\n", o);
            return -1;
        }
        incoming = rd(R_IMR1);
        if ((o >> 16) == (incoming >> 16)) {
            seq = (uint16_t)(o >> 16);
            return 0;
        }
        poll_pause();
    } while (now_ns() - start < TIMEOUT_NS);
    fprintf(stderr, "pending command unresolved: IMR1=0x%08" PRIx32
                    " OMR0=0x%08" PRIx32 "; reset/reinspect before retrying\n", incoming, o);
    return -1;
}

static int command(uint16_t op, uint32_t arg)
{
    uint64_t start;
    uint32_t o = 0;
    seq = (uint16_t)(seq + 1u);
    wr(R_IMR0, arg);
    wr(R_IMR1, ((uint32_t)seq << 16) | op);
    start = now_ns();
    do {
        o = rd(R_OMR0);
        if ((o >> 16) == seq) return (int)(o & 0xffffu);
        poll_pause();
    } while (now_ns() - start < TIMEOUT_NS);
    fprintf(stderr, "timeout: op=%u arg=0x%08" PRIx32 " expected-seq=%u OMR0=0x%08" PRIx32 "\n",
            op, arg, seq, o);
    return -1;
}

static int expect(uint16_t op, uint32_t arg, int wanted)
{
    int status = command(op, arg);
    if (status == wanted) return 0;
    if (status >= 0) fprintf(stderr, "op=%u rejected: status=0x%04x (expected 0x%04x)\n", op, status, wanted);
    return -1;
}

static uint32_t word(const unsigned char *b)
{
    return (uint32_t)b[0] | ((uint32_t)b[1] << 8) |
           ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24);
}

/* Read and validate the complete file BEFORE sending any commands. The bounded
 * buffer also makes readback compare against precisely the bytes transmitted. */
static int load_file(uint32_t addr, const char *path)
{
    unsigned char data[PAYLOAD_END - PAYLOAD_BASE + 1u] = {0};
    size_t bytes, padded, i;
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return 1; }
    bytes = fread(data, 1, sizeof(data), f);
    if (ferror(f)) { perror("payload read"); fclose(f); return 1; }
    if (fclose(f)) { perror("payload close"); return 1; }
    if (!bytes || bytes > PAYLOAD_END - PAYLOAD_BASE || !payload_word(addr)) {
        fprintf(stderr, "payload must be nonempty, aligned, and fit internal RAM [0x200,0x400)\n");
        return 1;
    }
    padded = (bytes + 3u) & ~(size_t)3u;
    if (padded > (size_t)(PAYLOAD_END - addr)) {
        fprintf(stderr, "padded payload exceeds internal RAM at 0x%08" PRIx32 "\n", addr);
        return 1;
    }
    if (expect(OP_SET_ADDR, addr, ST_OK)) return 1;
    for (i = 0; i < padded; i += 4u) {
        if (expect(OP_WRITE, word(data + i), ST_OK)) {
            fprintf(stderr, "upload incomplete at byte %zu; do not GO\n", i);
            return 1;
        }
    }
    for (i = 0; i < padded; i += 4u) {
        uint32_t a = addr + (uint32_t)i;
        if (expect(OP_READ, a, ST_OK)) return 1;
        if (rd(R_OMR1) != word(data + i)) {
            fprintf(stderr, "verification mismatch at 0x%08" PRIx32 "; do not GO\n", a);
            return 1;
        }
    }
    printf("loaded and verified %zu bytes (%zu padded bytes) at 0x%08" PRIx32 "\n", bytes, padded, addr);
    return 0;
}

static int parse_number(const char *s, uint64_t max, uint64_t *value)
{
    char *end;
    unsigned long long v;
    if (!s[0] || s[0] == '-' || s[0] == '+' || isspace((unsigned char)s[0])) return -1;
    errno = 0;
    v = strtoull(s, &end, 0);
    if (errno || *end || v > max) return -1;
    *value = (uint64_t)v;
    return 0;
}

#ifndef PCI_SYSFS_ROOT
#define PCI_SYSFS_ROOT "/sys/bus/pci/devices"
#endif

static int read_number_file(const char *path, uint64_t *value)
{
    char buf[64];
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    if (!fgets(buf, sizeof(buf), f)) { fclose(f); return -1; }
    fclose(f);
    buf[strcspn(buf, "\r\n")] = 0;
    return parse_number(buf, UINT64_MAX, value);
}

/* Accept a full PCI BDF or the historical BAR0 address; both resolve to one
 * DAC960PG resource0. Never map an arbitrary physical address via /dev/mem. */
static int device_path(const char *selector, char *result, size_t size)
{
    DIR *dir = opendir(PCI_SYSFS_ROOT);
    struct dirent *entry;
    uint64_t phys = 0;
    int by_phys = parse_number(selector, UINT64_MAX, &phys) == 0;
    int matches = 0;
    if (!dir) { perror("PCI sysfs"); return -1; }
    while ((entry = readdir(dir))) {
        char path[512];
        uint64_t vendor, device;
        unsigned long long base, end, flags;
        FILE *f;
        if (entry->d_name[0] == '.') continue;
        if (!by_phys && strcmp(selector, entry->d_name)) continue;
        snprintf(path, sizeof(path), "%s/%s/vendor", PCI_SYSFS_ROOT, entry->d_name);
        if (read_number_file(path, &vendor) || vendor != 0x1069u) continue;
        snprintf(path, sizeof(path), "%s/%s/device", PCI_SYSFS_ROOT, entry->d_name);
        if (read_number_file(path, &device) || device != 0x0010u) continue;
        snprintf(path, sizeof(path), "%s/%s/resource", PCI_SYSFS_ROOT, entry->d_name);
        f = fopen(path, "r");
        if (!f) continue;
        int valid = fscanf(f, "%llx %llx %llx", &base, &end, &flags) == 3;
        fclose(f);
        if (!valid || !base || end < base || end - base < WINDOW - 1u || !(flags & 0x200u)) continue;
        if (by_phys && (uint64_t)base != phys) continue;
        snprintf(result, size, "%s/%s", PCI_SYSFS_ROOT, entry->d_name);
        matches++;
    }
    closedir(dir);
    if (matches != 1) { fprintf(stderr, "selector must identify exactly one 1069:0010 device with a memory BAR0\n"); return -1; }
    return 0;
}

static int unbound(const char *device)
{
    char path[600];
    struct stat st;
    snprintf(path, sizeof(path), "%s/driver", device);
    if (lstat(path, &st) == 0 || errno != ENOENT) {
        fprintf(stderr, "device has a bound driver or ownership cannot be checked; unbind it first\n");
        return 0;
    }
    return 1;
}

#ifndef LOADCTL_TEST
int main(int argc, char **argv)
{
    char device[512], path[600];
    uint64_t address = 0, value = 0;
    const char *cmd;
    int expected_argc, fd = -1, lockfd = -1, rc = 1;
    if (argc < 3) goto usage;
    cmd = argv[2];
    if (!strcmp(cmd, "status") || !strcmp(cmd, "ping")) expected_argc = 3;
    else if (!strcmp(cmd, "read") || !strcmp(cmd, "go") || !strcmp(cmd, "reg-read")) expected_argc = 4;
    else if (!strcmp(cmd, "load") || !strcmp(cmd, "reg-write")) expected_argc = 5;
    else goto usage;
    if (argc != expected_argc) goto usage;
    if (argc >= 4 && parse_number(argv[3], UINT32_MAX, &address)) goto usage;
    if (!strcmp(cmd, "reg-write") && parse_number(argv[4], UINT32_MAX, &value)) goto usage;
    if (argc >= 4 && !(strstr(cmd, "reg-") ? register_word((uint32_t)address) : payload_word((uint32_t)address))) {
        fprintf(stderr, "address outside allowed aligned %s region\n", strstr(cmd, "reg-") ? "register" : "payload");
        return 2;
    }
    if (device_path(argv[1], device, sizeof(device))) return 1;
    /* Lock the device's sysfs config inode, common to BDF and physical selectors.
     * Advisory: all loadctl instances cooperate; other tools/driver binds do not. */
    snprintf(path, sizeof(path), "%s/config", device);
    lockfd = open(path, O_RDONLY | O_CLOEXEC);
    if (lockfd < 0 || flock(lockfd, LOCK_EX | LOCK_NB)) { perror("device lock"); goto done; }
    if (!unbound(device)) goto done;
    snprintf(path, sizeof(path), "%s/resource0", device);
    fd = open(path, O_RDWR | O_SYNC | O_CLOEXEC);
    if (fd < 0) { perror("resource0"); goto done; }
    bar = mmap(NULL, WINDOW, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (bar == MAP_FAILED) { perror("mmap resource0"); bar = NULL; goto done; }
    if (!unbound(device)) goto done;
    if (!strcmp(cmd, "status")) {
        uint32_t o = rd(R_OMR0);
        printf("OMR0=0x%08" PRIx32 " ackseq=%u status=0x%04x OMR1=0x%08" PRIx32 "\n",
               o, o >> 16, o & 0xffffu, rd(R_OMR1));
        rc = 0;
        goto done;
    }
    if (synchronize()) goto done;
    if (!strcmp(cmd, "ping")) {
        rc = expect(OP_PING, 0, ST_OK) != 0;
        if (!rc) puts("ping: acknowledged");
    } else if (!strcmp(cmd, "load")) {
        rc = load_file((uint32_t)address, argv[4]);
    } else if (!strcmp(cmd, "read") || !strcmp(cmd, "reg-read")) {
        rc = expect(!strcmp(cmd, "read") ? OP_READ : OP_REG_READ, (uint32_t)address, ST_OK) != 0;
        if (!rc) printf("[0x%08" PRIx32 "]=0x%08" PRIx32 "\n", (uint32_t)address, rd(R_OMR1));
    } else if (!strcmp(cmd, "reg-write")) {
        rc = expect(OP_SET_REG_ADDR, (uint32_t)address, ST_OK) != 0;
        if (!rc) rc = expect(OP_REG_WRITE, (uint32_t)value, ST_OK) != 0;
    } else {
        rc = expect(OP_GO, (uint32_t)address, ST_HANDOFF) != 0;
        if (!rc) puts("go: hand-off acknowledged; use status to inspect the payload marker");
    }
 done:
    if (bar) munmap((void *)bar, WINDOW);
    if (fd >= 0) close(fd);
    if (lockfd >= 0) close(lockfd);
    return rc;
 usage:
    fprintf(stderr, "usage: %s <PCI-BDF|BAR0-phys> ping|status|read ADDR|load ADDR FILE|go ADDR|reg-read ADDR|reg-write ADDR WORD\n", argv[0]);
    return 2;
}
#endif

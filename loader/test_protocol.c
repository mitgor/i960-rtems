#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE 1
#define _DARWIN_C_SOURCE 1
/* Native tests of the actual C sender and firmware command dispatcher.
 * Fake hardware uses delayed consumption, including ACK reads before the card
 * executes: this is the ordering the former Python model failed to exercise. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include "mu.h"
static uint32_t registers[8], memory[REG_END / 4u];
#define REG(off) registers[(off) / 4]
#define MEMORY(addr) memory[(addr) / 4]
#define LOADER_TEST
#include "loader.c"
static char fake_sysfs_root[128];
#define PCI_SYSFS_ROOT fake_sysfs_root
#define LOADCTL_TEST
#include "loadctl.c"

static struct loader_state card;
static uint64_t fake_time;
static int stopped, freeze, corrupt, reject;
static unsigned int consumed;
static unsigned int payload_reads;

static void step(void)
{
    uint32_t cmd = REG(R_IMR1), status;
    if (stopped || freeze || (cmd >> 16) == card.last) return;
    consumed++;
    status = reject ? ST_BADOP : dispatch(&card, cmd & 0xffffu, REG(R_IMR0));
    if ((cmd & 0xffffu) == OP_READ) {
        payload_reads++;
        if (corrupt) REG(R_OMR1) ^= 1;
    }
    card.last = cmd >> 16;
    REG(R_OMR0) = (card.last << 16) | status;
    if (status == ST_HANDOFF) {
        stopped = 1;
        REG(R_OMR1) = PAYLOAD_MAGIC; /* immediate payload execution */
    }
}
static uint32_t rd(int off) { return REG(off); }
static void wr(int off, uint32_t v) { REG(off) = v; }
static uint64_t now_ns(void) { return fake_time; }
static void poll_pause(void) { fake_time += UINT64_C(100000000); step(); }
static void reset(uint16_t initial)
{
    memset(registers, 0, sizeof(registers)); memset(memory, 0, sizeof(memory));
    card.last = initial; card.dst = card.mode = 0;
    REG(R_IMR1) = (uint32_t)initial << 16;
    REG(R_OMR0) = ((uint32_t)initial << 16) | ST_READY;
    fake_time = 0; stopped = freeze = corrupt = reject = 0;
    consumed = payload_reads = 0;
    seq = 0;
}
static void test_restart(void)
{
    reset(0);
    assert(!synchronize()); assert(!expect(OP_PING, 0, ST_OK));
    seq = 0; /* a fresh CLI process */
    assert(!synchronize()); assert(seq == 1);
    assert(!expect(OP_SET_ADDR, PAYLOAD_BASE, ST_OK));
    assert(consumed == 2 && card.dst == PAYLOAD_BASE);
    /* Pending command from a crashed host: drain rather than overwrite. */
    REG(R_IMR0) = 42;
    REG(R_IMR1) = (3u << 16) | OP_WRITE;
    seq = 0; assert(!synchronize());
    assert(seq == 3 && memory[PAYLOAD_BASE / 4] == 42);
    assert(!expect(OP_PING, 0, ST_OK));
    reset(0xffffu); assert(!synchronize());
    assert(!expect(OP_PING, 0, ST_OK)); assert(seq == 0 && consumed == 1);
    /* Reset discards stale input by publishing READY at the incoming sequence. */
    reset(17); assert(!synchronize()); assert(!expect(OP_PING, 0, ST_OK)); assert(seq == 18);
}
static void test_validation(void)
{
    reset(0);
    assert(dispatch(&card, OP_WRITE, 1) == ST_BADSTATE);
    assert(dispatch(&card, OP_SET_ADDR, 0) == ST_BADADDR);
    assert(dispatch(&card, OP_SET_ADDR, 0x201) == ST_BADADDR);
    assert(dispatch(&card, OP_SET_ADDR, 0xfffffffcu) == ST_BADADDR);
    assert(dispatch(&card, OP_SET_ADDR, PAYLOAD_END - 4u) == ST_OK);
    assert(dispatch(&card, OP_WRITE, 7) == ST_OK);
    assert(dispatch(&card, OP_WRITE, 8) == ST_BADADDR);
    assert(memory[(PAYLOAD_END - 4u) / 4] == 7);
    assert(dispatch(&card, OP_SET_ADDR, 0x40) == ST_BADADDR);
    assert(dispatch(&card, OP_WRITE, 8) == ST_BADSTATE);
    assert(dispatch(&card, OP_READ, PAYLOAD_END) == ST_BADADDR);
    assert(dispatch(&card, OP_GO, 0x40) == ST_BADADDR);
    assert(dispatch(&card, 0x1234, 0) == ST_BADOP);
    assert(dispatch(&card, OP_SET_REG_ADDR, MU_LOCAL_BASE + R_OMR0) == ST_BADADDR);
    assert(dispatch(&card, OP_SET_REG_ADDR, REG_BASE) == ST_OK);
    assert(dispatch(&card, OP_WRITE, 9) == ST_BADSTATE);
    assert(dispatch(&card, OP_REG_WRITE, 9) == ST_OK);
    assert(card.dst == REG_BASE);
    assert(dispatch(&card, OP_REG_READ, REG_BASE) == ST_OK && REG(R_OMR1) == 9);
    assert(dispatch(&card, OP_SET_ADDR, PAYLOAD_BASE) == ST_OK);
    assert(dispatch(&card, OP_REG_WRITE, 9) == ST_BADSTATE);
}
static void test_failures(void)
{
    reset(0); assert(!synchronize()); reject = 1;
    assert(expect(OP_PING, 0, ST_OK) == -1);
    reset(0); assert(!synchronize()); freeze = 1;
    assert(expect(OP_GO, PAYLOAD_BASE, ST_HANDOFF) == -1);
    assert(fake_time >= TIMEOUT_NS);
    assert(synchronize() == -1); /* unresolved pending command */
    reset(0); assert(!synchronize()); assert(!expect(OP_GO, PAYLOAD_BASE, ST_HANDOFF));
    assert(REG(R_OMR1) == PAYLOAD_MAGIC && stopped);
    assert(synchronize() == -1);
    reset(0); REG(R_OMR0) = 0xffffffffu; assert(synchronize() == -1);
}
static void test_files(void)
{
    char name[] = "/tmp/i960-load-test-XXXXXX";
    unsigned char data[513];
    int fd = mkstemp(name);
    assert(fd >= 0);
    memset(data, 0xa5, sizeof(data)); data[0] = 1; data[1] = 2; data[2] = 3;
    assert(write(fd, data, 3) == 3); close(fd);
    reset(0); assert(!synchronize()); assert(!load_file(PAYLOAD_BASE, name));
    assert(memory[PAYLOAD_BASE / 4] == 0x00030201u && payload_reads == 1);
    reset(0); corrupt = 1; assert(!synchronize()); assert(load_file(PAYLOAD_BASE, name));
    fd = open(name, O_WRONLY | O_TRUNC); assert(fd >= 0); close(fd);
    reset(0); assert(load_file(PAYLOAD_BASE, name) && consumed == 0);
    fd = open(name, O_WRONLY | O_TRUNC); assert(fd >= 0);
    assert(write(fd, data, 513) == 513); close(fd);
    reset(0); assert(load_file(PAYLOAD_BASE, name) && consumed == 0);
    fd = open(name, O_WRONLY | O_TRUNC); assert(fd >= 0);
    assert(write(fd, data, 5) == 5); close(fd);
    reset(0); assert(load_file(PAYLOAD_END - 4u, name) && consumed == 0);
    fd = open(name, O_WRONLY | O_TRUNC); assert(fd >= 0);
    assert(write(fd, data, 512) == 512); close(fd);
    reset(0); assert(!synchronize()); assert(!load_file(PAYLOAD_BASE, name));
    assert(payload_reads == 128 && card.dst == PAYLOAD_END);
    assert(load_file(PAYLOAD_BASE, "/does/not/exist"));
    /* On supported Unix hosts, fread on a directory returns a read error. */
    reset(0); assert(load_file(PAYLOAD_BASE, "/tmp") && consumed == 0);
    unlink(name);
}
static void fixture_file(const char *device, const char *name, const char *contents)
{
    char path[600];
    FILE *f;
    snprintf(path, sizeof(path), "%s/%s", device, name);
    f = fopen(path, "w"); assert(f);
    assert(fputs(contents, f) >= 0); assert(!fclose(f));
}
static void test_devices(void)
{
    char root[] = "/tmp/i960-pci-test-XXXXXX";
    char device[512], other[512], result[512], path[600];
    int fd, second;
    assert(mkdtemp(root));
    snprintf(fake_sysfs_root, sizeof(fake_sysfs_root), "%s", root);
    snprintf(device, sizeof(device), "%s/0000:37:09.1", root);
    assert(!mkdir(device, 0700));
    fixture_file(device, "vendor", "0x1069\n");
    fixture_file(device, "device", "0x0010\n");
    fixture_file(device, "resource", "ee000000 ee001fff 200\n");
    fixture_file(device, "config", "");
    assert(!device_path("0000:37:09.1", result, sizeof(result)) && !strcmp(device, result));
    assert(!device_path("0xee000000", result, sizeof(result)) && !strcmp(device, result));
    assert(device_path("0xdeadbeef", result, sizeof(result)));
    assert(unbound(device));
    snprintf(path, sizeof(path), "%s/driver", device);
    assert(!symlink("/nonexistent-driver", path));
    assert(!unbound(device)); assert(!unlink(path));
    fixture_file(device, "resource", "ee000000 ee000fff 200\n");
    assert(device_path("0000:37:09.1", result, sizeof(result))); /* BAR too small */
    fixture_file(device, "resource", "ee000000 ee001fff 100\n");
    assert(device_path("0000:37:09.1", result, sizeof(result))); /* I/O BAR */
    fixture_file(device, "resource", "ee000000 ee001fff 200\n");
    fixture_file(device, "vendor", "0x8086\n");
    assert(device_path("0000:37:09.1", result, sizeof(result)));
    fixture_file(device, "vendor", "0x1069\n");
    snprintf(other, sizeof(other), "%s/0000:38:09.1", root);
    assert(!mkdir(other, 0700));
    fixture_file(other, "vendor", "0x1069\n");
    fixture_file(other, "device", "0x0010\n");
    fixture_file(other, "resource", "ee000000 ee001fff 200\n");
    assert(device_path("0xee000000", result, sizeof(result))); /* ambiguous selector */
    assert(!device_path("0000:37:09.1", result, sizeof(result)));
    snprintf(path, sizeof(path), "%s/config", device);
    fd = open(path, O_RDONLY); second = open(path, O_RDONLY);
    assert(fd >= 0 && second >= 0);
    assert(!flock(fd, LOCK_EX | LOCK_NB));
    assert(flock(second, LOCK_EX | LOCK_NB) == -1);
    close(fd); assert(!flock(second, LOCK_EX | LOCK_NB)); close(second);
    const char *files[] = {"vendor", "device", "resource", "config"};
    for (unsigned int i = 0; i < 4; i++) {
        snprintf(path, sizeof(path), "%s/%s", device, files[i]); assert(!unlink(path));
        if (i < 3) { snprintf(path, sizeof(path), "%s/%s", other, files[i]); assert(!unlink(path)); }
    }
    assert(!rmdir(device)); assert(!rmdir(other)); assert(!rmdir(root));
}
static void test_numbers(void)
{
    uint64_t n;
    assert(!parse_number("0xffffffff", UINT32_MAX, &n) && n == UINT32_MAX);
    assert(parse_number("0x100000000", UINT32_MAX, &n));
    assert(parse_number("12junk", UINT32_MAX, &n));
    assert(parse_number("-1", UINT32_MAX, &n));
    assert(parse_number("", UINT32_MAX, &n));
    assert(parse_number("18446744073709551616", UINT64_MAX, &n));
}
int main(void)
{
    test_restart(); test_validation(); test_failures(); test_files(); test_numbers(); test_devices();
    puts("C protocol/sender tests: PASS (expected error diagnostics above)");
    return 0;
}

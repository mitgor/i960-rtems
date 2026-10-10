/* Host side of the i960 loader protocol (see mu.h).
 * Talks to the loader through the card's BAR0 window via /dev/mem.
 *
 *   sudo ./loadctl <bar0_phys> ping
 *   sudo ./loadctl <bar0_phys> status           # print OMR0 (BAR0+0x18)
 *   sudo ./loadctl <bar0_phys> read  <addr>      # OP_READ -> prints OMR1
 *   sudo ./loadctl <bar0_phys> load  <addr> FILE # SET_ADDR + stream words
 *   sudo ./loadctl <bar0_phys> go    <addr>      # jump to addr
 *
 * bar0_phys is the card's BAR0 (0xee000000 on the dev box). Requires the myrb
 * driver unbound/blacklisted so nothing else drives the card.
 *
 * Build: gcc -O2 -Wall -o loadctl loadctl.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#include "mu.h"

#define WINDOW 0x2000
#define TIMEOUT 2000000

static volatile uint32_t *bar;
static uint16_t seq;

static uint32_t rd(int off) { return bar[off / 4]; }
static void     wr(int off, uint32_t v) { bar[off / 4] = v; __sync_synchronize(); }

/* one command; returns status (low 16 of OMR0), or -1 on timeout */
static int command(uint16_t op, uint32_t arg)
{
    seq++;
    wr(R_IMR0, arg);                               /* arg first ... */
    wr(R_IMR1, ((uint32_t)seq << 16) | op);        /* ... then the seq commits it */
    for (long i = 0; i < TIMEOUT; i++) {
        uint32_t o = rd(R_OMR0);
        if ((o >> 16) == seq) return o & 0xffff;
    }
    return -1;
}

static int load_file(uint32_t addr, const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return 1; }
    if (command(OP_SET_ADDR, addr) < 0) { fprintf(stderr, "SET_ADDR timeout\n"); return 1; }
    uint32_t w; size_t n, words = 0;
    unsigned char buf[4];
    while ((n = fread(buf, 1, 4, f)) > 0) {
        if (n < 4) memset(buf + n, 0, 4 - n);      /* pad last word with zero */
        w = buf[0] | (buf[1] << 8) | (buf[2] << 16) | ((uint32_t)buf[3] << 24);
        if (command(OP_WRITE, w) < 0) { fprintf(stderr, "WRITE timeout at word %zu\n", words); return 1; }
        words++;
    }
    fclose(f);
    printf("loaded %zu words (%zu bytes) to 0x%08x\n", words, words * 4, addr);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: %s <bar0_phys> ping|status|read <a>|load <a> FILE|go <a>\n", argv[0]); return 2; }
    uint64_t phys = strtoull(argv[1], 0, 0);
    const char *cmd = argv[2];

    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd < 0) { perror("/dev/mem"); return 1; }
    bar = mmap(0, WINDOW, PROT_READ | PROT_WRITE, MAP_SHARED, fd, phys);
    if (bar == MAP_FAILED) { perror("mmap"); return 1; }

    int rc = 0;
    if (!strcmp(cmd, "status")) {
        uint32_t o = rd(R_OMR0);
        printf("OMR0 = 0x%08x  (ackseq=%u status=0x%04x)\n", o, o >> 16, o & 0xffff);
    } else if (!strcmp(cmd, "ping")) {
        int st = command(OP_PING, 0);
        printf(st < 0 ? "ping: TIMEOUT (no loader?)\n" : "ping: ack status=0x%04x\n", st);
        rc = st < 0;
    } else if (!strcmp(cmd, "read") && argc >= 4) {
        if (command(OP_READ, strtoul(argv[3], 0, 0)) < 0) { fprintf(stderr, "read timeout\n"); rc = 1; }
        else printf("[0x%08lx] = 0x%08x\n", strtoul(argv[3], 0, 0), rd(R_OMR1));
    } else if (!strcmp(cmd, "load") && argc >= 5) {
        rc = load_file(strtoul(argv[3], 0, 0), argv[4]);
    } else if (!strcmp(cmd, "go") && argc >= 4) {
        int st = command(OP_GO, strtoul(argv[3], 0, 0));
        printf(st < 0 ? "go: no ack (may have jumped already)\n" : "go: ack, jumped\n");
    } else {
        fprintf(stderr, "bad command\n"); rc = 2;
    }
    munmap((void *)bar, WINDOW);
    close(fd);
    return rc;
}

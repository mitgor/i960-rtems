/* Bounded, self-restoring MMIO byte round trip.
 *
 * The complete target range must equal ORIGINAL before the first store.  The
 * helper writes REPLACEMENT, verifies it through the mapping, restores
 * ORIGINAL on every handled post-mmap exit path, and verifies the restoration.
 * It cannot leave a payload installed intentionally.
 */
#define _FILE_OFFSET_BITS 64
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

static unsigned long long parse_u64(const char *s)
{
    char *end = NULL;
    unsigned long long value;

    errno = 0;
    value = strtoull(s, &end, 0);
    if (errno || !end || *end) {
        fprintf(stderr, "invalid number: %s\n", s);
        exit(2);
    }
    return value;
}

static uint8_t *read_file(const char *path, size_t *length)
{
    struct stat st;
    uint8_t *data;
    int fd;
    ssize_t got;

    fd = open(path, O_RDONLY);
    if (fd < 0 || fstat(fd, &st) < 0 || st.st_size <= 0 ||
        (uintmax_t)st.st_size > SIZE_MAX) {
        perror(path);
        exit(1);
    }
    *length = (size_t)st.st_size;
    data = malloc(*length);
    if (!data) {
        perror("malloc");
        exit(1);
    }
    got = read(fd, data, *length);
    if (got < 0 || (size_t)got != *length) {
        if (got < 0)
            perror(path);
        else
            fprintf(stderr, "short read: %s\n", path);
        exit(1);
    }
    close(fd);
    return data;
}

static void volatile_copy(volatile uint8_t *destination,
                          const uint8_t *source, size_t length)
{
    size_t i;

    for (i = 0; i < length; ++i)
        destination[i] = source[i];
    __sync_synchronize();
}

int main(int argc, char **argv)
{
    unsigned long long offset;
    size_t original_length, replacement_length, delta, map_length;
    uint8_t *original, *replacement;
    volatile uint8_t *target;
    long page_size;
    off_t map_offset;
    int fd, rc = 1;
    void *mapping;

    if (argc != 5) {
        fprintf(stderr, "usage: %s RESOURCE OFFSET ORIGINAL REPLACEMENT\n", argv[0]);
        return 2;
    }
    offset = parse_u64(argv[2]);
    original = read_file(argv[3], &original_length);
    replacement = read_file(argv[4], &replacement_length);
    if (original_length != replacement_length || original_length > 4096) {
        fprintf(stderr, "inputs must have equal lengths no greater than 4096\n");
        return 2;
    }
    page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) {
        perror("sysconf");
        return 1;
    }
    map_offset = (off_t)(offset & ~((unsigned long long)page_size - 1));
    delta = (size_t)(offset - (unsigned long long)map_offset);
    if (delta + original_length > (size_t)page_size) {
        fprintf(stderr, "target must fit in one system page\n");
        return 2;
    }
    map_length = delta + original_length;
    fd = open(argv[1], O_RDWR | O_SYNC);
    if (fd < 0) {
        perror(argv[1]);
        return 1;
    }
    mapping = mmap(NULL, map_length, PROT_READ | PROT_WRITE, MAP_SHARED,
                   fd, map_offset);
    if (mapping == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return 1;
    }
    target = (volatile uint8_t *)mapping + delta;
    if (memcmp((const void *)target, original, original_length)) {
        fprintf(stderr, "pre-write comparison failed; no stores issued\n");
        goto out;
    }
    volatile_copy(target, replacement, replacement_length);
    if (memcmp((const void *)target, replacement, replacement_length)) {
        fprintf(stderr, "replacement readback failed\n");
        goto restore;
    }
    rc = 0;
restore:
    volatile_copy(target, original, original_length);
    if (memcmp((const void *)target, original, original_length)) {
        fprintf(stderr, "FATAL: original-byte restoration failed\n");
        rc = 3;
    }
out:
    munmap(mapping, map_length);
    close(fd);
    free(replacement);
    free(original);
    if (!rc)
        puts("replacement-readback=pass restoration-readback=pass");
    return rc;
}

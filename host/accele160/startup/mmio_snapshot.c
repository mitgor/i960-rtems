/* Read-only snapshot helper for a sysfs PCI resource mmap.
 *
 * This deliberately has no write mode.  It is used to inspect the translated
 * half of the AcceleRAID 160 BAR without issuing MMIO stores.
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

int main(int argc, char **argv)
{
    const char *resource, *output;
    unsigned long long offset, length;
    long page_size;
    off_t map_offset;
    size_t delta, map_length;
    int input_fd, output_fd;
    void *mapping;
    ssize_t written;

    if (argc != 5) {
        fprintf(stderr, "usage: %s RESOURCE OFFSET LENGTH OUTPUT\n", argv[0]);
        return 2;
    }
    resource = argv[1];
    offset = parse_u64(argv[2]);
    length = parse_u64(argv[3]);
    output = argv[4];
    if (!length || length > SIZE_MAX || offset > (unsigned long long)INT64_MAX) {
        fprintf(stderr, "unsupported range\n");
        return 2;
    }

    page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) {
        perror("sysconf");
        return 1;
    }
    map_offset = (off_t)(offset & ~((unsigned long long)page_size - 1));
    delta = (size_t)(offset - (unsigned long long)map_offset);
    if (length > SIZE_MAX - delta) {
        fprintf(stderr, "range overflow\n");
        return 2;
    }
    map_length = delta + (size_t)length;

    input_fd = open(resource, O_RDONLY | O_SYNC);
    if (input_fd < 0) {
        perror(resource);
        return 1;
    }
    mapping = mmap(NULL, map_length, PROT_READ, MAP_SHARED, input_fd, map_offset);
    if (mapping == MAP_FAILED) {
        perror("mmap");
        close(input_fd);
        return 1;
    }
    output_fd = open(output, O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (output_fd < 0) {
        perror(output);
        munmap(mapping, map_length);
        close(input_fd);
        return 1;
    }
    written = write(output_fd, (const uint8_t *)mapping + delta, (size_t)length);
    if (written < 0 || (unsigned long long)written != length) {
        if (written < 0)
            perror("write");
        else
            fprintf(stderr, "short write: %zd\n", written);
        close(output_fd);
        munmap(mapping, map_length);
        close(input_fd);
        return 1;
    }
    if (fsync(output_fd) < 0) {
        perror("fsync");
        close(output_fd);
        munmap(mapping, map_length);
        close(input_fd);
        return 1;
    }
    close(output_fd);
    munmap(mapping, map_length);
    close(input_fd);
    return 0;
}

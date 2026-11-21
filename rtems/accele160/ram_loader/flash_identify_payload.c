/* RAM1 diagnostic, linked at 0xc0710000. It issues only read-array (FF) and
 * read-identifier (90) commands; it never unlocks, erases, or programs. */
#define FLASH_BASE 0xfef00000u
#define BLOCK 0x10000u
#define FIRST 0u
#define END 0x100000u
#define RESULT_MAGIC 0x31444953u /* SID1 */

#ifdef ACCELE160_FLASH_IDENTIFY_TEST
typedef unsigned char (*test_read_fn)(unsigned int);
typedef void (*test_write_fn)(unsigned int, unsigned char);
static test_read_fn test_read;
static test_write_fn test_write;
void flash_identify_set_io(test_read_fn read, test_write_fn write)
{
    test_read = read;
    test_write = write;
}
#define FLASH_READ(offset) test_read(offset)
#define FLASH_WRITE(offset, value) test_write(offset, value)
#else
static volatile unsigned char *flash =
    (volatile unsigned char *)(unsigned long)FLASH_BASE;
#define FLASH_READ(offset) flash[offset]
#define FLASH_WRITE(offset, value) do { \
    flash[offset] = (value); \
    __asm__ volatile("syncf" ::: "memory"); \
} while (0)
#endif

unsigned int accele160_flash_identify_main(volatile unsigned int *control)
{
    unsigned int block, locks = 0u, manufacturer, device, master;
    if (!control) return 1u;
    control[13] = 0u;
    FLASH_WRITE(0, 0xffu);
    FLASH_WRITE(0, 0x90u);
    manufacturer = FLASH_READ(0);
    device = FLASH_READ(1);
    master = FLASH_READ(3);
    for (block = FIRST; block < END; block += BLOCK)
        if (FLASH_READ(block + 2u) != 0u)
            locks |= 1u << ((block - FIRST) / BLOCK);
    FLASH_WRITE(0, 0xffu);
    control[14] = manufacturer;
    control[15] = device;
    control[16] = master;
    control[17] = locks;
    control[13] = RESULT_MAGIC; /* publish after read-array restoration */
    return manufacturer == 0x89u && device == 0xa6u &&
        master == 0u && locks == 0u ? 0u : 2u;
}

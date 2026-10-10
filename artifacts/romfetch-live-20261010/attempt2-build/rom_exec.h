/* Pinned, fixed-address live RAM-table / post-startup ROM-fetch experiment. */
#ifndef ROM_EXEC_H
#define ROM_EXEC_H
#define EXEC_TABLE_ADDRESS 0xc001f9bcu
#define EXEC_RAM_ADDRESS 0xc0fac100u
#define EXEC_FLASH_ADDRESS 0xc0fac180u
#define EXEC_REGION_SIZE 64u
#define EXEC_RAM_SIZE 24u
#define EXEC_FLASH_SIZE 48u
#define EXEC_TABLE_SIZE 4u
#define EXEC_RAM_OFFSET (EXEC_RAM_ADDRESS - STAGING_BASE)
#define EXEC_FLASH_OFFSET (EXEC_FLASH_ADDRESS - STAGING_BASE)
#define EXEC_TABLE_OFFSET (EXEC_TABLE_ADDRESS - STAGING_BASE)

static const unsigned char exec_ram_code[EXEC_RAM_SIZE] = {
  0x02,0x1e,0x90,0x65,0x7e,0x01,0x88,0x8c,0x18,0x20,0x8c,0x8a,
  0x00,0x30,0x88,0x8c,0xd0,0xba,0x04,0xc0,0x00,0x50,0x04,0x84
};
static const unsigned char exec_flash_code[EXEC_FLASH_SIZE] = {
  0x10,0x16,0x20,0x5c,0x82,0x1d,0x80,0x65,0x01,0x1e,0x80,0x5c,
  0x00,0x30,0x00,0x86,0x08,0x82,0xfc,0xfe,0x04,0x16,0x80,0x5c,
  0x02,0x1e,0x90,0x65,0x7f,0x01,0x88,0x8c,0x18,0x20,0x8c,0x8a,
  0x00,0x30,0x88,0x8c,0xd0,0xba,0x04,0xc0,0x00,0x50,0x04,0x84
};
static const unsigned char exec_ram_pointer[4] = {0x00,0xc1,0xfa,0xc0};
static const unsigned char exec_flash_pointer[4] = {0x80,0xc1,0xfa,0xc0};

static int exec_read_allowed(unsigned int count, unsigned int offset,
                             int verified, int armed)
{
    return verified && armed &&
        ((count == EXEC_TABLE_SIZE && offset == EXEC_TABLE_OFFSET) ||
         (count == EXEC_REGION_SIZE && offset == EXEC_RAM_OFFSET) ||
         (count == EXEC_REGION_SIZE && offset == EXEC_FLASH_OFFSET));
}
static int exec_upload_allowed(unsigned int count, unsigned int offset,
                               int verified, int armed)
{
    return verified && armed &&
        ((count == EXEC_TABLE_SIZE && offset == EXEC_TABLE_OFFSET) ||
         (count == EXEC_RAM_SIZE && offset == EXEC_RAM_OFFSET) ||
         (count == EXEC_FLASH_SIZE && offset == EXEC_FLASH_OFFSET));
}
#endif

#ifndef RESIDENT_LARGE_RAM_H
#define RESIDENT_LARGE_RAM_H
#define LARGE_LO 0xc0240000u
#define LARGE_BYTES (I960_OWNED_MIB*1048576u)
#define LARGE_HI (LARGE_LO+LARGE_BYTES)
#define LARGE_WORKSPACE (LARGE_LO+64u)
#define LARGE_STACKS (LARGE_LO+0x40080u)
#define LARGE_RESERVE (LARGE_LO+0x90000u)
unsigned int exclusive_large_prepare(void),exclusive_large_valid(void);
unsigned int exclusive_large_finish(void);
void exclusive_large_report(unsigned int*);
#endif

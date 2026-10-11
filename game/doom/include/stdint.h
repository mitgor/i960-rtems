/* GCC 3.3/newlib 1.11 i960 ABI: use its signed types, add unsigned C99 names. */
#ifndef DOOM_I960_STDINT_H
#define DOOM_I960_STDINT_H
#include <machine/types.h>
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef signed long long int64_t;
typedef unsigned long long uint64_t;
typedef unsigned int uintptr_t;
typedef int intptr_t;
#endif

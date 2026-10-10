#ifndef I960_LWIP_CC_H
#define I960_LWIP_CC_H
#include <stddef.h>
#ifndef I960_TARGET
#include <sys/types.h>
#include <limits.h>
#ifndef SSIZE_MAX
#define SSIZE_MAX LONG_MAX
#endif
#endif
typedef unsigned char u8_t;
typedef signed char s8_t;
typedef unsigned short u16_t;
typedef signed short s16_t;
typedef unsigned int u32_t;
typedef signed int s32_t;
typedef unsigned long long u64_t;
typedef signed long long s64_t;
typedef unsigned long mem_ptr_t;
#ifdef BYTE_ORDER
#undef BYTE_ORDER
#endif
#ifdef htons
#undef htons
#undef ntohs
#undef htonl
#undef ntohl
#endif
#define BYTE_ORDER LITTLE_ENDIAN
#define LWIP_PLATFORM_DIAG(x) do {} while(0)
void bounded_fatal(unsigned int code);
#define LWIP_PLATFORM_ASSERT(x) bounded_fatal(0x60000+__LINE__)
#define PACK_STRUCT_STRUCT __attribute__((packed))
#define PACK_STRUCT_BEGIN
#define PACK_STRUCT_END
#define PACK_STRUCT_FIELD(x) x
#endif

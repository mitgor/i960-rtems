/* Compile-time assumptions, emitted sizes; never loaded on the card. */
#include <stdint.h>
#include <stddef.h>
typedef char require_int32[(sizeof(int)==4)?1:-1];
typedef char require_pointer32[(sizeof(void*)==4)?1:-1];
typedef char require_i64[(sizeof(int64_t)==8)?1:-1];
typedef char require_u64[(sizeof(uint64_t)==8)?1:-1];
char abi_int[sizeof(int)],abi_long[sizeof(long)],abi_pointer[sizeof(void*)];
char abi_size_t[sizeof(size_t)],abi_double[sizeof(double)],abi_i64[sizeof(int64_t)];
struct layout {char c;void*p;int64_t wide;};
char abi_layout[sizeof(struct layout)];
char abi_wide_offset[offsetof(struct layout,wide)];

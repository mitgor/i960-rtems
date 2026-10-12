#ifndef DOOM_OWNED_API_H
#define DOOM_OWNED_API_H
#include "../entry/api.h"
#define DOOM_OWNED_MAGIC 0x3252444fu
#define DOOM_OWNED_VERSION 0x00020000u
#define DOOM_OWNED_FEATURES 7u
struct doom_runtime_owned {
 struct doom_runtime_v1 io;
 unsigned magic,version,bytes,features;
 unsigned (*owner)(void);
 int (*wait_ms)(unsigned);
 unsigned (*stopping)(void);
 unsigned reserved;
};
#ifdef I960_TARGET
typedef char doom_owned_size_check[(sizeof(struct doom_runtime_owned)==128)?1:-1];
#endif
unsigned owned_entry(const struct doom_runtime_owned*);
#endif

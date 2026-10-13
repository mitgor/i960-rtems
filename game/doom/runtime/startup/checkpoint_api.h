#ifndef DOOM_CHECKPOINT_API_H
#define DOOM_CHECKPOINT_API_H
#include "../owned/api.h"
#define DOOM_CHECKPOINT_MAGIC 0x31504344u
#define DOOM_CHECKPOINT_VERSION 0x00020001u
#define DOOM_CHECKPOINT_FEATURES 15u
#define DOOM_CHECKPOINT_CAPACITY 512u
struct doom_runtime_checkpoint {
 struct doom_runtime_owned base;
 int (*mark)(unsigned,unsigned,unsigned,unsigned);
 unsigned reserved[3];
};
#endif

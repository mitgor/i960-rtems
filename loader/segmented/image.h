#ifndef SEG_IMAGE_H
#define SEG_IMAGE_H
#include "arena.h"
#define SEG_MAX 8u
#define SEG_CHUNK 1024u
#define SEG_ABI 1u
#define SEG_RX 1u
#define SEG_RW 2u
#define SEG_EMPTY 0u
#define SEG_LOADING 1u
#define SEG_VERIFYING 2u
#define SEG_READY 3u
#define SEG_RUNNING 4u
#define SEG_CANCELLING 5u
#define SEG_QUARANTINED 6u
/* Relative, position-independent images only. No relocations or imports yet. */
struct segment {unsigned int offset,file_bytes,memory_bytes,flags,crc32;};
struct manifest {unsigned int abi,count,entry;struct segment segment[SEG_MAX];};
struct seg_image {
 struct arena *arena;struct manifest manifest;unsigned char *base;
 unsigned int handle,state,received[SEG_MAX],current,position,crc;
};
typedef int (*seg_cache_sync)(void *,unsigned int);
unsigned int seg_crc32(unsigned int,const void *,unsigned int);
void seg_init(struct seg_image *);
int seg_begin(struct seg_image *,struct arena *,const struct manifest *);
int seg_write(struct seg_image *,unsigned int,unsigned int,const void *,unsigned int);
/* One <=1024-byte checksum/zero step. 1=more, 2=ready, 0=error. */
int seg_prepare(struct seg_image *,seg_cache_sync);
void *seg_start(struct seg_image *);
int seg_complete(struct seg_image *); /* only after all execution contexts drain */
int seg_cancel(struct seg_image *);
void seg_uncertain(struct seg_image *); /* permanently retain storage */
#endif

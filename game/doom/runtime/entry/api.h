#ifndef DOOM_RUNTIME_API_H
#define DOOM_RUNTIME_API_H
#define DOOM_API_MAGIC 0x31545244u
#define DOOM_API_BATCH_VERSION 0x00010001u
#define DOOM_API_BATCH_FEATURES 15u
#define DOOM_API_VERSION 0x00010000u
#define DOOM_API_FEATURES 7u
#define DOOM_WAD_CHUNK 512u
/* Native i960 ABI, not a serialized C structure. Wire packets use u32 words.
 * 32-bit little endian, function pointer offsets 72/76/80/84, 96 bytes. */
struct doom_runtime_v1 {
 unsigned int magic,version,bytes,features,pointer_bytes,little_endian;
 unsigned int arena_bytes,max_read,file_id,file_bytes,sha256[8];
 void *(*allocate)(unsigned int);
 void (*release)(void *);
 unsigned int (*ticks_ms)(void);
 int (*read)(unsigned int,unsigned int,void*,unsigned int);
 unsigned int reserved[2];
};
#ifdef I960_TARGET
typedef char doom_api_size_check[(sizeof(struct doom_runtime_v1)==96&&sizeof(void*)==4)?1:-1];
#endif
unsigned int doom_runtime_probe(const struct doom_runtime_v1*);
#endif

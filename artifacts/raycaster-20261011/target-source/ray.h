#ifndef MYLEX_RAY_H
#define MYLEX_RAY_H
#define RAY_MAGIC 0x31594152u
#define RAY_W 80
#define RAY_H 60
#define RAY_PIXELS 4800u
#define RAY_HEADER 64u
#define RAY_REPLY 4864u
/* Eight LE32 request words: magic, op, columns, keys, pixels, kind, reps, reserved.
 * op 0 reset; 1 render bounded columns; 2 snapshot; 3 benchmark.
 * keys bits: forward/back/left/right. pixels 0/1 selects header/full reply.
 * Benchmark kinds 0 empty, 1 memcpy aligned, 2 memcpy unaligned, 3 memset,
 * 4 memmove overlap, 5 memcmp, 6 strlen, 7 RTEMS handoffs, 8 RTEMS ticks. */
unsigned int ray_size(void);
unsigned int ray_request(void*,const unsigned char*,unsigned int,unsigned char*,unsigned int);
#endif

#ifndef I960_CHIP8_H
#define I960_CHIP8_H
/* No libc, floating point or host-sized integer fields in the interpreter. */
typedef unsigned char c8_u8;
typedef unsigned short c8_u16;
typedef unsigned int c8_u32;
#define C8_MAX_CYCLES 1000u
#define C8_FRAME_BYTES 256u
#define C8_REPLY_BYTES 304u
#define C8_MAGIC 0x31473843u /* C8G1, little endian */
enum { C8_OK, C8_WAIT, C8_OPCODE, C8_MEMORY, C8_STACK };
struct chip8 {
 c8_u8 ram[4096], frame[C8_FRAME_BYTES], v[16];
 c8_u16 stack[16], pc, index, keys;
 c8_u8 sp, delay, sound, fault;
 c8_u32 rng, total;
};
unsigned int c8_size(void);
void c8_reset(struct chip8 *s, unsigned int seed);
unsigned int c8_run(struct chip8 *s, unsigned int cycles, unsigned int ticks,
                    unsigned int keys, unsigned int *executed);
/* Request: six LE32 words magic/op/cycles/keys/timer_ticks/seed + ROM for op=0.
 * op=0 reset+load, op=1 bounded step. Invalid requests leave state unchanged.
 * Reply: eight LE32 words magic/status/executed/total/pc/I/delay/sound,
 * 16 V registers, then 256 bytes of row-major MSB-first 64x32 pixels.
 * Return 0 success (including guest faults), 1 bad request, 2 short capacity. */
unsigned int c8_request(struct chip8 *s, const c8_u8 *in, unsigned int n,
                       c8_u8 *out, unsigned int capacity);
#endif

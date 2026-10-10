#ifndef IO_H
#define IO_H
/* Shared memory-mapped I/O contract between the i960 game and the host/emulator.
   Flat little-endian RAM; this struct lives at a fixed address both sides know. */

typedef unsigned char  u8;
typedef unsigned int   u32;
typedef int            i32;

#define IO_BASE 0x00090000u

#define ROWS 24
#define COLS 80

struct io {
    volatile u8  fb[ROWS][COLS]; /* ASCII framebuffer, host renders this            */
    volatile i32 doorbell;       /* game writes 1 -> host services I/O, clears it   */
    volatile i32 key;            /* host writes last key byte (0 = none)            */
    volatile i32 frame;          /* host-maintained monotonic frame counter         */
    volatile i32 halt;           /* game writes 1 -> emulator stops                 */
};

#define IO ((struct io *)IO_BASE)

/* keys the host passes through */
#define K_LEFT   'a'
#define K_RIGHT  'd'
#define K_ROT    'w'
#define K_DROP   's'
#define K_QUIT   'q'

#endif

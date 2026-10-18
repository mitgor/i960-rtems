#ifndef CHIP8_PLAYER_H
#define CHIP8_PLAYER_H
#include "../chip8.h"
#define C8_PACKET_BYTES 512u
#define C8_PLAYER_MAGIC 0x31503843u
struct c8_player {
 struct chip8 guest;
 unsigned last,cycle_carry,tick_carry,frame_carry,hz,generation;
 unsigned held,pressed,input_seen,status,executed,dropped_ms;
 unsigned start,updates,trace_count,trace[8][4];
};
unsigned c8_player_size(void);
unsigned c8_player_init(struct c8_player*,const unsigned char*,unsigned,unsigned,unsigned,unsigned);
unsigned c8_player_key(struct c8_player*,unsigned);
/* Real elapsed time; <=250ms catch-up, <=1000 instructions/update, no libc.
 * Brief down/up transitions latch for one execution slice, not forever. */
unsigned c8_player_update(struct c8_player*,unsigned,unsigned char*);
#endif

#ifndef TETRIS_H
#define TETRIS_H
#include "io.h"
#define TETRIS_STATE_BYTES 240u
#define TETRIS_REQUEST_BYTES 256u
#define TETRIS_RESPONSE_BYTES (TETRIS_STATE_BYTES+ROWS*COLS)
#define TETRIS_MAX_TICKS 20u
/* phase 0 running, 1 game over, 2 quit; ticks are 50 ms host simulation ticks. */
struct tetris_state {
    u32 version,rng,score,piece,rotation;
    i32 x,y;
    u32 tick,phase,reserved;
    u8 board[20][10];
};
void tetris_init(struct tetris_state *s,u32 seed);
int tetris_valid(const struct tetris_state *s);
int tetris_step(struct tetris_state *s,u32 key,u32 ticks);
void tetris_render(const struct tetris_state *s,u8 *frame);
void tetris_encode(const struct tetris_state *s,u8 *out);
void tetris_decode(struct tetris_state *s,const u8 *in);
/* request: op (0 step, 1 init/restart), seed, key, ticks, 240-byte state.
 * response: 240-byte state followed by 1920 framebuffer cells.
 * status 0 success, 1 invalid input, 2 insufficient output capacity. */
unsigned tetris_request(const u8 *in,unsigned length,u8 *out,unsigned capacity);
#endif

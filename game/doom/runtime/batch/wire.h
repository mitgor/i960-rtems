#ifndef DOOM_BATCH_WIRE_H
#define DOOM_BATCH_WIRE_H
#include "../wad.h"
#define DOOM_BATCH_MAGIC 0x31424157u
#define DOOM_BATCH_BYTES 4096u
/* One logical request, ordered 512-byte fragments. Header word 7 binds every
 * fragment to the original wanted length. No destination pointer on wire. */
struct doom_batch {
 unsigned state,sequence,offset,wanted,file_bytes,fragments,words,expected;
 unsigned accepted,rejected,cancelled,frozen[8];
 unsigned (*inbox)[136]; /* caller-owned staging, pinned for the whole request */
};
int doom_batch_begin(struct doom_batch*,unsigned,unsigned,unsigned);
unsigned doom_batch_control(struct doom_batch*,unsigned,unsigned,unsigned,unsigned);
int doom_batch_claim(struct doom_batch*);
int doom_batch_copy(struct doom_batch*,void*,unsigned);
void doom_batch_cancel(struct doom_batch*);
#endif

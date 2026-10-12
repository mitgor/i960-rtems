#ifndef DOOM_WAD_H
#define DOOM_WAD_H
#define WAD_WORDS 136u
#define WAD_MAGIC 0x31444157u
enum {WAD_IDLE,WAD_REQUEST,WAD_READY,WAD_CONSUMING};
/* Caller serializes control/begin/claim/cancel. After claim, the response is
 * immutable until finish: CRC and payload work may run with interrupts enabled.
 * No host address or destination pointer appears on the wire. */
struct doom_wad {
 unsigned int state,sequence,file,offset,wanted,file_bytes,words,expected;
 unsigned int inbox[WAD_WORDS],frozen[8],accepted,rejected,cancelled;
};
int doom_wad_begin(struct doom_wad*,unsigned int,unsigned int,unsigned int,unsigned int);
unsigned int doom_wad_control(struct doom_wad*,unsigned int,unsigned int,unsigned int,unsigned int);
int doom_wad_claim(struct doom_wad*);
int doom_wad_copy(struct doom_wad*,void*,unsigned int);
void doom_wad_cancel(struct doom_wad*);
#endif

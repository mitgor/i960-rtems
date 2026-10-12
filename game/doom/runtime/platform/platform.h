#ifndef DOOM_PLATFORM_H
#define DOOM_PLATFORM_H
#include "../entry/api.h"
#define DPL_LOG 4096u
#define DPL_KEYS 32u
struct doom_platform_stats {unsigned log_bytes,log_dropped,frames,frame_hash,palette_hash,sleeps,key_events,exit_code,exited,live_bytes,peak_bytes,blocks,peak_blocks,stdio_reads;};
/* One application owner, one immutable IWAD. This bind does not grant a task
 * or STOP authority; a later engine admission must supply that contract. */
int doom_platform_bind(const struct doom_runtime_v1*,const char*);
const struct doom_platform_stats *doom_platform_stats(void);
unsigned doom_platform_log(void*,unsigned);
int doom_platform_key(int,unsigned char);
int doom_platform_call(void (*)(void));
int doom_platform_finish(void);
int doom_platform_frame(void*,unsigned,void*,unsigned);
#endif

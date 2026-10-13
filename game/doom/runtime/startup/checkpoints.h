#ifndef DOOM_STARTUP_CHECKPOINTS_H
#define DOOM_STARTUP_CHECKPOINTS_H
void doom_platform_mark(unsigned,unsigned,unsigned,unsigned);
static unsigned doom_checkpoint_hash(const void *v,unsigned n){const unsigned char*p=v;unsigned h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;}
/* Hash scalar fields only: pointers and structure padding are ABI-dependent. */
static unsigned doom_checkpoint_mix(unsigned h,unsigned v){unsigned i;for(i=0;i<4;i++){h=(h^(v&255))*16777619u;v>>=8;}return h;}
#endif

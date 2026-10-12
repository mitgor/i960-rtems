/* Included only by profile.c for the allocator integration experiment. */
#include "libc.h"
static unsigned char runtime_memory[8*1048576] __attribute__((aligned(16)));
static struct arena runtime_arena;
static struct doom_heap runtime_heap;
static int runtime_locked;
static unsigned int runtime_image;
static int runtime_enter(void*p){(void)p;if(runtime_locked)abort();runtime_locked=1;return 1;}
static void runtime_leave(void*p){(void)p;if(!runtime_locked)abort();runtime_locked=0;}
static int runtime_progress(void*p){(void)p;if(runtime_locked)abort();return 1;}
static void runtime_fatal(unsigned int code){fprintf(stderr,"Doom arena fatal %u\n",code);abort();}
static void runtime_finish(void){
 if(!doom_heap_stop(&runtime_heap)||!doom_heap_drain(&runtime_heap)||runtime_heap.live||runtime_heap.blocks||!arena_unpin(&runtime_arena,runtime_image)||!arena_release(&runtime_arena,runtime_image))abort();
 fprintf(stderr,"Doom arena drained; peak=%u blocks=%u; reserved engine=655360\n",runtime_heap.peak,runtime_heap.peak_blocks);
}
static void runtime_init(void){
 struct doom_heap_hooks hooks={runtime_enter,runtime_leave,runtime_progress,0};
 if(!arena_init(&runtime_arena,runtime_memory,sizeof runtime_memory))abort();
 runtime_image=arena_alloc(&runtime_arena,655360);if(!runtime_image||!arena_pin(&runtime_arena,runtime_image))abort();
 if(!doom_heap_init(&runtime_heap,&runtime_arena,&hooks)||!doom_libc_bind(&runtime_heap,runtime_fatal))abort();
 atexit(runtime_finish);
}
#define __real_malloc doom_malloc
#define __real_calloc doom_calloc
#define __real_realloc doom_realloc
#define __real_free doom_free

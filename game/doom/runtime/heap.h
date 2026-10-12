#ifndef DOOM_RUNTIME_HEAP_H
#define DOOM_RUNTIME_HEAP_H
#include "../../../loader/segmented/arena.h"
/* The arena is already admitted/initialized. These hooks serialize ALL arena
 * users, refuse ISR/wrong task, and never mask interrupts across bulk work.
 * progress runs outside the lock; return zero to cancel the current operation.
 * Caller storage is initially zero and must not be reset while live. */
struct doom_heap_hooks {
 int (*enter)(void *); void (*leave)(void *); int (*progress)(void *);
 void *cookie;
};
struct doom_allocation { void *pointer; unsigned int handle,bytes,busy,loan; };
struct doom_heap {
 struct arena *arena;
 struct doom_heap_hooks hooks;
 struct doom_allocation slots[ARENA_SLOTS];
 unsigned int initialized,stopping,fault,error,live,peak,blocks,peak_blocks,busy,loan_sequence;
};
enum { DH_OK, DH_OOM, DH_INVALID, DH_CORRUPT, DH_STOP, DH_BUSY, DH_DENIED };
int doom_heap_init(struct doom_heap *,struct arena *,const struct doom_heap_hooks *);
void *doom_heap_malloc(struct doom_heap *,unsigned int);
void *doom_heap_calloc(struct doom_heap *,unsigned int,unsigned int);
void *doom_heap_realloc(struct doom_heap *,void *,unsigned int);
char *doom_heap_strdup(struct doom_heap *,const char *);
int doom_heap_free(struct doom_heap *,void *);
int doom_heap_stop(struct doom_heap *);
/* Only AFTER every application/external consumer and IRQ context has drained.
 * Busy operations or additional arena pins refuse reclamation; faults retain. */
int doom_heap_drain(struct doom_heap *);
/* One outstanding loan per allocation. Non-reused namespace token, refusing
 * wrap. Return only after the borrower drains; a stale token cannot unpin. */
unsigned int doom_heap_borrow(struct doom_heap *,void *,unsigned int);
int doom_heap_return(struct doom_heap *,void *,unsigned int);
#endif

#ifndef SEG_ARENA_H
#define SEG_ARENA_H
/* Caller serializes operations. Metadata must live outside the admitted arena.
 * No ISR use; cancellation does not imply completion of a pinned consumer. */
#define ARENA_SLOTS 128u
#define ARENA_GUARD 16u
struct arena_slot { unsigned int offset, bytes, span, generation, pins, cancelled; };
struct arena { unsigned char *base; unsigned int bytes, poisoned; struct arena_slot slot[ARENA_SLOTS]; };
int arena_init(struct arena *, void *, unsigned int);
int arena_valid(struct arena *);
unsigned int arena_alloc(struct arena *, unsigned int);
void *arena_pin(struct arena *, unsigned int);
int arena_unpin(struct arena *, unsigned int);
int arena_cancel(struct arena *, unsigned int);
int arena_release(struct arena *, unsigned int);
#endif

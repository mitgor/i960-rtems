#ifndef RESIDENT_GENERAL_HEAP_H
#define RESIDENT_GENERAL_HEAP_H
#define RESIDENT_HEAP_BASE 0xc022ee80u
#define RESIDENT_HEAP_BYTES 69952u
#ifdef I960_QUEUE_RECLAIM
#define FALLBACK_HEAP_BYTES 101872u
#define HEAP_MAX_BYTES FALLBACK_HEAP_BYTES
#define HEAP_TOTAL_BYTES (RESIDENT_HEAP_BYTES+FALLBACK_HEAP_BYTES)
unsigned int resident_fallback_base(void),resident_fallback_valid(void);
#else
#define HEAP_MAX_BYTES RESIDENT_HEAP_BYTES
#define HEAP_TOTAL_BYTES RESIDENT_HEAP_BYTES
#endif
void *resident_malloc(unsigned int);
void *resident_calloc(unsigned int,unsigned int);
void *resident_realloc(void*,unsigned int);
unsigned int resident_free(void*);
unsigned int resident_heap_init(void),resident_heap_valid(void);
void resident_heap_step(unsigned int,unsigned int),resident_heap_drain(unsigned int);
void resident_heap_check(void);
void resident_heap_report(unsigned int*),resident_heap_inject(void);
#ifdef I960_HEAP_SHARED
unsigned int resident_shared_new(unsigned int,unsigned int),resident_shared_acquire(unsigned int,unsigned int);
void*resident_shared_pin(unsigned int,unsigned int);
unsigned int resident_shared_unpin(unsigned int,unsigned int),resident_shared_cancel(unsigned int);
unsigned int resident_shared_ack(unsigned int,unsigned int),resident_shared_resume(unsigned int);
void resident_heap_irq_sample(void),resident_heap_diagnostics(unsigned int*);
#endif
#endif

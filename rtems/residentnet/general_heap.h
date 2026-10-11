#ifndef RESIDENT_GENERAL_HEAP_H
#define RESIDENT_GENERAL_HEAP_H
#define RESIDENT_HEAP_BASE 0xc022ee80u
#define RESIDENT_HEAP_BYTES 69952u
void *resident_malloc(unsigned int);
void *resident_calloc(unsigned int,unsigned int);
void *resident_realloc(void*,unsigned int);
unsigned int resident_free(void*);
unsigned int resident_heap_init(void),resident_heap_valid(void);
void resident_heap_step(unsigned int,unsigned int),resident_heap_drain(unsigned int);
void resident_heap_check(void);
void resident_heap_report(unsigned int*),resident_heap_inject(void);
#endif

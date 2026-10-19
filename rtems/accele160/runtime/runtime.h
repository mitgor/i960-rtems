#ifndef ACCELE_RUNTIME_H
#define ACCELE_RUNTIME_H
#include "image.h"
#define AR_BOARD 0x01601077u
#define AR_ABI 1u
#define AR_BYTES (512u*1024u)
#define AR_HEAP_BYTES (128u*1024u)
#define AR_MODULE_BYTES (AR_BYTES-AR_HEAP_BYTES)
/* The caller is the sole RTEMS task owner. No allocator operation from IRQs.
 * Parent remains pinned until module execution and every heap pin drain. */
struct ar_runtime {
 struct arena *parent,modules,heap;
 struct seg_image image;
 unsigned int reservation,epoch,busy,poisoned,calls;
};
void ar_init(struct ar_runtime *,unsigned int);
int ar_reserve(struct ar_runtime *,struct arena *);
int ar_begin(struct ar_runtime *,unsigned int,unsigned int,unsigned long,const struct manifest *);
int ar_close(struct ar_runtime *);
unsigned int ar_alloc(struct ar_runtime *,unsigned int);
void *ar_pin(struct ar_runtime *,unsigned int);
int ar_unpin(struct ar_runtime *,unsigned int);
int ar_cancel(struct ar_runtime *,unsigned int);
int ar_release(struct ar_runtime *,unsigned int);
unsigned int ar_heap_proof(struct ar_runtime *);
int ar_valid(struct ar_runtime *);
#endif

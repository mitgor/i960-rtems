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
/* Exclusive idle-zone loan. Parent pin remains until every child drains.
 * Owner cancellation revokes allocation/pin; completion still permits unpin.
 * Caller serializes, and must prove the previous engine will not restart. */
struct ar_loan {
 struct arena *parent,heap;
 unsigned int handle,owner,cancelled,poisoned,proof_handle,offset,phase;
 unsigned char *proof;
};
void ar_loan_init(struct ar_loan *);
int ar_loan_attach(struct ar_loan *,struct arena *,unsigned int,unsigned int,unsigned int);
unsigned int ar_loan_alloc(struct ar_loan *,unsigned int,unsigned int);
void *ar_loan_pin(struct ar_loan *,unsigned int,unsigned int);
int ar_loan_unpin(struct ar_loan *,unsigned int,unsigned int);
int ar_loan_free(struct ar_loan *,unsigned int,unsigned int);
int ar_loan_cancel(struct ar_loan *,unsigned int);
int ar_loan_release(struct ar_loan *,unsigned int);
unsigned int ar_loan_proof(struct ar_loan *);
#endif

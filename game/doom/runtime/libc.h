#ifndef DOOM_ARENA_LIBC_H
#define DOOM_ARENA_LIBC_H
#include <stddef.h>
#include "heap.h"
/* One Doom application per resident lifetime. No process-global malloc override.
 * Bind only in the owning task before application entry; no ISR use. */
int doom_libc_bind(struct doom_heap *,void (*fatal)(unsigned int));
void *doom_malloc(size_t);
void *doom_calloc(size_t,size_t);
void *doom_realloc(void *,size_t);
void doom_free(void *);
char *doom_strdup(const char *);
#endif

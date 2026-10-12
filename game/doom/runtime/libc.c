#include "libc.h"
static struct doom_heap *bound;
static void (*failure)(unsigned int);
int doom_libc_bind(struct doom_heap*h,void(*fatal)(unsigned int)) {
 if(bound||!h||!h->initialized||!fatal)return 0;bound=h;failure=fatal;return 1;
}
void *doom_malloc(size_t n){if(!bound||n>0xffffffffu)return 0;return doom_heap_malloc(bound,(unsigned int)n);}
void *doom_calloc(size_t n,size_t s){if(!bound||n>0xffffffffu||s>0xffffffffu)return 0;return doom_heap_calloc(bound,(unsigned int)n,(unsigned int)s);}
void *doom_realloc(void*p,size_t n){if(!bound||n>0xffffffffu)return 0;return doom_heap_realloc(bound,p,(unsigned int)n);}
void doom_free(void*p){if(!p)return;if(!bound)return; /* application must bind before entry */
 if(!doom_heap_free(bound,p)){failure(bound->error);}}
char *doom_strdup(const char*s){if(!bound)return 0;return doom_heap_strdup(bound,s);}

#ifndef DOOM_HEAP_SHARED_H
#define DOOM_HEAP_SHARED_H
#ifdef I960_DOOM_SHARED
struct arena;
struct doom_heap;
void doom_shared_owner(struct doom_heap*);
void doom_shared_init(void);
int doom_shared_enter(void *);
void doom_shared_leave(void *);
void doom_shared_quiesce(unsigned int);
void doom_shared_peer_step(void);
void doom_shared_start(struct arena *);
void doom_shared_resize(void);
void doom_shared_wait(unsigned int);
unsigned int doom_shared_finish(void);
unsigned int doom_shared_report(unsigned int);
void doom_shared_yield(void);
#ifdef I960_WAD_POLL
void doom_shared_service(void);
#endif
unsigned int doom_shared_application_owner(void);
#endif
#endif

#ifdef I960_EXTRA_RAM
static unsigned int queue_slots=68;
#define NETWORK_QUEUE_SLOTS queue_slots
#define NETWORK_EXTERNAL_QUEUE 1
#define NETWORK_LENGTH_SLOTS 128
#elif defined(I960_FAULT_OWNER)
#define NETWORK_QUEUE_SLOTS 68
#else
#define NETWORK_QUEUE_SLOTS 72
#endif
#define NETWORK_FRAME_BYTES 1500
#define RESIDENT_QUEUE_STATS 1
#include "../net/network.c"

#ifdef I960_EXTRA_RAM
#define QUEUE_ADDRESS(a) ((void*)(a))
#include "queue_extend.h"
#endif

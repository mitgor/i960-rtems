#include "../entry/api.h"
static unsigned seed=0x49393630u;
static unsigned counts[32];
static unsigned *selected=counts+3;
static unsigned mix(unsigned n){return (n*33)^seed;}
unsigned relocated_entry(const struct doom_runtime_v1*a){unsigned i;void*p;
 if(!a||a->magic!=DOOM_API_MAGIC)return 1;
 p=a->allocate(512);if(!p)return 2;
 for(i=0;i<32;i++)counts[i]=mix(i);
 i=selected[2];a->release(p);return i;
}

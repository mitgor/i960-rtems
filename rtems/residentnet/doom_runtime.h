#ifndef RESIDENT_DOOM_RUNTIME_H
#define RESIDENT_DOOM_RUNTIME_H
#include "../../game/doom/runtime/entry/api.h"
#ifdef I960_DOOM_RUNTIME
unsigned int doom_runtime_bind(const unsigned int*,unsigned int);
const struct doom_runtime_v1 *doom_runtime_api(void);
unsigned int doom_runtime_control(unsigned int,unsigned int,unsigned int,unsigned int);
unsigned int doom_runtime_finish(void),doom_runtime_report(unsigned int);
#endif
#endif

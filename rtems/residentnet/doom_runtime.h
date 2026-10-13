#ifndef RESIDENT_DOOM_RUNTIME_H
#define RESIDENT_DOOM_RUNTIME_H
#include "../../game/doom/runtime/entry/api.h"
#ifdef I960_DOOM_RUNTIME
unsigned int doom_runtime_bind(const unsigned int*,unsigned int);
const struct doom_runtime_v1 *doom_runtime_api(void);
unsigned int doom_runtime_control(unsigned int,unsigned int,unsigned int,unsigned int);
unsigned int doom_runtime_finish(void),doom_runtime_report(unsigned int);
#ifdef I960_WAD_BATCH
const struct doom_runtime_v1 *doom_runtime_batch_api(unsigned limit);
unsigned doom_runtime_batch_report(unsigned);
#endif
#ifdef I960_DOOM_OWNED
#include "../../game/doom/runtime/owned/api.h"
const struct doom_runtime_owned *doom_runtime_owned_api(void);
unsigned doom_runtime_owned_begin(void),doom_runtime_owned_end(void);
unsigned doom_runtime_owned_control(unsigned,unsigned,unsigned,unsigned);
#endif
#endif
#endif

#ifdef I960_WAD_BATCH
const struct doom_runtime_owned *doom_runtime_owned_batch_api(void);
#endif

#ifdef I960_DOOM_CHECKPOINTS
unsigned doom_runtime_checkpoint_control(unsigned,unsigned,unsigned,unsigned);
#endif

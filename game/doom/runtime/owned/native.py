"""Native support for the owned proof, modeling processor priority explicitly."""
def prefix(source):
 source='#define I960_DOOM_OWNED 1\n#define OWNED_NATIVE_TEST 1\n'+source
 source=source.replace('static _Thread_local unsigned int identity;', 'static _Thread_local unsigned int identity;\nstatic _Thread_local unsigned native_priority=20;\nunsigned owned_test_mask(unsigned n){unsigned old=native_priority;native_priority=n;return old;}')
 source=source.replace('return identity;', 'return identity==2&&native_priority!=20?0:identity;')
 return source.replace('#include "doom_runtime.c"','#include "doom_runtime.c"\n#include "../../game/doom/runtime/owned/probe.c"')

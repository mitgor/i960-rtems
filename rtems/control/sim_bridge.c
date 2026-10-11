/* Native-process demo only. These barriers are NOT an i960/PCI implementation. */
#include <stdatomic.h>
#include "control.h"
void sim_barrier(void *unused){(void)unused;atomic_thread_fence(memory_order_seq_cst);}
void sim_store(volatile ctl_u32 *p,ctl_u32 v){atomic_store_explicit((_Atomic ctl_u32*)p,v,memory_order_seq_cst);}
ctl_u32 sim_load(volatile ctl_u32 *p){return atomic_load_explicit((_Atomic ctl_u32*)p,memory_order_seq_cst);}

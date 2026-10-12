#ifdef I960_DOOM_OWNED
#include "../../game/doom/runtime/owned/api.h"
static struct doom_runtime_owned owned_api;
static unsigned owned_yields,owned_completed,owned_refused,owned_observed;
static unsigned owned_owner(void){return owned_running&&doom_shared_application_owner();}
static unsigned owned_stopping(void){return !owned_owner()||upload_stopping()||owned_stop_requested;}
static void *owned_allocate(unsigned n){return owned_owner()&&!owned_stopping()?allocate(n):0;}
static void owned_release(void*p){if(!owned_owner()){exclusive_abort();return;}doom_free(p);}
static unsigned owned_clock(void){return owned_owner()?milliseconds():0;}
static int owned_read(unsigned f,unsigned o,void*p,unsigned n){if(!owned_owner()||owned_stopping())return -1;return read_wad(f,o,p,n);}
static int owned_wait(unsigned ms){unsigned i,n;if(!owned_owner())return -1;if(ms>1000){owned_refused++;return -1;}
 n=(ms+9)/10;if(!n)n=1;
 for(i=0;i<n;i++){if(owned_stopping())return -1;doom_shared_yield();if(!owned_owner()){exclusive_abort();return -1;}owned_yields++;}
 return owned_stopping()?-1:0;
}
static void owned_bind(void){unsigned i;for(i=0;i<sizeof(api);i++)((unsigned char*)&owned_api.io)[i]=((unsigned char*)&api)[i];
 owned_api.io.allocate=owned_allocate;owned_api.io.release=owned_release;owned_api.io.ticks_ms=owned_clock;owned_api.io.read=owned_read;
 owned_api.magic=DOOM_OWNED_MAGIC;owned_api.version=DOOM_OWNED_VERSION;owned_api.bytes=sizeof(owned_api);owned_api.features=DOOM_OWNED_FEATURES;owned_api.owner=owned_owner;owned_api.wait_ms=owned_wait;owned_api.stopping=owned_stopping;owned_api.reserved=0;
}
const struct doom_runtime_owned *doom_runtime_owned_api(void){return bound?&owned_api:0;}
unsigned doom_runtime_owned_begin(void){unsigned saved;if(!bound||!doom_shared_application_owner()||owned_running||leases||wad.state!=WAD_IDLE)return 0;
 saved=runtime_lock();if(owned_generation==~0u){runtime_unlock(saved);return 0;}owned_generation++;owned_stop_requested=0;owned_running=1;runtime_unlock(saved);return 1;
}
unsigned doom_runtime_owned_end(void){unsigned saved;if(!owned_owner()||leases||wad.state!=WAD_IDLE)return 0;
 saved=runtime_lock();if(owned_stop_requested||upload_stopping())owned_observed++;owned_running=0;owned_completed++;runtime_unlock(saved);return 1;
}
unsigned doom_runtime_owned_control(unsigned op,unsigned index,unsigned value,unsigned running){static unsigned frozen[8];
 if(op==0x7b){if(index||value)return ~0u;frozen[0]=DOOM_OWNED_MAGIC;frozen[1]=owned_generation;frozen[2]=owned_running;frozen[3]=owned_stop_requested;frozen[4]=owned_yields;frozen[5]=owned_completed;frozen[6]=owned_refused;frozen[7]=owned_observed;return 0;}
 if(op==0x7c)return index<8&&!value?frozen[index]:~0u;
 if(op!=0x7a||index||!running||upload_stopping()||!owned_running||!value||value!=owned_generation)return ~0u;
 owned_stop_requested=1;return 0;
}
#endif

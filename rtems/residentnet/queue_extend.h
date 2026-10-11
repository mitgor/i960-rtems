/* Only before worker execution; initial IPv6 setup can have queued frames.
 * The fallback becomes reusable only after the irreversible external handoff. */
unsigned int resident_queue_extend(unsigned int base){unsigned int i;
 if(base!=0xc0200040u||queue_slots!=68||frames!=internal_frames||head||queued>68||tail!=queued%68)return 1;
 for(i=0;i<queued;i++)if(lengths[i]>NETWORK_FRAME_BYTES)return 1;
 for(i=0;i<queued;i++)memcpy(QUEUE_ADDRESS(base+i*NETWORK_FRAME_BYTES),frames[i],lengths[i]);
 frames=QUEUE_ADDRESS(base);queue_slots=128;tail=queued;
 return 0;
}

unsigned int resident_queue_external_valid(void){
 return frames==QUEUE_ADDRESS(0xc0200040u)&&queue_slots==128&&head<128&&tail<128&&queued<=128;
}

#ifdef I960_QUEUE_RECLAIM
#include "ram.h"
static unsigned int fallback_ready;
unsigned int resident_fallback_base(void){return (unsigned int)internal_frames+64;}
unsigned int resident_fallback_valid(void){unsigned int i;
 unsigned int *p=(unsigned int*)internal_frames;
 if(!fallback_ready||!resident_queue_external_valid())return 0;
 for(i=0;i<16;i++)if(p[i]!=0x51a7cafeu||p[sizeof(internal_frames)/4-16+i]!=0xcafe51a7u)return 0;
 return 1;
}
unsigned int resident_fallback_prepare(void){unsigned int i;unsigned int*p=(unsigned int*)internal_frames;
 if(fallback_ready||!resident_queue_external_valid()||((unsigned int)p&15)||!ram_owned((unsigned int)p,sizeof(internal_frames)))return 1;
 for(i=0;i<16;i++){p[i]=0x51a7cafeu;p[sizeof(internal_frames)/4-16+i]=0xcafe51a7u;}
 fallback_ready=1;return !resident_fallback_valid();
}
#endif

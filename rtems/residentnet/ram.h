/* Allocation ownership is separate from engine completion. No host override. */
#ifndef RESIDENT_RAM_H
#define RESIDENT_RAM_H
static unsigned int ram_owned(unsigned int start,unsigned int size){
 const unsigned int lo=0xc0f4c010u,hi=0xc0f9bff0u;
 return size&&start>=lo&&start<hi&&size<=hi-start;
}
/* Until cache queue/drain + all bus masters + saved firmware ranges are proven,
 * no region outside the existing mutable upload allocation is admitted. */
static unsigned int ram_reclaim(unsigned int start,unsigned int size){return 0;}
#endif

/* Only before worker execution; initial IPv6 setup can have queued frames.
 * Existing storage remains reserved for the parked/cooperative context. */
unsigned int resident_queue_extend(unsigned int base){unsigned int i;
 if(base!=0xc0200040u||queue_slots!=68||head||queued>68)return 1;
 for(i=0;i<queued;i++)memcpy(QUEUE_ADDRESS(base+i*NETWORK_FRAME_BYTES),frames[i],lengths[i]);
 frames=QUEUE_ADDRESS(base);queue_slots=128;tail=queued;
 return 0;
}

unsigned int resident_queue_external_valid(void){
 return frames==QUEUE_ADDRESS(0xc0200040u)&&queue_slots==128&&head<128&&tail<128&&queued<=128;
}

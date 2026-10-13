/* Single CPU: arrival is published with interrupts masked. Do not cancel shared
 * references until BOTH workers have left their work loops. A peer can still be
 * between deciding to acquire a handle and actually acquiring it. */
static volatile unsigned int worker_stop_arrived[2];
static unsigned int worker_stop_complete(void){return worker_stop_arrived[0]&&worker_stop_arrived[1];}
static unsigned int worker_stop_arrive(unsigned int id){worker_stop_arrived[id]=1;return worker_stop_complete();}
static unsigned int worker_stop_expired(unsigned int start,unsigned int now,unsigned int polls){return now-start>=1000u||polls>=100000000u;}

/* Reads only firmware-evidenced addresses. Distinguish bus-data echo from a
 * register value; this is never an idle/completion or RAM-ownership predicate. */
static volatile unsigned int probe_seed __attribute__((aligned(16)));
static unsigned int cache_probe_read(unsigned int address,unsigned int seed,unsigned int half){
 unsigned int result,primed;probe_seed=seed;
 if(half)__asm__ volatile("ld (%2),%1;ldos (%3),%0":"=&r"(result),"=&r"(primed):"r"(&probe_seed),"r"(address):"memory");
 else __asm__ volatile("ld (%2),%1;ld (%3),%0":"=&r"(result),"=&r"(primed):"r"(&probe_seed),"r"(address):"memory");
 return result;
}
static void cache_probe(unsigned int*w){unsigned int i,cache_status,scratch;const unsigned int addresses[3]={0x40800000,0x40800008,0x4080000a};
 __asm__ volatile("dcctl 4,0,%0":"=r"(cache_status)::"memory");
 __asm__ volatile("dcctl 0,0,%0":"=r"(scratch)::"memory");
 w[0]=0x31484343;
 for(i=0;i<3;i++){w[1+i*2]=cache_probe_read(addresses[i],0xa5a5a5a5,i!=0);w[2+i*2]=cache_probe_read(addresses[i],0x5a5a5a5a,i!=0);}
 w[7]=*(volatile unsigned int*)0x1700; /* NMISR, read only */
 w[8]=*(volatile unsigned int*)0x1288; /* ATU direct-address decode control */
 w[9]=cache_status; /* observed before temporary D-cache disable */
 __asm__ volatile("dcctl 2,0,%0":"=r"(scratch)::"memory");
 if(cache_status&1)__asm__ volatile("dcctl 1,0,%0":"=r"(scratch)::"memory");
}

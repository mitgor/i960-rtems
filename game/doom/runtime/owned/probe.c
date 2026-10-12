#include "api.h"
#include <setjmp.h>
#ifdef OWNED_NATIVE_TEST
extern unsigned owned_test_mask(unsigned);
#endif
static volatile unsigned seed=0x49393630u;
static jmp_buf escape __attribute__((aligned(16)));
static const struct doom_runtime_owned *context;
static unsigned char *buffer;
/* Only these stable scalars are reported. Saved register/window pointers in the
 * jump buffer remain opaque; they are not an address admission mechanism. */
volatile unsigned owned_result[8];
static unsigned walk(unsigned depth){volatile unsigned local[8];unsigned i,h=seed^depth;
 for(i=0;i<8;i++)local[i]=seed^(depth*33+i);
 if(!context->owner())return 0;
 if(context->wait_ms(10)&&!context->stopping())return 0;
 if(depth)h^=walk(depth-1);
 for(i=0;i<8;i++)if(local[i]!=(seed^(depth*33+i)))return 0;
 return h;
}
static void owned_leave_stack(unsigned depth,int code){volatile unsigned canary=seed^depth;
 if(canary!=(seed^depth)||!context->owner()){owned_result[7]=1;longjmp(escape,99);}
 if(depth){context->wait_ms(10);owned_leave_stack(depth-1,code);}else longjmp(escape,code);
}
unsigned owned_entry(const struct doom_runtime_owned*a){unsigned i,start;int code;
 if(!a||a->magic!=DOOM_OWNED_MAGIC||a->version!=DOOM_OWNED_VERSION||a->bytes!=sizeof(*a)||a->features!=DOOM_OWNED_FEATURES||a->reserved||a->io.magic!=DOOM_API_MAGIC||a->io.bytes!=sizeof(a->io)||a->io.version!=DOOM_API_VERSION||a->io.pointer_bytes!=sizeof(void*)||a->io.little_endian!=1||a->io.features!=DOOM_API_FEATURES||a->io.reserved[0]||a->io.reserved[1]||!a->owner||!a->wait_ms||!a->stopping||!a->owner())return 1;
 context=a;for(i=0;i<8;i++)if(owned_result[i])return 2;
 buffer=a->io.allocate(512);if(!buffer&&!a->stopping())return 3;
 if(buffer)for(i=0;i<512;i++)buffer[i]=(unsigned char)(i^seed);
 owned_result[0]=walk(6);if(owned_result[0]!=(seed^7))goto bad;
 if(a->wait_ms(1001)!=-1)goto bad;owned_result[1]=1;
 {unsigned saved=0,bad;
#ifdef I960_TARGET
 unsigned level=31u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(level)::"g0","memory");saved=level;
#elif defined(OWNED_NATIVE_TEST)
 saved=owned_test_mask(31);
#endif
 bad=a->owner()||a->wait_ms(10)!=-1||a->io.allocate(1)!=0||!a->stopping();
#ifdef I960_TARGET
 __asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(saved)::"g0","memory");
#elif defined(OWNED_NATIVE_TEST)
 owned_test_mask(saved);
#endif
 if(bad||!a->owner())goto bad;owned_result[1]|=2;
 }
 code=setjmp(escape);
 if(!code)owned_leave_stack(4,7);
 if(code!=7)goto bad;owned_result[2]++;
 start=a->io.ticks_ms();
 while(a->io.ticks_ms()-start<10000&&!a->stopping()){
  if(a->wait_ms(10)&&!a->stopping())goto bad;owned_result[3]++;
 }
 owned_result[4]=a->io.ticks_ms()-start;owned_result[5]=a->stopping()?1:0;
 code=setjmp(escape);
 if(!code)owned_leave_stack(5,owned_result[5]?53:37);
 if(code!=(owned_result[5]?53:37)||!a->owner())goto bad;owned_result[2]++;owned_result[6]=code;
 if(buffer)for(i=0;i<512;i++)if(buffer[i]!=(unsigned char)(i^seed))goto bad;
 a->io.release(buffer);buffer=0;return DOOM_OWNED_MAGIC^seed^(unsigned)code;
 bad:a->io.release(buffer);buffer=0;return 4;
}

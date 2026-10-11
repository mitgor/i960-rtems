/* Native threaded model using the exact ioctl body and real pthread mutexes. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <errno.h>
#include <pthread.h>
#include <unistd.h>
#include <stdatomic.h>
typedef uint32_t u32;
#define __user
#define ODB 0x2c
#define mutex_lock pthread_mutex_lock
#define mutex_unlock pthread_mutex_unlock
#define record(...) ((void)0)
struct experiment {void*bar;pthread_mutex_t control_lock,session_lock;bool control_window,control_taken,control_done;int control_error;u32 control_epoch,control_sequence,stop_delay_ms;};
struct file {struct experiment*private_data;};
static u32 regs[64];static unsigned int writes;static int fail_copy;
static int copy_from_user(void*a,void*b,unsigned int n){memcpy(a,b,n);return 0;}
static int copy_to_user(void*a,void*b,unsigned int n){if(fail_copy)return 1;memcpy(a,b,n);return 0;}
static u32 readl(void*p){return *(u32*)p;}
static void writel(u32 v,void*p){assert(p==(char*)regs+0x14);writes++;*(u32*)p=v;if((v>>24)==0x72)regs[0x1c/4]=0x73001234;else assert(v==0x74001234);}
static void usleep_range(int a,int b){(void)b;usleep(a);}
static void msleep(unsigned int n){assert(n==120);usleep(10000);}
#include "concurrent_host.h"
static atomic_int published;
static void *writer(void*arg){struct experiment*d=arg;
 pthread_mutex_lock(&d->session_lock);pthread_mutex_lock(&d->control_lock);
 d->control_window=true;atomic_store(&published,1);pthread_mutex_unlock(&d->control_lock);
 for(;;){pthread_mutex_lock(&d->control_lock);if(d->control_done){d->control_window=false;pthread_mutex_unlock(&d->control_lock);break;}pthread_mutex_unlock(&d->control_lock);usleep(100);}
 pthread_mutex_unlock(&d->session_lock);return 0;
}
int main(void){struct experiment d={.bar=regs,.control_lock=PTHREAD_MUTEX_INITIALIZER,.session_lock=PTHREAD_MUTEX_INITIALIZER,.control_epoch=0x1234,.control_sequence=1,.stop_delay_ms=120};
 struct file f={&d};u32 w[8]={0,0x1234};pthread_t thread;
 regs[0x28/4]=0x1fb;regs[0x34/4]=0xff;regs[0x1c/4]=0x71001234;
 assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==-EAGAIN);
 pthread_create(&thread,0,writer,&d);while(!atomic_load(&published))usleep(100);
 assert(pthread_mutex_trylock(&d.session_lock)==EBUSY);
 w[1]=9;assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==-ESTALE&&writes==0);
 w[1]=0x1234;assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==0&&w[2]==1&&w[4]==0x71001234);
 memset(w,0,sizeof(w));w[0]=1;w[1]=0x1234;
 assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==0&&w[7]==1&&w[6]==0x73001234&&writes==2);
 pthread_join(thread,0);memset(w,0,sizeof(w));w[0]=1;w[1]=0x1234;
 assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==-EAGAIN&&writes==2);
 d.control_window=true;assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==-EALREADY&&writes==2);
 d.control_taken=d.control_done=false;regs[ODB/4]=1;
 assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==-EPROTO&&d.control_error==-EPROTO);
 d.control_taken=d.control_done=false;d.control_error=0;regs[ODB/4]=0;regs[0x1c/4]=0x71001234;
 fail_copy=1;assert(concurrent_ioctl(&f,0xc0204d03,(unsigned long)w)==-EFAULT&&d.control_done&&!d.control_error);
 puts("Concurrent ioctl: session lock held by writer, wrong epoch refused, STOP/RELEASE once, window joined, late/duplicate control refused");
}

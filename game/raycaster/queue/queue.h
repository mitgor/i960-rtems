#ifndef FRAME_QUEUE_H
#define FRAME_QUEUE_H
#define FQ_MAGIC 0x31514642u
#define FQ_OFFSET 0x60000u
#define FQ_SLOT_SIZE 5120u
#define FQ_SIZE (2u*FQ_SLOT_SIZE)
#define FQ_READY 0x59444152u
#define FQ_REPLY 64u
#define FQ_FRAME 4864u
#define FQ_BAD 1u
#define FQ_STALE 2u
#define FQ_BUSY 3u
#define FQ_CORRUPT 4u
struct fq_state {unsigned int epoch,last,mask,gen[2];};
static inline unsigned int fq_word(const unsigned char*p){return (unsigned int)p[0]|(unsigned int)p[1]<<8|(unsigned int)p[2]<<16|(unsigned int)p[3]<<24;}
static inline void fq_put(unsigned char*p,unsigned int n){p[0]=n;p[1]=n>>8;p[2]=n>>16;p[3]=n>>24;}
static inline unsigned int fq_hash(const unsigned char*p,unsigned int n){unsigned int h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;}
/* Shared pure validation, ordinary snapshots only, never live MMIO. */
static inline int fq_valid(const unsigned char*p,unsigned int epoch,unsigned int gen,unsigned int slot){
 unsigned int i;
 if(!epoch||!gen||slot>1||fq_word(p)!=FQ_MAGIC||fq_word(p+4)!=epoch||fq_word(p+8)!=gen||
    fq_word(p+12)!=FQ_FRAME||fq_word(p+16)!=FQ_READY||fq_word(p+24)!=~gen||fq_word(p+28)!=slot)return 0;
 for(i=32;i<64;i++)if(p[i]!=0xa5)return 0;
 for(i=64+FQ_FRAME;i<FQ_SLOT_SIZE;i++)if(p[i]!=0x5a)return 0;
 return fq_word(p+20)==fq_hash(p+64,FQ_FRAME);
}
unsigned int fq_request(struct fq_state*,void*,unsigned char*,const unsigned char*,unsigned int,unsigned char*,unsigned int,unsigned int);
#endif

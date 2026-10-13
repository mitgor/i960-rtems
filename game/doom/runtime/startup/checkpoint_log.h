#ifndef DOOM_CHECKPOINT_LOG_H
#define DOOM_CHECKPOINT_LOG_H
#include "checkpoint_api.h"
struct doom_checkpoint_log {unsigned count,overflow,origin;unsigned rows[DOOM_CHECKPOINT_CAPACITY][8];};
/* Caller serializes publication with the existing short runtime lock. No wait,
 * allocation, application pointer or overwrite is involved. */
static int doom_checkpoint_put(struct doom_checkpoint_log*l,unsigned generation,unsigned reads,unsigned stage,unsigned x,unsigned y,unsigned z){unsigned*w;
 if(!stage||stage>102||!generation)return 0;
 if(stage==1)l->origin=reads;
 if(reads-l->origin<4600&&stage>=100&&(stage==101||(x&63)))return 1;
 if(l->count==DOOM_CHECKPOINT_CAPACITY){l->overflow=1;return 0;}
 w=l->rows[l->count];w[0]=DOOM_CHECKPOINT_MAGIC;w[1]=l->count+1;w[2]=generation;w[3]=stage;w[4]=x;w[5]=y;w[6]=z;w[7]=reads-l->origin;l->count++;return 1;
}
static int doom_checkpoint_get(const struct doom_checkpoint_log*l,unsigned index,unsigned*out){unsigned i;
 if(!index||index>DOOM_CHECKPOINT_CAPACITY)return 0;
 if(index<=l->count){for(i=0;i<8;i++)out[i]=l->rows[index-1][i];}
 else {for(i=0;i<8;i++)out[i]=0;out[0]=DOOM_CHECKPOINT_MAGIC;out[2]=l->count;out[3]=l->overflow;}
 return 1;
}
#endif

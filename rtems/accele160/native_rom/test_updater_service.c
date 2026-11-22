#include "updater_service.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned char *flash, *target, *buffer;
static volatile unsigned int control[1024];
static volatile unsigned char data[4096];
static accele160_update_service service;

static void command(unsigned int seq,unsigned int cmd,unsigned int index,
                    unsigned int length,unsigned int digest,unsigned int expected)
{
    control[3]=cmd;control[4]=index;control[5]=length;control[6]=digest;
    control[1]=seq;
    accele160_update_service_poll(&service,control,data,buffer,flash,0,0);
    assert(control[2]==seq);
    if (control[7]!=expected)
        fprintf(stderr,"command %u seq %u returned %u expected %u state %u\n",
            cmd,seq,control[7],expected,control[8]);
    assert(control[7]==expected);
}

int main(void)
{
    unsigned char base[32],wanted[32];
    unsigned int i,seq=1;
    flash=malloc(0x100000u);target=malloc(0x100000u);buffer=malloc(0x100000u);
    assert(flash&&target&&buffer);
    for (i=0;i<0x100000u;++i) flash[i]=(unsigned char)(i*7u+i/127u);
    memcpy(target,flash,0x100000u);target[0x41000u]^=0x2au;
    accele160_sha256(flash,0x100000u,base);
    accele160_sha256(target,0x100000u,wanted);
    accele160_update_service_init(&service,control);
    assert(control[0]==ACCELE160_UPDATE_MAGIC&&control[10]==ACCELE160_UPDATE_VERSION);
    for (i=0;i<32u;++i) {
        ((volatile unsigned char *)control)[ACCELE160_UPDATE_BASE_SHA_OFFSET+i]=base[i];
        ((volatile unsigned char *)control)[ACCELE160_UPDATE_TARGET_SHA_OFFSET+i]=wanted[i];
    }
    command(seq++,ACCELE160_UPDATE_CMD_BEGIN,0,0,0,ACCELE160_UPDATE_OK);
    for (i=0;i<256u;++i) {
        unsigned int j;
        for (j=0;j<4096u;++j) data[j]=target[i*4096u+j];
        command(seq++,ACCELE160_UPDATE_CMD_CHUNK,i,4096u,
            accele160_fnv32(target+i*4096u,4096u),ACCELE160_UPDATE_OK);
    }
    command(seq++,ACCELE160_UPDATE_CMD_SEAL,0,0,0,ACCELE160_UPDATE_OK);
    assert(service.updater.state==2u);
    assert(memcmp(buffer,target,0x100000u)==0);
    assert(memcmp(flash,target,0x100000u)!=0);
    command(seq++,ACCELE160_UPDATE_CMD_ABORT,0,0,0,ACCELE160_UPDATE_OK);
    assert(service.updater.state==0u&&service.updater.next_chunk==0u);
    assert(control[8]==0u&&control[9]==0u);
    assert(control[10]==ACCELE160_UPDATE_VERSION);
    command(seq++,ACCELE160_UPDATE_CMD_BEGIN,0,0,0,ACCELE160_UPDATE_OK);
    assert(service.updater.state==1u&&service.updater.next_chunk==0u);
    free(flash);free(target);free(buffer);
    return 0;
}

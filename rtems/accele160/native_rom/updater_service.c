#include "updater_service.h"

void accele160_update_service_init(accele160_update_service *s,
                                   volatile unsigned int *control)
{
    unsigned int i;
    for (i=0;i<sizeof(*s);++i) ((unsigned char *)s)[i]=0u;
    for (i=0;i<24u;++i) control[i]=0u;
    control[0]=ACCELE160_UPDATE_MAGIC;
    control[10]=ACCELE160_UPDATE_VERSION;
}

void accele160_update_service_poll(accele160_update_service *s,
    volatile unsigned int *control, const volatile unsigned char *data,
    unsigned char *buffer, const volatile unsigned char *flash,
    accele160_update_write_block write_block, void *write_context)
{
    unsigned char base[32],target[32];
    unsigned int seq,cmd,index,length,digest,i,result;
    if (!s||!control||!data||!buffer||!flash) return;
    if (control[0]!=ACCELE160_UPDATE_MAGIC) return;
    seq=control[1];
    if (seq==s->acknowledged) return;
    if (seq!=s->acknowledged+1u||seq==0u) {
        control[7]=ACCELE160_UPDATE_SEQUENCE;
        return; /* wrong sequence cannot advance the protocol */
    }
    cmd=control[3];index=control[4];length=control[5];digest=control[6];
    if (cmd==ACCELE160_UPDATE_CMD_BEGIN) {
        for (i=0;i<32u;++i) {
            base[i]=((volatile unsigned char *)control)[ACCELE160_UPDATE_BASE_SHA_OFFSET+i];
            target[i]=((volatile unsigned char *)control)[ACCELE160_UPDATE_TARGET_SHA_OFFSET+i];
        }
        result=accele160_update_begin(&s->updater,buffer,flash,base,target);
    } else if (cmd==ACCELE160_UPDATE_CMD_CHUNK) {
        if (length!=ACCELE160_UPDATE_CHUNK_BYTES) result=ACCELE160_UPDATE_ARGUMENT;
        else {
            for (i=0;i<ACCELE160_UPDATE_CHUNK_BYTES;++i) s->chunk[i]=data[i];
            result=accele160_update_chunk(&s->updater,index,s->chunk,length,digest);
        }
    } else if (cmd==ACCELE160_UPDATE_CMD_SEAL) {
        result=accele160_update_seal(&s->updater);
    } else if (cmd==ACCELE160_UPDATE_CMD_ABORT) {
        result=accele160_update_abort(&s->updater);
    } else if (cmd==ACCELE160_UPDATE_CMD_APPLY) {
        result=accele160_update_apply(&s->updater,write_block,write_context);
    } else result=ACCELE160_UPDATE_ARGUMENT;
    control[7]=result;
    control[8]=s->updater.state;
    control[9]=s->updater.next_chunk;
    s->acknowledged=seq;
    control[2]=seq; /* response publication is last */
}

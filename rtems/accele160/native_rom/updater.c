#include "updater.h"

static unsigned int rotr(unsigned int x, unsigned int n)
{
    return (x >> n) | (x << (32u - n));
}

static const unsigned int k[64] = {
    0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
    0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
    0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
    0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
    0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
    0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
    0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
    0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
};

static void compress(unsigned int h[8], const unsigned char block[64])
{
    unsigned int w[64], a,b,c,d,e,f,g,hh,t1,t2,i;
    for (i=0;i<16u;++i) w[i]=((unsigned int)block[4u*i]<<24)|
        ((unsigned int)block[4u*i+1u]<<16)|((unsigned int)block[4u*i+2u]<<8)|block[4u*i+3u];
    for (i=16u;i<64u;++i) w[i]=w[i-16u]+(rotr(w[i-15u],7)^rotr(w[i-15u],18)^(w[i-15u]>>3))+
        w[i-7u]+(rotr(w[i-2u],17)^rotr(w[i-2u],19)^(w[i-2u]>>10));
    a=h[0];b=h[1];c=h[2];d=h[3];e=h[4];f=h[5];g=h[6];hh=h[7];
    for (i=0;i<64u;++i) {
        t1=hh+(rotr(e,6)^rotr(e,11)^rotr(e,25))+((e&f)^(~e&g))+k[i]+w[i];
        t2=(rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c));
        hh=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;
}

/* Bounded one-shot SHA-256. The 1 MiB image is streamed through one block. */
void accele160_sha256(const volatile unsigned char *data, unsigned int length,
                      unsigned char out[32])
{
    unsigned int h[8]={0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,
        0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u};
    unsigned char block[64];
    unsigned int i, full=length/64u, tail=length%64u;
    unsigned int bits_hi=length>>29, bits_lo=length<<3;
    for (i=0;i<full;++i) {
        unsigned int j;
        for (j=0;j<64u;++j) block[j]=data[i*64u+j];
        compress(h,block);
    }
    for (i=0;i<64u;++i) block[i]=0u;
    for (i=0;i<tail;++i) block[i]=data[full*64u+i];
    block[tail]=0x80u;
    if (tail>=56u) {
        compress(h,block);
        for (i=0;i<64u;++i) block[i]=0u;
    }
    for (i=0;i<4u;++i) {
        block[56u+i]=(unsigned char)(bits_hi>>(24u-8u*i));
        block[60u+i]=(unsigned char)(bits_lo>>(24u-8u*i));
    }
    compress(h,block);
    for (i=0;i<8u;++i) {
        out[4u*i]=(unsigned char)(h[i]>>24);
        out[4u*i+1u]=(unsigned char)(h[i]>>16);
        out[4u*i+2u]=(unsigned char)(h[i]>>8);
        out[4u*i+3u]=(unsigned char)h[i];
    }
}

unsigned int accele160_fnv32(const unsigned char *data, unsigned int length)
{
    unsigned int hash=2166136261u,i;
    for (i=0;i<length;++i) hash=(hash^data[i])*16777619u;
    return hash;
}

static int equal(const unsigned char *a,const unsigned char *b,unsigned int n)
{
    unsigned int i,diff=0u;
    for (i=0;i<n;++i) diff|=(unsigned int)(a[i]^b[i]);
    return diff==0u;
}

int accele160_update_begin(accele160_updater *u, unsigned char *buffer,
    const volatile unsigned char *flash, const unsigned char base_sha256[32],
    const unsigned char target_sha256[32])
{
    unsigned char digest[32];
    unsigned int i;
    if (!u||!buffer||!flash||!base_sha256||!target_sha256) return ACCELE160_UPDATE_ARGUMENT;
    if (u->state!=0u&&u->state!=3u) return ACCELE160_UPDATE_STATE;
    /* Flash is read-only here; copy it first to avoid hashing a volatile MMIO
     * pointer through ordinary C loads and to verify the exact base image. */
    for (i=0;i<ACCELE160_UPDATE_IMAGE_BYTES;++i) buffer[i]=flash[i];
    accele160_sha256(buffer,ACCELE160_UPDATE_IMAGE_BYTES,digest);
    if (!equal(digest,base_sha256,32u)) return ACCELE160_UPDATE_BASE_HASH;
    for (i=0;i<32u;++i) {
        u->base_sha256[i]=base_sha256[i];
        u->target_sha256[i]=target_sha256[i];
    }
    u->buffer=buffer;u->flash=flash;u->next_chunk=0u;u->state=1u;
    return ACCELE160_UPDATE_OK;
}

int accele160_update_chunk(accele160_updater *u, unsigned int index,
    const unsigned char *bytes, unsigned int length, unsigned int fnv32)
{
    unsigned int i,offset;
    if (!u||!bytes||length!=ACCELE160_UPDATE_CHUNK_BYTES) return ACCELE160_UPDATE_ARGUMENT;
    if (u->state!=1u) return ACCELE160_UPDATE_STATE;
    if (index!=u->next_chunk||index>=ACCELE160_UPDATE_CHUNKS) return ACCELE160_UPDATE_SEQUENCE;
    if (accele160_fnv32(bytes,length)!=fnv32) return ACCELE160_UPDATE_CHUNK_HASH;
    offset=index*ACCELE160_UPDATE_CHUNK_BYTES;
    if (offset<ACCELE160_UPDATE_MUTABLE_FIRST||offset>=ACCELE160_UPDATE_MUTABLE_END)
        for (i=0;i<length;++i)
            if (bytes[i]!=u->buffer[offset+i]) return ACCELE160_UPDATE_PROTECTED;
    for (i=0;i<length;++i) u->buffer[offset+i]=bytes[i];
    ++u->next_chunk;
    return ACCELE160_UPDATE_OK;
}

int accele160_update_seal(accele160_updater *u)
{
    unsigned char digest[32];
    unsigned int i;
    if (!u||u->state!=1u||u->next_chunk!=ACCELE160_UPDATE_CHUNKS)
        return ACCELE160_UPDATE_STATE;
    accele160_sha256(u->buffer,ACCELE160_UPDATE_IMAGE_BYTES,digest);
    if (!equal(digest,u->target_sha256,32u)) return ACCELE160_UPDATE_IMAGE_HASH;
    accele160_sha256(u->flash,ACCELE160_UPDATE_IMAGE_BYTES,digest);
    if (!equal(digest,u->base_sha256,32u)) return ACCELE160_UPDATE_BASE_HASH;
    for (i=0;i<ACCELE160_UPDATE_MUTABLE_FIRST;++i)
        if (u->buffer[i]!=u->flash[i]) return ACCELE160_UPDATE_PROTECTED;
    for (i=ACCELE160_UPDATE_MUTABLE_END;i<ACCELE160_UPDATE_IMAGE_BYTES;++i)
        if (u->buffer[i]!=u->flash[i]) return ACCELE160_UPDATE_PROTECTED;
    u->state=2u;
    return ACCELE160_UPDATE_OK;
}

int accele160_update_abort(accele160_updater *u)
{
    unsigned int i;
    if (!u) return ACCELE160_UPDATE_ARGUMENT;
    if (u->state==4u) return ACCELE160_UPDATE_STATE;
    u->buffer=0;u->flash=0;u->next_chunk=0u;u->state=0u;
    for (i=0;i<32u;++i) {
        u->base_sha256[i]=0u;
        u->target_sha256[i]=0u;
    }
    return ACCELE160_UPDATE_OK;
}

int accele160_update_apply(accele160_updater *u,
    accele160_update_write_block write_block,void *context)
{
    unsigned int offset,i,changed;
    unsigned char digest[32];
    if (!u||u->state!=2u) return ACCELE160_UPDATE_STATE;
    if (!write_block) return ACCELE160_UPDATE_NO_WRITER;
    /* The staging buffer may have been changed by host PCI writes after seal. */
    accele160_sha256(u->buffer,ACCELE160_UPDATE_IMAGE_BYTES,digest);
    if (!equal(digest,u->target_sha256,32u)) return ACCELE160_UPDATE_IMAGE_HASH;
    accele160_sha256(u->flash,ACCELE160_UPDATE_IMAGE_BYTES,digest);
    if (!equal(digest,u->base_sha256,32u)) return ACCELE160_UPDATE_BASE_HASH;
    for (i=0;i<ACCELE160_UPDATE_MUTABLE_FIRST;++i)
        if (u->buffer[i]!=u->flash[i]) return ACCELE160_UPDATE_PROTECTED;
    for (i=ACCELE160_UPDATE_MUTABLE_END;i<ACCELE160_UPDATE_IMAGE_BYTES;++i)
        if (u->buffer[i]!=u->flash[i]) return ACCELE160_UPDATE_PROTECTED;
    /* S3 has sixteen 64 KiB blocks. The stock boot and descriptor blocks are
     * excluded; only main firmware blocks may be sent to a qualified writer. */
    for (offset=ACCELE160_UPDATE_MUTABLE_FIRST;
         offset<ACCELE160_UPDATE_MUTABLE_END;offset+=0x10000u) {
        changed=0u;
        for (i=0;i<0x10000u;++i) changed|=u->flash[offset+i]^u->buffer[offset+i];
        if (changed) {
            if (write_block(offset,u->buffer+offset,0x10000u,context)) {
                u->state=4u; /* partial write: no in-session retry */
                return ACCELE160_UPDATE_WRITE_FAILED;
            }
            for (i=0;i<0x10000u;++i)
                if (u->flash[offset+i]!=u->buffer[offset+i]) {
                    u->state=4u;
                    return ACCELE160_UPDATE_VERIFY_FAILED;
                }
        }
    }
    /* A full-array digest also catches unintended changes outside the blocks
     * selected above (for example an address decode alias). */
    accele160_sha256(u->flash,ACCELE160_UPDATE_IMAGE_BYTES,digest);
    if (!equal(digest,u->target_sha256,32u)) {
        u->state=4u;
        return ACCELE160_UPDATE_VERIFY_FAILED;
    }
    u->state=3u;
    return ACCELE160_UPDATE_OK;
}

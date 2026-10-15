#ifndef I960_WAD_RING_WIRE_H
#define I960_WAD_RING_WIRE_H
/* Wire words are 32-bit little endian, never native pointers. Single producer
 * per record. Publish word 7 last; acquire before reading the other words. */
#define WR_SLOTS 2u
#define WR_BLOCK 32768u
#define WR_BATCH (WR_SLOTS*WR_BLOCK)
#define WR_BYTES 40960u
#define WR_REQUEST 4096u
#define WR_RESPONSE 4160u
#define WR_COMPLETE 4224u
#define WR_DATA 4288u
#define WR_REQ_MAGIC 0x31515257u
#define WR_RSP_MAGIC 0x31535257u
#define WR_END_MAGIC 0x31435257u
struct wr_record { unsigned w[16]; };
static void wr_record_make(struct wr_record*r,unsigned magic,unsigned gen,
                           unsigned offset,unsigned length,unsigned total){
 unsigned i;for(i=0;i<16;i++)r->w[i]=0;
 r->w[0]=magic;r->w[1]=gen;r->w[2]=(gen-1u)&1u;r->w[3]=offset;
 r->w[4]=length;r->w[5]=total;r->w[6]=~gen;r->w[7]=gen;
}
static unsigned wr_record_valid(const struct wr_record*r,unsigned magic,
                                unsigned gen,unsigned total){
 unsigned i;if(!gen||r->w[0]!=magic||r->w[1]!=gen||r->w[2]!=((gen-1u)&1u)||
 r->w[5]!=total||!total||total>268435456u||r->w[6]!=~gen||r->w[7]!=gen||
 r->w[3]>=total||(r->w[3]&(WR_BLOCK-1u))||!r->w[4]||r->w[4]>WR_BLOCK||
 r->w[4]!=((total-r->w[3]<WR_BLOCK)?total-r->w[3]:WR_BLOCK))return 0;
 for(i=8;i<16;i++)if(r->w[i])return 0;return 1;
}
static unsigned wr_record_matches(const struct wr_record*a,const struct wr_record*b){
 unsigned i;for(i=1;i<16;i++)if(a->w[i]!=b->w[i])return 0;return 1;
}
#endif

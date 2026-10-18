/* Single host producer / owning Init-task consumer. No ISR touches this ring.
 * Control-page offset e80..fff: 16 header words, 16 four-word entries,
 * 16 guard words. Frame timestamps end at e80; DMA log ends at e00.
 * Producer writes descriptor words and mirror first, publishes tail LAST.
 * Consumer copies/validates an entry before publishing its ACK LAST.
 */
#define KF_MAGIC 0x3146424bu
#define KF_EPOCH 0x161610e1u
#define KF_CAP 16u
#define KF_WORDS 96u
#ifndef KF_SYNC
#define KF_SYNC() do{}while(0)
#endif
typedef char kf_unsigned_is_32_bits[(sizeof(unsigned)==4)?1:-1];
struct key_fifo_state {
 unsigned cursor,discarded,run,mode,maximum,tick,frame,value,polls;
};
static unsigned kf_guard(unsigned i){return 0x4b475244u^(i*0x10204081u);}
static void kf_init(struct key_fifo_state*s,volatile unsigned*w,unsigned run){
 unsigned i;for(i=0;i<sizeof(*s)/sizeof(unsigned);i++)((unsigned*)s)[i]=0;
 for(i=0;i<KF_WORDS;i++)w[i]=0;
 s->run=run;w[0]=KF_MAGIC;w[1]=KF_EPOCH;w[2]=1;w[3]=KF_CAP;
 w[7]=run;w[15]=~KF_MAGIC;
 for(i=0;i<16;i++)w[80+i]=kf_guard(i);
 KF_SYNC();
}
static unsigned kf_check(struct key_fifo_state*s,volatile unsigned*w,volatile unsigned*live){
 unsigned i,tail=w[4],limit=s->mode?KF_CAP:1u;
 if(w[0]!=KF_MAGIC||w[1]!=KF_EPOCH||w[2]!=1||w[3]!=KF_CAP||w[15]!=~KF_MAGIC)return 1;
 for(i=0;i<16;i++)if(w[80+i]!=kf_guard(i))return 2;
 if(w[5]!=s->cursor||w[6]!=s->discarded||w[7]!=s->run||w[8]||w[14]!=s->mode)return 3;
 if(w[9]!=s->maximum||w[10]!=s->tick||w[11]!=s->frame||w[12]!=s->value||w[13]!=s->polls)return 4;
 if(tail<s->cursor||tail>=0xfffffffeu||tail-s->cursor>limit)return 5;
 /* The host may already be staging a newer producer mirror, but may never
  * publish the tail before the mirror or reuse an unacknowledged entry. */
 if(live[10]<tail||live[10]-tail>limit||live[12]!=s->cursor)return 6;
 return 0;
}
static unsigned kf_entry(struct key_fifo_state*s,volatile unsigned*w,unsigned seq,unsigned*value){
 unsigned base=16u+((seq-1u)&15u)*4u;
 if(w[base]!=seq||w[base+1]!=s->run||w[base+3]!=~seq)return 7;
 *value=w[base+2];if(*value&~0x1ffu)return 8;
 return 0;
}
static unsigned kf_begin(struct key_fifo_state*s,volatile unsigned*w,volatile unsigned*live,unsigned run){
 unsigned err,mode=w[14];struct key_fifo_state candidate=*s;
 if(mode>1)return 9;
 /* Mode may change only at the already-owned fresh-engine entry boundary. */
 candidate.mode=mode;err=kf_check(&candidate,w,live);
 if(err)return err;
 if(s->run!=run||w[4]!=s->cursor||live[10]!=s->cursor)return 10;
 s->mode=mode;return 0;
}
static unsigned kf_pop(struct key_fifo_state*s,volatile unsigned*w,volatile unsigned*live,
 unsigned tick,unsigned frame,unsigned*value,unsigned*available){
 unsigned err,tail,depth;
 *available=0;err=kf_check(s,w,live);if(err)return err;
 tail=w[4];depth=tail-s->cursor;
 if(tail<s->cursor||tail>=0xfffffffeu||depth>(s->mode?KF_CAP:1u)||live[10]<tail)return 5;
 if(!depth)return 0;
 if(s->mode){err=kf_entry(s,w,s->cursor+1u,value);if(err)return err;}
 else{*value=live[11];if(*value&~0x1ffu)return 8;}
 if(depth>s->maximum)s->maximum=depth;
 s->cursor++;s->tick=tick;s->frame=frame;s->value=*value;s->polls++;
 w[9]=s->maximum;w[10]=tick;w[11]=frame;w[12]=*value;w[13]=s->polls;
 live[12]=s->cursor;KF_SYNC();w[5]=s->cursor;*available=1;
 return 0;
}
static unsigned kf_pending(struct key_fifo_state*s,volatile unsigned*w,volatile unsigned*live){
 unsigned seq,value,err=kf_check(s,w,live);if(err)return err;
 if(live[10]!=w[4])return 11;
 if(!s->mode){if(live[11]&~0x1ffu)return 8;return 0;}
 for(seq=s->cursor+1u;seq<=w[4];seq++){
  err=kf_entry(s,w,seq,&value);if(err)return err;
 }
 return 0;
}
static void kf_rearm(struct key_fifo_state*s,volatile unsigned*w,volatile unsigned*live,unsigned next){
 /* Caller must first pass pending-entry and complete reusable ownership audits.
  * Classification is explicit: ACK cursor includes consumed + discarded;
  * discarded counts never mean that the engine consumed those old-game keys. */
 s->discarded+=w[4]-s->cursor;s->cursor=w[4];s->run=next;
 w[6]=s->discarded;w[7]=next;live[12]=s->cursor;KF_SYNC();w[5]=s->cursor;
}

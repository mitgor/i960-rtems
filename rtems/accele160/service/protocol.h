#ifndef ACCELE_SERVICE_PROTOCOL_H
#define ACCELE_SERVICE_PROTOCOL_H
/* One outstanding request. Host owns words 0..15, card owns 16..255.
 * Uncached, grant-owned odd page c0775000; no allocator or MMIO traversal.
 * Publish sequence/ACK last. Duplicate sequence preserves its exact reply. */
#define SVC_MAGIC 0x31435653u
#define SVC_BYTES 768u
#define SVC_VERSION 1u
struct svc_state { unsigned int epoch,seq,accepted,rejected; };
static void svc_text(volatile unsigned char *out,unsigned int *n,const char *s){
 while(*s && *n<SVC_BYTES)out[(*n)++]=(unsigned char)*s++;
}
static void svc_number(volatile unsigned char *out,unsigned int *n,unsigned int v){
 char b[10];unsigned int i=0;
 do{b[i++]=(char)('0'+v%10u);v/=10u;}while(v&&i<10u);
 while(i&&*n<SVC_BYTES)out[(*n)++]=(unsigned char)b[--i];
}
static void svc_field(volatile unsigned char *out,unsigned int *n,const char *s,unsigned int v){
 svc_text(out,n,s);svc_number(out,n,v);svc_text(out,n,"\n");
}
static void svc_poll(struct svc_state *s,volatile unsigned int *w,const unsigned int *v){
 unsigned int seq=w[0],op=w[3],n=0,status=0,i;
 volatile unsigned char *out=(volatile unsigned char *)(w+32);
 if(!seq||seq==s->seq)return;
 if(w[1]!=SVC_VERSION||w[2]!=s->epoch)status=1;
 else if(s->seq==0xffffffffu||seq!=s->seq+1u)status=2;
 else if(w[4]!=0u)status=3;
 else for(i=5;i<16u;i++)if(w[i])status=3;
 if(!status && (op<1u||op>7u))status=4;
 /* Invalid epoch/sequence cannot advance accepted sequence. Their ACK is
  * visible, but repeated polling must not inflate counters. Host restores
  * a valid next request or clears publication after reading the rejection. */
 if(w[16]==seq&&w[18]==w[2])return;
 if(!status){
  s->accepted++;
  if(op==1u)svc_text(out,&n,"help version uptime tasks mem apps stats\nRead-only RTEMS diagnostics; quit closes client.\n");
  if(op==2u)svc_text(out,&n,"RTEMS 4.6.6 / AcceleRAID160 / SVC1\n");
  if(op==3u){svc_field(out,&n,"ticks=",v[0]);svc_text(out,&n,"tick_ms=10\n");}
  if(op==4u){for(i=0;i<4u;i++){svc_field(out,&n,"owner=",v[4+i]);svc_field(out,&n,"irq_live=",v[8+i]);}svc_field(out,&n,"handoffs=",v[1]);svc_field(out,&n,"fault=",v[2]);}
  if(op==5u){svc_field(out,&n,"workspace_bytes=",v[12]);svc_field(out,&n,"arena_bytes=",v[13]);svc_field(out,&n,"fixed_allocations=",v[14]);svc_field(out,&n,"zone_loaned=",v[15]);svc_text(out,&n,"No dynamic heap walk; values are observational.\n");}
  if(op==6u){svc_field(out,&n,"run=",v[16]);svc_field(out,&n,"running=",v[17]);svc_field(out,&n,"idle=",v[18]);svc_field(out,&n,"frames=",v[19]);}
  if(op==7u){svc_field(out,&n,"accepted=",s->accepted);svc_field(out,&n,"rejected=",s->rejected);svc_field(out,&n,"wad_good=",v[20]);svc_field(out,&n,"wad_bad=",v[21]);svc_field(out,&n,"dma_completed=",v[22]);svc_field(out,&n,"worker_loops=",v[23]);}
 }else{s->rejected++;svc_field(out,&n,"error=",status);}
 if(w[1]==SVC_VERSION&&w[2]==s->epoch&&seq==s->seq+1u)s->seq=seq;
 w[17]=status;w[18]=w[2];w[19]=n;w[20]=v[0];w[21]=s->accepted;w[22]=s->rejected;
 w[23]=s->seq;w[24]=SVC_MAGIC;
 SVC_SYNC();w[16]=seq;
}
#endif
